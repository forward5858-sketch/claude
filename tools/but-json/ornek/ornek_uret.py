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

bicd_cols = ["Object Identifier", "Object Number", "Object Heading", "Object Text", "Connector Name", "Part Number",
             "Mating Part Number", "Contact Count", "Pin Index", "Name on Pin", "Direction", "Related Path Functionality"]
P = lambda i, n, c, p, nm, d, f: T(i, n, "", **{"Connector Name": c, "Pin Index": p, "Name on Pin": nm, "Direction": d, "Related Path Functionality": f})
save("ornek_bicd.xlsx", bicd_cols, [
    H("BICD-1", "1", "Introduction"),
    T("BICD-2", "1-1", "Bu doküman kartın arayüzlerini tanımlar (sentetik örnek)."),
    H("BICD-3", "6", "Connection"),
    H("BICD-4", "6.1", "Connectors"),
    H("BICD-5", "6.1.1", "External Connectors"),
    T("BICD-6", "6.1.1-1", "Ekipmanın dışına çıkan konnektörler aşağıdadır."),
    T("BICD-7", "6.1.1-2", "", **{"Connector Name": "J1", "Part Number": "DAMA-9S-A197", "Contact Count": "9"}),
    T("BICD-8", "6.1.1-3", "", **{"Connector Name": "J2", "Part Number": "D38999/24FB35SN", "Contact Count": "13 pos"}),
    H("BICD-9", "6.1.2", "Internal Connectors"),
    T("BICD-10", "6.1.2-1", "", **{"Connector Name": "J3", "Part Number": "PH-10S-VS", "Contact Count": "10"}),
    H("BICD-11", "6.2", "Connection List"),
    H("BICD-12", "6.2.1", "External Connection List"),
    P("BICD-13", "6.2.1-1", "J1", "1", "MAINT_TX_P", "OUT", "RS422 bakım hattı — verici"),
    P("BICD-14", "6.2.1-2", "J1", "2", "MAINT_TX_N", "OUT", "RS422 bakım hattı — verici"),
    P("BICD-15", "6.2.1-3", "J1", "3", "MAINT_RX_P", "IN", "RS422 bakım hattı — alıcı"),
    P("BICD-16", "6.2.1-4", "J2", "A1", "VIN_28V", "POWER", "Ana besleme"),
    P("BICD-17", "6.2.1-5", "J2", "A2", "PGND", "GROUND", "Güç şasesi"),
    H("BICD-18", "6.2.2", "Internal Connection List"),
    P("BICD-19", "6.2.2-1", "J3", "1", "I2C_SDA", "BIDIR", "I2C veri hattı"),
    P("BICD-20", "6.2.2-2", "J3", "2", "I2C_SCL", "OUT", "I2C saat hattı"),
    P("BICD-21", "6.2.2-3", "J4", "1", "SPARE", "NC", "Yedek"),
    H("BICD-22", "7", "Mechanical"),
    T("BICD-23", "7-1", "Kartın üst ve alt görünümleri (görseller export'a girmez)."),
    H("BICD-24", "8", "Constraints"),
    T("BICD-25", "8-1", "", **{"Connector Name": "J1", "Mating Part Number": "DAMA-9P-A197"}),
    T("BICD-26", "8-2", "", **{"Connector Name": "J2", "Mating Part Number": "D38999/26FB35PN"}),
])

# BRS: kullanıcının verdiği DOORS düzeni — ID, Object Text, Object Type, Verification Method,
# Source of Verification; ilgisiz kolonlar da var ve sıra karışık (araç kolonları adından bulur).
brs_cols = ["Created By", "Object Type", "ID", "Object Text", "Last Modified On", "Source of Verification", "Verification Method"]
O = lambda i, typ, t, vm="", sov="": {"ID": i, "Object Type": typ, "Object Text": t, "Verification Method": vm,
                                     "Source of Verification": sov, "Created By": "ornek", "Last Modified On": "2026-11-13"}
save("ornek_brs.xlsx", brs_cols, [
    O("BRS-1", "Heading", "Introduction"),
    O("BRS-2", "Remark", "Sentetik BRS: BUT.json üreticisini sınamak için."),
    O("BRS-3", "Heading", "Requirements"),
    O("BRS-4", "Heading", "Power Interface"),
    O("BRS-101", "Allocated", "The board shall accept 28 VDC ± 4 VDC input power on connector J2.",
      "MoC4: Laboratory Test", "MoC4 -> BVP(BVP-0001)"),
    O("BRS-102", "Derived", "The board power consumption shall be less than 12 W.",
      "MoC1: Design Review\nMoC4: Laboratory Test", "MoC1 -> BDDD(BDDD-0042)\nMoC4 -> BVP(BVP-0001)"),
    O("BRS-103", "Allocated", "The input power path shall have reverse polarity protection.", "MoC1: Design Review", ""),
    O("BRS-5", "Figure", "Power input block diagram"),
    O("BRS-6", "Heading", "RS422 Maintenance Interface"),
    O("BRS-201", "Allocated", "The board shall provide one RS422 maintenance interface on connector J1.",
      "MoC4: Laboratory Test", "MoC4 -> BVP(BVP-0001)"),
    O("BRS-202", "Allocated", "The RS422 interface shall support 115200 baud.", "", ""),
    O("BRS-203", "Design Goal", "RS422 receive lines should be terminated with 120 ohm.",
      "MoC1: Design Review", "MoC1 -> Schematics(SCH-0007)"),
    O("BRS-7", "Table", "RS422 pin assignment"),
])
print("ok")
