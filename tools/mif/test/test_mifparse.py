"""Ayrıştırıcı testleri.  Koşum:  python3 -m unittest discover -s test -v

pytest gerekmez; kısıtlı bir kurum makinesinde de standart kütüphaneyle çalışır.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mifparse import mif                                    # noqa: E402
from mifparse.bicd import extract                           # noqa: E402
from mifparse.emit import build_sql, lit                    # noqa: E402
from mifparse.mapping import Mapping, normalize             # noqa: E402
from mifparse.tables import anchor_map, collect_tables      # noqa: E402

ORNEK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ornek_bicd.mif")


def _hucre(text):
    return "<Cell <CellContent <Para <ParaLine <String `%s'>>>>>" % text


def _kucuk_mif(pins):
    """Verilen (konnektör, pin, sinyal) satırlarından minik bir 6.2.1 tablosu."""
    head = "<Row " + "".join(_hucre(c) for c in
                             ("Connector Name", "Pin Index", "Name on Pin")) + ">"
    body = "".join("<Row " + "".join(_hucre(v) for v in row) + ">" for row in pins)
    src = ("<Tbls <Tbl <TblID 1> <TblNumColumns 3>"
           "<TblH " + head + "><TblBody " + body + ">>>"
           "<TextFlow <Para <PgfTag `H'> <ParaLine <String `6.2.1 External Connection List'>>>"
           "<Para <ParaLine <ATbl 1>>>>")
    root = mif.parse(src)
    return anchor_map(root, collect_tables(root)), Mapping.load()


def oku(path=ORNEK):
    text, enc = mif.read_mif(path)
    root = mif.parse(text)
    return enc, root, anchor_map(root, collect_tables(root))


class Sozdizimi(unittest.TestCase):
    def test_kacislar(self):
        r = mif.parse(r"<T <String `a\>b \qc\Q d\\e'>>")
        self.assertEqual(r.first("T").first("String").text(), "a>b 'c` d\\e")

    def test_hex_kacisi(self):
        # \xNN<boşluk> — sondaki boşluk kaçışın parçasıdır, metne girmez.
        r = mif.parse(r"<T <String `A\xd0 B'>>")
        s = r.first("T").first("String").text()
        self.assertEqual(len(s), 3)
        self.assertTrue(s.startswith("A") and s.endswith("B"))

    def test_yorum_atlanir(self):
        r = mif.parse("<A 1> # <B 2>\n<C 3>")
        self.assertEqual([c.name for c in r.children], ["A", "C"])

    def test_yorum_dizgi_icinde_yorum_degil(self):
        r = mif.parse("<T <String `a # b'>>")
        self.assertEqual(r.first("T").first("String").text(), "a # b")

    def test_char_deyimi(self):
        r = mif.parse("<Para <ParaLine <String `a '> <Char EmDash> <String ` b'>>>")
        self.assertEqual(mif.para_text(r.first("Para")), "a — b")

    def test_bilinmeyen_char_bos(self):
        r = mif.parse("<Para <ParaLine <String `a'> <Char Zurna> <String `b'>>>")
        self.assertEqual(mif.para_text(r.first("Para")), "ab")


class Tablolar(unittest.TestCase):
    def setUp(self):
        self.enc, self.root, self.tbls = oku()

    def test_kodlama(self):
        self.assertEqual(self.enc, "UTF-8")

    def test_tablo_sayisi_ve_capalar(self):
        self.assertEqual(len(self.tbls), 6)
        self.assertTrue(all(t.order is not None for t in self.tbls.values()))

    def test_baslik_baglami(self):
        self.assertEqual(self.tbls["1"].heading, "6.1.1 External Connectors")
        self.assertEqual(self.tbls["5"].heading, "8 Constraints")
        self.assertEqual(self.tbls["6"].heading, "7 Mechanical")

    def test_tablo_basligi(self):
        self.assertEqual(self.tbls["1"].title, "Table 3 — External Connectors")

    def test_cok_paragrafli_baslik_hucresi(self):
        # "Related Path" + "Functionality" iki paragraf; tek kolon adına iner.
        self.assertIn("Related Path", self.tbls["3"].columns[4])
        self.assertIn("Functionality", self.tbls["3"].columns[4])
        self.assertEqual(normalize(self.tbls["3"].columns[4]),
                         "related path functionality")

    def test_satir_sozlukleri(self):
        rows = self.tbls["1"].rows_as_dicts()
        self.assertEqual(rows[0]["Connector Name"], "J1")
        self.assertEqual(rows[1]["Contact Count"], "13 pos")


class Esleme(unittest.TestCase):
    def setUp(self):
        self.m = Mapping.load()

    def test_bolum_eslemesi(self):
        self.assertEqual(self.m.match_section("6.1.2 Internal Connectors")["scope"],
                         "internal")
        self.assertEqual(self.m.match_section("8 Constraints")["tip"], "mating")
        self.assertIsNone(self.m.match_section("7 Mechanical"))

    def test_kolon_eslemesi_ve_artiklar(self):
        mapped, warns = self.m.match_columns(
            ["Connector Name", "Part Number", "Notes"])
        self.assertEqual(mapped["Part Number"], "part_number")
        self.assertNotIn("Notes", mapped)          # eşleşmeyen kolon raw'da kalır
        self.assertEqual(warns, [])

    def test_cakisan_kolonlar_uyari_verir(self):
        mapped, warns = self.m.match_columns(["Part Number", "PN"])
        self.assertEqual(len(mapped), 1)
        self.assertEqual(len(warns), 1)


class Kayitlar(unittest.TestCase):
    def setUp(self):
        _, _, tbls = oku()
        self.ext = extract(tbls, Mapping.load())
        self.k = {c["connector_name"]: c for c in self.ext.connectors}

    def test_sayilar(self):
        self.assertEqual(len(self.ext.connectors), 4)
        self.assertEqual(len(self.ext.pins), 9)
        self.assertEqual(self.ext.errors, [])

    def test_61_ve_8_birlestirilir(self):
        j1 = self.k["J1"]
        self.assertEqual(j1["part_number"], "DAMA-9S-A197")       # §6.1
        self.assertEqual(j1["mating_part_number"], "DAMA-9P-A197")  # §8
        self.assertEqual(sorted(j1["source_sections"]), ["6.1", "8"])

    def test_kontak_sayisi_metinden_cikarilir(self):
        self.assertEqual(self.k["J2"]["contact_count"], 13)        # "13 pos"
        self.assertEqual(self.k["J2"]["raw"]["6.1"]["Contact Count"], "13 pos")

    def test_ham_veri_kayipsiz_ve_bolumlu(self):
        raw = self.k["J1"]["raw"]
        self.assertEqual(set(raw), {"6.1", "8"})
        self.assertEqual(raw["6.1"]["Notes"], "RS422 bakım hattı")
        self.assertEqual(raw["8"]["Remark"], "Kablo tarafı")

    def test_mating_eksigi_bosta_kalir(self):
        self.assertIsNone(self.k["J3"]["mating_part_number"])      # §8'de yok

    def test_yalniz_pinde_gecen_konnektor_taslak_acar(self):
        j4 = self.k["J4"]
        self.assertEqual(j4["source_sections"], ["6.2"])
        self.assertIsNone(j4["part_number"])
        self.assertTrue(any("J4" in w for w in self.ext.warnings))

    def test_alfanumerik_pin_index(self):
        idx = [p["pin_index"] for p in self.ext.pins if p["connector_name"] == "J2"]
        self.assertEqual(idx, ["A1", "A2"])

    def test_kapsam_pin_listesinden_gelir(self):
        j3 = [p for p in self.ext.pins if p["connector_name"] == "J3"]
        self.assertTrue(all(p["scope"] == "internal" for p in j3))

    def test_tekrar_eden_pin_hata_uretir(self):
        """Aynı (konnektör, pin index) ikilisi veritabanına gitmeden yakalanır."""
        ext = extract(*_kucuk_mif([
            ("J1", "1", "SIG_A"),
            ("J1", "1", "SIG_B"),     # tekrar
        ]))
        self.assertEqual(len(ext.errors), 1)
        self.assertIn("J1", ext.errors[0])
        self.assertIn("pin 1", ext.errors[0])

    def test_konnektor_adi_kolonu_yoksa_hata(self):
        """Eşleme tutmazsa sessizce boş kayıt üretmek yerine hata verilir."""
        src = ("<Tbls <Tbl <TblID 1> <TblNumColumns 2>"
               "<TblH <Row " + _hucre("Sinyal") + _hucre("Yon") + ">>"
               "<TblBody <Row " + _hucre("A") + _hucre("IN") + ">>>>"
               "<TextFlow <Para <PgfTag `H'> <ParaLine <String `6.2.1 Liste'>>>"
               "<Para <ParaLine <ATbl 1>>>>")
        root = mif.parse(src)
        ext = extract(anchor_map(root, collect_tables(root)), Mapping.load())
        self.assertEqual(len(ext.errors), 1)
        self.assertIn("konnektör adı kolonu bulunamadı", ext.errors[0])


class SqlUretimi(unittest.TestCase):
    def setUp(self):
        _, _, tbls = oku()
        self.ext = extract(tbls, Mapping.load())
        self.sql = build_sql(self.ext, {
            "project": "P", "board": "K", "doc_number": "D", "revision": "A",
            "imported_by": "u", "tool_version": "t", "mif_filename": "x.mif",
            "mif_sha256": "0" * 64, "export_date": "2026-03-14",
        })

    def test_tek_islem(self):
        self.assertEqual(self.sql.count("BEGIN;"), 1)
        self.assertEqual(self.sql.count("COMMIT;"), 1)

    def test_kontroller_kosuluyor(self):
        self.assertIn("PERFORM vdb.run_soft_checks(v_ver, v_run);", self.sql)

    def test_plpgsql_yer_tutucusu_tek_yuzde(self):
        self.assertIn("version_id=%)", self.sql)
        self.assertNotIn("version_id=%%)", self.sql)

    def test_tirnak_kacisi(self):
        self.assertEqual(lit("Kablo'nun"), "'Kablo''nun'")
        self.assertIn("I2C '' veri hattı", self.sql)   # \q -> ' -> '' 

    def test_dizi_ve_jsonb(self):
        self.assertIn("ARRAY['6.1', '8']::text[]", self.sql)
        self.assertIn("::jsonb", self.sql)

    def test_turkce_korunur(self):
        self.assertIn("Ön panel", self.sql)


if __name__ == "__main__":
    unittest.main(verbosity=2)
