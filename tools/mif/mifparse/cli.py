"""BICD .mif aracı: keşfet · çıkar · yükle."""

import argparse
import getpass
import hashlib
import json
import os
import re
import sys

from . import mif
from .bicd import extract
from .emit import build_sql
from .mapping import Mapping
from .tables import collect_tables, anchor_map, tables_in_order

TOOL_VERSION = "mif-import 0.1.0"

# "AGK-1200_BICD_C.mif" -> kart AGK-1200, revizyon C
_NAME_RE = re.compile(r"^(?P<kart>.+?)[_-]BICD[_-](?P<rev>[^_.]+)", re.IGNORECASE)


def _read(path, esleme):
    text, enc = mif.read_mif(path)
    root = mif.parse(text)
    tbls = anchor_map(root, collect_tables(root))
    return text, enc, tbls, Mapping.load(esleme)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _meta(args, path):
    base = os.path.basename(path)
    m = _NAME_RE.match(os.path.splitext(base)[0])
    kart = args.kart or (m.group("kart") if m else None)
    rev = args.revizyon or (m.group("rev") if m else None)
    if not kart:
        sys.exit("Kart adı çıkarılamadı; --kart verin.")
    if not rev:
        sys.exit("Revizyon çıkarılamadı; --revizyon verin.")
    return {
        "project": args.proje, "board": kart,
        "doc_number": args.dokuman_no or ("BICD-" + kart),
        "revision": rev,
        "doors_baseline": args.baseline, "export_date": args.export_tarihi,
        "view_name": args.view, "mif_filename": base, "mif_sha256": _sha256(path),
        "imported_by": args.kullanici, "note": args.not_,
        "tool_version": TOOL_VERSION, "fresh": args.taze,
    }


# ----------------------------------------------------------------------
# kesfet — gerçek dosya geldiğinde İLK koşulacak komut
# ----------------------------------------------------------------------

def cmd_kesfet(args):
    text, enc, tbls, mp = _read(args.dosya, args.esleme)
    ext = extract(tbls, mp)
    size = os.path.getsize(args.dosya)

    if args.json:
        out = {"dosya": args.dosya, "kodlama": enc, "bayt": size, "tablolar": []}
        for tbl, rule, colmap in ext.tables:
            out["tablolar"].append({
                "id": tbl.id, "tag": tbl.tag, "baslik_bagmi": tbl.heading,
                "tablo_basligi": tbl.title, "kolonlar": tbl.columns,
                "eslesen_bolum": rule["ad"] if rule else None,
                "kolon_eslemesi": colmap,
                "satir": len(tbl.body_rows),
                "ilk_satirlar": tbl.body_rows[:3],
            })
        out["uyarilar"] = ext.warnings
        out["hatalar"] = ext.errors
        json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return 0

    print("Dosya    : %s" % args.dosya)
    print("Kodlama  : %s   Boyut: %.1f KB" % (enc, size / 1024.0))
    print("Tablo    : %d (akışta çapalanan %d)"
          % (len(tbls), sum(1 for t in tbls.values() if t.order is not None)))
    print()

    for tbl, rule, colmap in ext.tables:
        mark = "✓ %s" % rule["ad"] if rule else "— eşleşmedi"
        print("Tablo %s  [%s]" % (tbl.id, mark))
        print("  Başlık bağlamı : %s%s" % (tbl.heading or "(yok)",
              ("   (PgfTag=%s)" % tbl.heading_tag) if tbl.heading_tag else ""))
        if tbl.title:
            print("  Tablo başlığı  : %s" % tbl.title)
        print("  Satır          : %d" % len(tbl.body_rows))
        print("  Kolonlar:")
        for col in tbl.columns:
            field = colmap.get(col)
            print("    %-34s -> %s" % (col.replace("\n", " ")[:34],
                                       field or "(raw'da kalır)"))
        for row in tbl.body_rows[:3]:
            print("    | " + " | ".join((c or "").replace("\n", " ")[:22] for c in row))
        print()

    unmatched = [t.heading for t, r, _ in ext.tables if r is None]
    if unmatched:
        print("Eşleşmeyen tablo başlıkları: %s" % ", ".join(
            repr(h or "(yok)") for h in unmatched))
    print("Sonuç: %d konnektör, %d pin, %d uyarı, %d hata."
          % (len(ext.connectors), len(ext.pins), len(ext.warnings), len(ext.errors)))
    for w in ext.warnings:
        print("  uyarı: %s" % w)
    for e in ext.errors:
        print("  HATA : %s" % e)
    if not ext.connectors and not ext.pins:
        print()
        print("Hiç kayıt çıkmadı. Yukarıdaki başlık ve kolon adlarına bakıp")
        print("%s dosyasını ayarlayın; kodun değişmesi gerekmez." % (args.esleme or Mapping.load().path))
    return 0


def _extract_or_die(args):
    _, _, tbls, mp = _read(args.dosya, args.esleme)
    ext = extract(tbls, mp)
    for w in ext.warnings:
        print("uyarı: %s" % w, file=sys.stderr)
    if ext.errors:
        for e in ext.errors:
            print("HATA: %s" % e, file=sys.stderr)
        sys.exit("Hatalar giderilmeden yükleme yapılmaz.")
    if not ext.connectors:
        sys.exit("Hiç konnektör çıkmadı. Önce 'kesfet' ile eşlemeyi kontrol edin.")
    return ext


def cmd_cikar(args):
    ext = _extract_or_die(args)
    sql = build_sql(ext, _meta(args, args.dosya))
    if args.cikti:
        with open(args.cikti, "w", encoding="utf-8") as f:
            f.write(sql)
        print("Yazıldı: %s  (%d konnektör, %d pin)"
              % (args.cikti, len(ext.connectors), len(ext.pins)), file=sys.stderr)
    else:
        sys.stdout.write(sql)
    return 0


def cmd_yukle(args):
    from .load import load
    ext = _extract_or_die(args)
    try:
        version_id, counts, checks = load(ext, _meta(args, args.dosya), args.dsn)
    except RuntimeError as exc:
        sys.exit(str(exc))
    print("Yüklendi: version_id=%d  konnektör=%d  pin=%d"
          % (version_id, counts["connector"], counts["pin"]))
    fails = [c for c in checks if c[1] == "fail"]
    print("Kalite kontrolleri: %d koştu, %d bulgu." % (len(checks), len(fails)))
    for code, _, detail in fails:
        print("  %s  %s" % (code, detail))
    if fails:
        print("Bulgular giderilmeden bu sürüm baseline'a çıkamaz.")
    return 0


# ----------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="mifparse", description="BICD .mif export'unu okur ve doğrulama "
                                     "veritabanına hazırlar.")
    sub = ap.add_subparsers(dest="komut", required=True)

    def common(p, meta=False):
        p.add_argument("dosya")
        p.add_argument("--esleme", help="eşleme yapılandırması (JSON)")
        if meta:
            p.add_argument("--proje", required=True)
            p.add_argument("--kart", help="varsayılan: dosya adından")
            p.add_argument("--dokuman-no", dest="dokuman_no")
            p.add_argument("--revizyon", help="varsayılan: dosya adından")
            p.add_argument("--baseline", help="DOORS baseline adı")
            p.add_argument("--export-tarihi", dest="export_tarihi", help="YYYY-AA-GG")
            p.add_argument("--view", help="export anındaki DOORS view adı")
            p.add_argument("--kullanici", default=getpass.getuser())
            p.add_argument("--not", dest="not_")
            p.add_argument("--taze", action="store_true",
                           help="aynı sürüm yüklüyse silip yeniden yükle "
                                "(baseline alınmışsa reddedilir)")

    p = sub.add_parser("kesfet", help="tabloları ve eşleme durumunu raporla")
    common(p)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_kesfet)

    p = sub.add_parser("cikar", help="yüklenecek SQL dosyasını üret")
    common(p, meta=True)
    p.add_argument("--cikti", help="hedef .sql dosyası (yoksa stdout)")
    p.set_defaults(func=cmd_cikar)

    p = sub.add_parser("yukle", help="psycopg ile doğrudan yükle")
    common(p, meta=True)
    p.add_argument("--dsn", required=True, help="ör. postgresql:///dogrulama")
    p.set_defaults(func=cmd_yukle)

    args = ap.parse_args(argv)
    return args.func(args)
