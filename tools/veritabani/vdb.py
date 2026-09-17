#!/usr/bin/env python3
"""Doğrulama veritabanı yönetim aracı: kur · goc · durum · arsivle.

`psql`'i alt süreç olarak çağırır — Python paketi gerektirmez ve Windows'ta
da aynı şekilde çalışır. `psql`in PATH'te olması yeterli.

    python3 vdb.py durum   --dsn postgresql:///dogrulama
    python3 vdb.py kur     --dsn postgresql:///dogrulama
    python3 vdb.py goc     --dsn postgresql:///dogrulama [--kuru]
    python3 vdb.py arsivle --dsn postgresql:///dogrulama --surum 3

--dsn verilmezse PGHOST / PGDATABASE / PGUSER ortam değişkenleri kullanılır.
"""

import argparse
import datetime as dt
import getpass
import hashlib
import os
import re
import subprocess
import sys
import tempfile

BURASI = os.path.dirname(os.path.abspath(__file__))
GOCLER = os.path.join(BURASI, "gocler")
TEKRAR = os.path.join(BURASI, "tekrarlanabilir")

_SURUM_RE = re.compile(r"^(\d{4})_")


# ----------------------------------------------------------------------
# psql sarmalayıcı
# ----------------------------------------------------------------------

def psql(dsn, args, girdi=None):
    cmd = ["psql", "-X", "-v", "ON_ERROR_STOP=1"]
    if dsn:
        cmd.append(dsn)
    cmd += args
    try:
        p = subprocess.run(cmd, input=girdi, capture_output=True, text=True,
                           encoding="utf-8")
    except FileNotFoundError:
        sys.exit("psql bulunamadı. PostgreSQL istemcisini kurun ve PATH'e ekleyin.")
    return p


def sorgu(dsn, sql):
    """Tek değer döndüren sorgu; hata olursa programı durdurur."""
    p = psql(dsn, ["-At", "-c", sql])
    if p.returncode != 0:
        sys.exit("Veritabanına erişilemedi:\n" + (p.stderr or "").strip())
    return p.stdout.rstrip("\n")


def lit(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


# ----------------------------------------------------------------------
# Dosya kütüğü
# ----------------------------------------------------------------------

def _ozet(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def dosyalar():
    """[(surum, tur, yol, ozet)] — önce sürümlü göçler, sonra tekrarlanabilirler."""
    out = []
    for ad in sorted(os.listdir(GOCLER)) if os.path.isdir(GOCLER) else []:
        if not ad.endswith(".sql"):
            continue
        m = _SURUM_RE.match(ad)
        if not m:
            sys.exit("Göç dosyası adı 4 haneli numarayla başlamalı: %s" % ad)
        yol = os.path.join(GOCLER, ad)
        out.append((m.group(1), "goc", yol, _ozet(yol)))
    for ad in sorted(os.listdir(TEKRAR)) if os.path.isdir(TEKRAR) else []:
        if not ad.endswith(".sql") or not ad.startswith("R__"):
            continue
        yol = os.path.join(TEKRAR, ad)
        out.append((os.path.splitext(ad)[0], "tekrar", yol, _ozet(yol)))
    return out


def uygulanmis(dsn):
    """{surum: (tur, ozet)} — tablo henüz yoksa boş."""
    var = sorgu(dsn, "SELECT to_regclass('vdb.schema_version') IS NOT NULL")
    if var != "t":
        return {}
    p = psql(dsn, ["-At", "-F", "\t", "-c",
                   "SELECT surum, tur, sha256 FROM vdb.schema_version"])
    if p.returncode != 0:
        sys.exit((p.stderr or "").strip())
    out = {}
    for satir in p.stdout.splitlines():
        if satir.strip():
            surum, tur, ozet = satir.split("\t")
            out[surum] = (tur, ozet)
    return out


def bekleyenler(dsn):
    """(uygulanacaklar, uyusmazliklar) döndürür."""
    var = uygulanmis(dsn)
    yapilacak, uyusmaz = [], []
    for surum, tur, yol, ozet in dosyalar():
        kayit = var.get(surum)
        if kayit is None:
            yapilacak.append((surum, tur, yol, ozet, "yeni"))
        elif kayit[1] != ozet:
            if tur == "goc":
                uyusmaz.append((surum, yol))
            else:
                yapilacak.append((surum, tur, yol, ozet, "değişmiş"))
    return yapilacak, uyusmaz


# ----------------------------------------------------------------------
# Komutlar
# ----------------------------------------------------------------------

def cmd_durum(args):
    var = uygulanmis(args.dsn)
    yapilacak, uyusmaz = bekleyenler(args.dsn)

    print("Uygulanmış: %d kayıt" % len(var))
    for surum, tur, yol, ozet in dosyalar():
        k = var.get(surum)
        if k is None:
            durum = "BEKLİYOR"
        elif k[1] != ozet:
            durum = "UYUŞMAZLIK" if tur == "goc" else "değişmiş → yeniden uygulanacak"
        else:
            durum = "güncel"
        print("  %-18s %-7s %s" % (surum, tur, durum))

    if uyusmaz:
        print()
        print("HATA: uygulanmış göç dosyaları değiştirilmiş:")
        for surum, yol in uyusmaz:
            print("  %s  (%s)" % (surum, os.path.relpath(yol, BURASI)))
        print("Sürümlü göçler uygulandıktan sonra değiştirilmez. Dosyayı eski")
        print("hâline döndürün ve değişikliği yeni numaralı bir göç olarak açın.")
        return 1
    if not yapilacak:
        print("\nBekleyen yok.")
    return 0


def cmd_goc(args):
    yapilacak, uyusmaz = bekleyenler(args.dsn)
    if uyusmaz:
        print("HATA: uygulanmış göç dosyaları değiştirilmiş: %s"
              % ", ".join(s for s, _ in uyusmaz), file=sys.stderr)
        print("Dosyayı eski hâline döndürün; değişiklik yeni bir göç olmalı.",
              file=sys.stderr)
        return 1
    if not yapilacak:
        print("Bekleyen göç yok.")
        return 0

    for surum, tur, yol, ozet, neden in yapilacak:
        ad = os.path.relpath(yol, BURASI)
        if args.kuru:
            print("uygulanacak: %-18s %-7s %s (%s)" % (surum, tur, ad, neden))
            continue
        with open(yol, encoding="utf-8") as f:
            govde = f.read()
        kayit = (
            "INSERT INTO vdb.schema_version (surum, tur, dosya, sha256, uygulayan)\n"
            "  VALUES (%s, %s, %s, %s, %s)\n"
            "  ON CONFLICT (surum) DO UPDATE\n"
            "     SET sha256 = EXCLUDED.sha256, dosya = EXCLUDED.dosya,\n"
            "         uygulandi = now(), uygulayan = EXCLUDED.uygulayan;\n"
            % (lit(surum), lit(tur), lit(ad), lit(ozet), lit(args.kullanici)))
        sql = "BEGIN;\n" + govde + "\n" + kayit + "COMMIT;\n"
        p = psql(args.dsn, ["-q", "-f", "-"], girdi=sql)
        if p.returncode != 0:
            print("BAŞARISIZ: %s\n%s" % (ad, (p.stderr or "").strip()), file=sys.stderr)
            print("Hiçbir şey yazılmadı; göç kendi işleminde geri alındı.", file=sys.stderr)
            return 1
        print("uygulandı: %-18s %-7s %s (%s)" % (surum, tur, ad, neden))
    return 0


def cmd_kur(args):
    p = psql(args.dsn, ["-At", "-c", "SELECT 1"])
    if p.returncode != 0:
        hata = (p.stderr or "").strip()
        print(hata, file=sys.stderr)
        if "does not exist" in hata or "mevcut değil" in hata:
            print("\nVeritabanı yok. Önce oluşturun (kodlama UTF-8 olmalı):",
                  file=sys.stderr)
            print("  createdb -E UTF8 dogrulama", file=sys.stderr)
        return 1

    rc = cmd_goc(args)
    if rc:
        return rc

    print()
    print("Şema hazır. Roller NOLOGIN olarak kuruldu: vdb_loader, vdb_engineer,")
    print("vdb_reader, vdb_admin. Giriş yapacak kullanıcıları IT açar — şifreleri")
    print("bu araç üretmez:")
    print()
    print("  CREATE ROLE <kullanici> LOGIN PASSWORD '<sifre>';")
    print("  GRANT vdb_engineer TO <kullanici>;   -- ya da vdb_reader / vdb_loader")
    return 0


# ----------------------------------------------------------------------
# Arşiv
# ----------------------------------------------------------------------

# Dosya adları ASCII kalsın (iki işletim sisteminde de sorunsuz taşınır),
# ama Türkçe harfler atılmasın — okunmaz ada döner.
_CEVRI = str.maketrans({
    "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
    "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
})


def _temiz(s):
    s = (s or "").strip().translate(_CEVRI)
    return re.sub(r"[^A-Za-z0-9._-]+", "-", s).strip("-") or "x"


def cmd_arsivle(args):
    n = args.surum
    p = psql(args.dsn, ["-At", "-F", "\t", "-c",
                        "SELECT b.project, b.name, v.doc_number, v.revision, v.status "
                        "FROM vdb.bicd_version v JOIN vdb.board b USING (board_id) "
                        "WHERE v.version_id = %d" % n])
    if p.returncode != 0:
        sys.exit((p.stderr or "").strip())
    if not p.stdout.strip():
        sys.exit("Sürüm bulunamadı: %d" % n)
    proje, kart, dokno, rev, durum = p.stdout.strip().split("\t")
    if durum != "baselined":
        sys.exit("Sürüm %d baseline alınmamış (durum: %s). Arşiv dondurulmuş "
                 "sürümün kaydıdır; taslak arşivlenmez." % (n, durum))

    # 1) Şema: göç ve tekrarlanabilir dosyaların tamamı, uygulanma sırasıyla.
    parcalar = []
    for surum, tur, yol, _ in dosyalar():
        with open(yol, encoding="utf-8") as f:
            parcalar.append("-- ---- %s (%s) ----\n%s" % (surum, tur, f.read()))
    sema = "\n".join(parcalar)

    # 2) Veri
    p = psql(args.dsn, ["-At", "-c", "SELECT vdb.archive_data_sql(%d)" % n])
    if p.returncode != 0:
        sys.exit((p.stderr or "").strip())
    veri = p.stdout

    bugun = dt.date.today()
    ad = "%s_%s_%s_%s_%s.sql" % (_temiz(proje), _temiz(kart), _temiz(dokno),
                                 _temiz(rev), bugun.strftime("%Y%m%d"))
    hedef = os.path.join(args.dizin, ad)

    basli = (
        "-- =====================================================================\n"
        "-- ARŞİV — %s / %s · %s rev %s\n"
        "-- Baseline alınmış BICD sürümünün dondurulmuş kaydı.\n"
        "--\n"
        "-- Kendine yeter: şema ve veri birlikte. Boş bir veritabanına iner:\n"
        "--   createdb -E UTF8 <ad> && psql -d <ad> -v ON_ERROR_STOP=1 -f %s\n"
        "--\n"
        "-- Üretildi: %s · %s\n"
        "-- Bu dosyayı DEĞİŞTİRMEYİN: SHA-256 özeti CSAR'a işlenir.\n"
        "-- =====================================================================\n\n"
        "SET standard_conforming_strings = on;\n\n"
        % (proje, kart, dokno, rev, ad, bugun.isoformat(), args.kullanici))

    icerik = basli + sema + "\n\n" + veri
    with open(hedef, "w", encoding="utf-8") as f:
        f.write(icerik)

    ham = icerik.encode("utf-8")
    ozet = hashlib.sha256(ham).hexdigest()

    p = psql(args.dsn, ["-At", "-c",
                        "INSERT INTO vdb.archive_record (version_id, filename, sha256,"
                        " byte_size, created_by) VALUES (%d, %s, %s, %d, %s)"
                        " RETURNING archive_id"
                        % (n, lit(ad), lit(ozet), len(ham), lit(args.kullanici))])
    if p.returncode != 0:
        os.remove(hedef)
        sys.exit("Arşiv kaydı yazılamadı, dosya silindi:\n" + (p.stderr or "").strip())

    print("Arşiv: %s  (%.1f KB)" % (hedef, len(ham) / 1024.0))
    print("SHA-256: %s" % ozet)
    print()
    print("CSAR satırı:")
    print("  Category                  : Verification data — BICD konnektör/pin")
    print("  Configuration Identification: %s" % dokno)
    print("  Revision                  : %s" % rev)
    print("  File                      : %s" % ad)
    print("  SHA-256                   : %s" % ozet)
    print("  Date                      : %s" % bugun.isoformat())
    return 0


# ----------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(prog="vdb", description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="komut", required=True)

    def ortak(p):
        p.add_argument("--dsn", default=os.environ.get("VDB_DSN"),
                       help="ör. postgresql:///dogrulama (yoksa PG* ortam değişkenleri)")
        p.add_argument("--kullanici", default=getpass.getuser())

    p = sub.add_parser("durum", help="uygulanmış ve bekleyen göçler")
    ortak(p); p.set_defaults(func=cmd_durum)

    p = sub.add_parser("goc", help="bekleyen göçleri uygula")
    ortak(p)
    p.add_argument("--kuru", action="store_true", help="uygulama, ne yapacağını yaz")
    p.set_defaults(func=cmd_goc)

    p = sub.add_parser("kur", help="şemayı kur (göçlerin tamamı) ve rol notunu bas")
    ortak(p)
    p.add_argument("--kuru", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_kur)

    p = sub.add_parser("arsivle", help="baseline sürümü kendine yeten .sql'e dök")
    ortak(p)
    p.add_argument("--surum", type=int, required=True, help="bicd_version.version_id")
    p.add_argument("--dizin", default=".", help="çıktı dizini (varsayılan: .)")
    p.set_defaults(func=cmd_arsivle)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
