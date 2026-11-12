"""Örnek .mif dosyalarını but-json-uretici.html içine gömer.

Sayfa tek dosya ve internetsiz çalışsın diye "Örnek dosyalarla dene"
düğmesinin yüklediği dosyalar sayfanın içinde base64 olarak durur.
ornek/ altındaki bir dosya değişince bu betik yeniden koşulur:

    python3 ornek_gom.py
"""
import base64, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "but-json-uretici.html")
SAMPLES = {"BICD": "ornek/ornek_bicd.xlsx", "BRS": "ornek/ornek_brs.xlsx"}

data = {}
for role, rel in SAMPLES.items():
    with open(os.path.join(HERE, rel), "rb") as f:
        data[role] = {"name": os.path.basename(rel), "data": base64.b64encode(f.read()).decode("ascii")}

with open(PAGE, encoding="utf-8") as f:
    page = f.read()
new, n = re.subn(r"/\*__SAMPLES__\*/.*?;\n", lambda m: "/*__SAMPLES__*/" + json.dumps(data) + ";\n", page, count=1, flags=re.S)
if n != 1:
    raise SystemExit("Yer tutucu bulunamadı: /*__SAMPLES__*/")
with open(PAGE, "w", encoding="utf-8") as f:
    f.write(new)
print("Gömüldü:", ", ".join("%s (%d bayt)" % (k, len(base64.b64decode(v["data"]))) for k, v in data.items()))
