# BUT.json Üretici

Kartın girdi dökümanlarını (BICD, BRS, BCDD, BDDD, şematik) okuyup analiz eder ve
`BUT.json` dosyasını üretir. Süreçteki yeri: **Aşama 2 — BUT.json üretimi** (panodaki
"BUT.json üretimi" işlem kutusu).

## Kullanım

1. `but-json-uretici.html` dosyasını tarayıcıda açın (çift tıklamak yeter). Kurulum yok,
   internet gerekmez; dosyalar yalnızca o tarayıcıda okunur, hiçbir yere gönderilmez.
2. Sol taraftaki kutulara dökümanları ekleyin: **Dosya seç** ya da dosyayı kutunun üstüne sürükleyin.
3. İsterseniz üstte kart adı, part number ve revizyonu yazın (`BUT.Identification`).
4. **Çalıştır** → sağdaki BUT.json kutusunda özet çıkar → **İndir** (ya da **Kopyala**).
5. Alttaki sekmeler: **Bulgular** (eksik / çelişkili veri), **Kaynak raporu** (her dosyanın
   bölüm haritası, tabloları ve hangi kolonun hangi alana eşlendiği), **BUT.json önizleme**.

Elinizde dosya yoksa **Örnek dosyalarla dene** sentetik bir BICD ve BRS yükler (`ornek/`).

## Ne okunuyor

| Girdi | Biçim | BUT.json'a giden |
|---|---|---|
| BICD | DOORS `.mif` | `BUT.Connectors` — §6.1.1 / §6.1.2 konnektörler (part number), §6.2.1 / §6.2.2 pin listesi (konnektörün `pins` dizisine), §8 mating part number |
| BRS | DOORS `.mif` | `BUT.Requirements` — metin kolonu ve kimlik ya da MoC kolonu olan her tablo; arayüz = tablonun bulunduğu bölüm başlığı (ya da Interface kolonu) |
| BCDD, BDDD | DOORS `.mif` | `sources[]` içinde bölüm haritası ve tablo listesi (şema verilince alanlara açılacak) |
| Şematik | herhangi | `sources[]` içinde ad, boyut, SHA-256 |

`.mif` olmayan bir dosya (ör. PDF) kaynak olarak kaydedilir, içeriği okunmaz.

## BUT.json (taslak şema `but.json/0.1`)

```json
{
  "$schema": "but.json/0.1",
  "generatedAt": "…", "generator": { "name": "BUT.json Üretici", "version": "0.1.0" },
  "BUT": {
    "Identification": { "name": "…", "partNumber": "…", "revision": "…" },
    "Connectors": [
      { "name": "J1", "scope": "external", "partNumber": "…", "matingPartNumber": "…",
        "type": "…", "contactCount": 9, "gender": null, "location": "…", "doorsObjectId": null,
        "sourceSections": ["6.1", "8", "6.2"],
        "pins": [ { "index": "1", "nameOnPin": "…", "direction": "…", "relatedPathFunctionality": "…",
                    "scope": "external", "doorsObjectId": null, "raw": { } } ],
        "raw": { "6.1": { }, "8": { } } }
    ],
    "Requirements": [
      { "id": "BRS-101", "text": "…", "interface": "3.1 Power Interface", "moc": ["MoC4"], "sov": "BVP",
        "section": "3.1 Power Interface", "raw": { } }
    ]
  },
  "sources": [ { "role": "BICD", "file": "…", "size": 0, "sha256": "…", "format": "mif",
                 "encoding": "…", "outline": [ { "number": "6.1.1", "title": "…" } ],
                 "tables": [ { "id": "1", "heading": "…", "columns": [ ], "rows": 0 } ],
                 "mapped": [ { "table": "1", "as": "6.1.1 External Connectors" } ] } ],
  "findings": [ { "level": "error | warning | info", "source": "BICD", "message": "…" } ]
}
```

Şema taslaktır: alanların detayı verildikçe genişleyecek. Kaynağa sadakat kuralı
`tools/mif/` ile aynı: adlı alanların yanında her satırın tüm kolonları `raw` içinde ham
adıyla durur, hiçbir kolon atılmaz.

## Ayar

Bölüm desenleri ve kolon takma adları sayfanın içindeki `CONFIG` bloğundadır
(`bicdSections`, `bicdColumns`, `brsColumns`). Gerçek bir dosyada bir tablo eşleşmezse
**Kaynak raporu** sekmesi tablonun başlık bağlamını ve kolon adlarını gösterir; ayar oradan
yapılır, kod değişmez. Eşlemeler `tools/mif/esleme/bicd.varsayilan.json` ile aynı başladı.

Okuma kuralları `tools/mif/mifparse/` ile aynıdır, gerçek DOORS export'unda görülen iki fark
eklendi: tabloların ayrı başlık satırı (`TblH`) yoksa kolon adları ilk gövde satırından alınır;
başlıklar `pHeading` gibi başlık etiketli paragraflardan tanınır (etiket yoksa numaralı satırdan).
Kodlama: dosyada `MIFEncoding` UTF-8 bildirilmişse UTF-8; değilse UTF-8 denenir, olmazsa
Windows-1254. `\xNN` kaçışları FrameRoman olarak çözülür ve bulgu olarak işaretlenir.

## Örnekler

`ornek/ornek_bicd.mif` (`tools/mif/test/` ile aynı, kasten kusurlu: J3'ün mating'i yok, J4
yalnızca pin listesinde) ve `ornek/ornek_brs.mif` sentetiktir; gerçek bir karta ait değildir.
Değiştirildiklerinde sayfaya yeniden gömmek için:

```
python3 ornek_gom.py
```
