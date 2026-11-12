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

brs_cols = ["Object Identifier", "Object Number", "Object Heading", "Object Text", "Object Type", "MoC", "Source of Verification"]
R = lambda i, n, t, moc, sov: T(i, n, t, **{"Object Type": "Requirement", "MoC": moc, "Source of Verification": sov})
save("ornek_brs.xlsx", brs_cols, [
    H("BRS-1", "1", "Introduction"),
    T("BRS-2", "1-1", "Sentetik BRS: BUT.json üreticisini sınamak için.", **{"Object Type": "Information"}),
    H("BRS-3", "3", "Requirements"),
    H("BRS-4", "3.1", "Power Interface"),
    R("BRS-101", "3.1-1", "The board shall accept 28 VDC ± 4 VDC input power on connector J2.", "MoC4", "BVP"),
    R("BRS-102", "3.1-2", "The board power consumption shall be less than 12 W.", "MoC4", "BVP"),
    R("BRS-103", "3.1-3", "The input power path shall have reverse polarity protection.", "MoC1", "Schematics"),
    T("BRS-5", "3.1-4", "Not: güç girişi MIL-STD-704F ile uyumludur.", **{"Object Type": "Information"}),
    H("BRS-6", "3.2", "RS422 Maintenance Interface"),
    R("BRS-201", "3.2-1", "The board shall provide one RS422 maintenance interface on connector J1.", "MoC4", "BVP"),
    R("BRS-202", "3.2-2", "The RS422 interface shall support 115200 baud.", "", ""),
    R("BRS-203", "3.2-3", "RS422 receive lines shall be terminated with 120 ohm.", "MoC1", "Schematics"),
])
print("ok")
