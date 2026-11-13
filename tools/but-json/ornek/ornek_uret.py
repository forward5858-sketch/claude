"""Sentetik DOORS Excel export örneklerini üretir (gerçek bir karta ait değildir).

Kolon düzeni bir VARSAYIMDIR: Object Identifier, Object Number, Object Heading,
Object Text ve attribute kolonları. Kullanıcının gerçek export'u gelince bu düzen
ona göre değişecek.

    python3 ornek/ornek_uret.py
"""
import os
from openpyxl import Workbook

HERE = os.path.dirname(os.path.abspath(__file__))

def save(name, header, rows):
    wb = Workbook(); ws = wb.active; ws.title = "Export"
    ws.append(header)
    for r in rows:
        ws.append([r.get(h, "") for h in header])
    wb.save(os.path.join(HERE, name))

H = lambda i, n, t: {"Object Identifier": i, "Object Number": n, "Object Heading": t}
T = lambda i, n, t, **kw: dict({"Object Identifier": i, "Object Number": n, "Object Text": t}, **kw)

# BICD: BRS ile aynı DOORS export düzeni varsayıldı (gerçek BICD export'u gelince güncellenecek).
# 2. kolon ana kolon (numaralı metin); §6.1 konnektörleri ve §8 mating DOORS TABLOSU olarak (her hücre
# Object Type = Table olan ayrı bir nesne; önce "Table N: …" başlığı, sonra hücreler satır satır);
# §6.2 pin listesi her pin ayrı nesne, pin bilgileri attribute kolonlarında.
BMAIN = "BICD-0001 - Örnek Kart Arayüz Dökümanı"
bicd_cols = ["ID", BMAIN, "Object Type", "Connector Name", "Pin Index", "Name on Pin", "Direction", "Related Path Functionality", "Created By"]
B = lambda i, txt, typ, **kw: dict({"ID": i, BMAIN: txt, "Object Type": typ, "Created By": "ornek"}, **kw)
def table(prefix, start, num, caption, header, rows):
    out = [B("%s-%d" % (prefix, start), "%s-%d Table %s" % (num, 1, caption), "Table")]
    k = start + 1
    for cell in header + [c for r in rows for c in r]:
        out.append(B("%s-%d" % (prefix, k), "%s-%d %s" % (num, k - start + 1, cell), "Table")); k += 1
    return out
PN = lambda i, n, c, p, nm, d, f: B(i, "%s %s" % (n, nm), "Description", **{"Connector Name": c, "Pin Index": p, "Name on Pin": nm,
                                                                             "Direction": d, "Related Path Functionality": f})
save("ornek_bicd.xlsx", bicd_cols, [
    B("BICD-1", "1 Introduction", "Heading"),
    B("BICD-2", "1.0-1 Bu doküman kartın arayüzlerini tanımlar (sentetik örnek).", "Description"),
    B("BICD-3", "6 Connection", "Heading"),
    B("BICD-4", "6.1 Connectors", "Heading"),
    B("BICD-5", "6.1.1 External Connectors", "Heading"),
    B("BICD-6", "6.1.1.0-1 Ekipmanın dışına çıkan konnektörler aşağıdaki tablodadır.", "Description"),
    *table("BICD", 100, "6.1.1.0", "1: External connectors", ["Connector Name", "Part Number", "Contact Count"],
           [["J1", "DAMA-9S-A197", "9"], ["J2", "D38999/24FB35SN", "13 pos"]]),
    B("BICD-7", "6.1.2 Internal Connectors", "Heading"),
    *table("BICD", 120, "6.1.2.0", "2: Internal connectors", ["Connector Name", "Part Number", "Contact Count"],
           [["J3", "PH-10S-VS", "10"]]),
    B("BICD-8", "6.2 Connection List", "Heading"),
    B("BICD-9", "6.2.1 External Connection List", "Heading"),
    PN("BICD-13", "6.2.1.0-1", "J1", "1", "MAINT_TX_P", "OUT", "RS422 bakım hattı — verici"),
    PN("BICD-14", "6.2.1.0-2", "J1", "2", "MAINT_TX_N", "OUT", "RS422 bakım hattı — verici"),
    PN("BICD-15", "6.2.1.0-3", "J1", "3", "MAINT_RX_P", "IN", "RS422 bakım hattı — alıcı"),
    PN("BICD-16", "6.2.1.0-4", "J2", "A1", "VIN_28V", "POWER", "Ana besleme"),
    PN("BICD-17", "6.2.1.0-5", "J2", "A2", "PGND", "GROUND", "Güç şasesi"),
    B("BICD-18", "6.2.2 Internal Connection List", "Heading"),
    PN("BICD-19", "6.2.2.0-1", "J3", "1", "I2C_SDA", "BIDIR", "I2C veri hattı"),
    PN("BICD-20", "6.2.2.0-2", "J3", "2", "I2C_SCL", "OUT", "I2C saat hattı"),
    PN("BICD-21", "6.2.2.0-3", "J4", "1", "SPARE", "NC", "Yedek"),
    B("BICD-22", "7 Mechanical", "Heading"),
    B("BICD-23", "7.0-1 Board top view", "Figure"),
    B("BICD-24", "8 Constraints", "Heading"),
    *table("BICD", 140, "8.0", "3: Mating connectors", ["Connector Name", "Mating Part Number"],
           [["J1", "DAMA-9P-A197"], ["J2", "D38999/26FB35PN"]]),
])

# BRS: kullanıcının verdiği DOORS düzeni. 2. kolon DOORS ana kolonudur: adı modül adıdır ("BRS.No - {Description}"),
# metinler hiyerarşik numarayla başlar ("3.1 Power Interface", "3.1.0-1 The board shall …"). Diğer kolonlar adıyla
# bulunur; ilgisiz kolonlar da var ve sıra karışık.
MAIN = "BRS-0001 - Örnek Kart Gereksinimleri"
brs_cols = ["ID", MAIN, "Object Type", "Created By", "Source of Verification", "Verification Method"]
O = lambda i, txt, typ, vm="", sov="": {"ID": i, MAIN: txt, "Object Type": typ, "Verification Method": vm,
                                       "Source of Verification": sov, "Created By": "ornek"}
save("ornek_brs.xlsx", brs_cols, [
    O("BRS-1", "1 Purpose", "Heading"),
    O("BRS-2", "1.0-1 The purpose of this document is to define the board requirements (sentetik örnek).", "Remark"),
    O("BRS-3", "2 Scope", "Heading"),
    O("BRS-4", "2.0-1 This document applies to the sample board.", "Remark"),
    O("BRS-5", "3 Requirements", "Heading"),
    O("BRS-6", "3.1 Power Interface", "Heading"),
    O("BRS-101", "3.1.0-1 The board shall accept 28 VDC ± 4 VDC input power on connector J2.", "Allocated",
      "MoC4: Laboratory Test", "MoC4 -> BVP(BVP-0001)"),
    O("BRS-102", "3.1.0-2 The board power consumption shall be less than 12 W.", "Derived",
      "MoC1: Design Review\nMoC4: Laboratory Test", "MoC1 -> BDDD(BDDD-0042)\nMoC4 -> BVP(BVP-0001)"),
    O("BRS-103", "3.1.0-3 The input power path shall have reverse polarity protection.", "Allocated", "MoC1: Design Review", ""),
    O("BRS-7", "3.1.0-4 Power input block diagram", "Figure"),
    O("BRS-8", "3.2 RS422 Maintenance Interface", "Heading"),
    O("BRS-201", "3.2.0-1 The board shall provide one RS422 maintenance interface on connector J1.", "Allocated",
      "MoC4: Laboratory Test", "MoC4 -> BVP(BVP-0001)"),
    O("BRS-202", "3.2.0-2 The RS422 interface shall support 115200 baud.", "Allocated"),
    O("BRS-9", "3.2.1 Electrical", "Heading"),
    O("BRS-203", "3.2.1.0-1 RS422 receive lines shall be terminated with 120 ohm.", "Allocated",
      "MoC1: Design Review", "MoC1 -> Schematics(SCH-0007)"),
    O("BRS-204", "3.2.1.0-2 RS422 lines should use twisted pair routing.", "Design Goal", "MoC1: Design Review"),
    O("BRS-10", "3.2.1.0-3 Table 1: RS422 pin assignment", "Table"),
    O("BRS-11", "3.2.1.0-4 Pin", "Table"), O("BRS-12", "3.2.1.0-5 Signal", "Table"),
    O("BRS-13", "3.2.1.0-6 J1-1", "Table"), O("BRS-14", "3.2.1.0-7 MAINT_TX_P", "Table"),
    O("BRS-15", "3.2.1.0-8 J1-3", "Table"), O("BRS-16", "3.2.1.0-9 MAINT_RX_P", "Table"),
])
print("ok")
