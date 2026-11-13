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

Okunan biçimler: **DOORS Excel export'u (.xlsx)** — tercih edilen —, CSV (`,` `;` ya da sekme ayraçlı)
ve FrameMaker `.mif`. Biçim dosyanın içeriğinden anlaşılır, uzantıya bakılmaz.

| Girdi | Biçim | BUT.json'a giden |
|---|---|---|
| BICD | .xlsx / .csv / .mif | `BUT.Connectors` — §6.1.1 / §6.1.2 konnektörler (part number), §6.2.1 / §6.2.2 pin listesi (konnektörün `pins` dizisine), §8 mating part number |
| BRS | .xlsx / .csv / .mif | `BUT.Requirements` — metin kolonu ve kimlik ya da MoC kolonu olan her tablo; arayüz = tablonun bulunduğu bölüm başlığı (ya da Interface kolonu) |
| BCDD, BDDD | .xlsx / .csv / .mif | `sources[]` içinde bölüm haritası ve tablo listesi (şema verilince alanlara açılacak) |
| Şematik | herhangi | `sources[]` içinde ad, boyut, SHA-256 |

Okunamayan bir dosya (ör. PDF) kaynak olarak kaydedilir, içeriği okunmaz.

### Excel / CSV export'u nasıl okunur

DOORS tablo export'unda her satır bir DOORS nesnesidir. İlk dolu satır kolon adlarıdır.
Yapı kolonları (`CONFIG.doorsColumns`): **Object Identifier**, **Object Number**, **Object Heading**,
**Object Text** (ya da birleşik "Object Heading and Object Text" ana kolonu), Object Level.

- **Başlık satırı:** Object Heading dolu, Object Text boş olan nesne. Ana kolon tek başınaysa
  Object Number'ı `6.1.1` biçiminde olan nesne (metin nesneleri `6.1.1-3` gibi numaralanır).
- Başlık, ardından gelen nesnelerin **bölüm bağlamıdır** (ör. `6.2.1 External Connection List`);
  BICD bölüm kuralları ve BRS arayüz bilgisi buradan gelir.
- **BICD:** konnektör adı kolonu boş olan nesneler açıklama metnidir, atlanır. Konnektör her
  bölümde ayrı bir DOORS nesnesi olduğu için kimlikler `doorsObjectIds` içinde bölüm bölüm tutulur.
- **BRS** (kullanıcının verdiği DOORS düzeni; kolonlar ilk satırdan adlarıyla bulunur, sıra ve fazladan
  kolonlar önemli değil):

  | Kolon | Kullanımı |
  |---|---|
  | `ID` | Prefix + Absolute Number (Object Identifier) → `id` |
  | `Object Text` | Gereksinim metni; Heading nesnesinde başlık metni |
  | `Object Type` | `Heading` → bölüm başlığı (sonraki nesnelerin arayüzü). `Allocated`, `Derived`, `Design Goal` → gereksinim (`CONFIG.brsRequirementTypes`). `Remark`, `Figure`, `Table` → alınmaz. Tanınmayan tip bulgu olur. |
  | `Verification Method` | `MoC1: Design Review` gibi; hücrede birden çok değer olabilir (satır satır) → `moc`, `verificationMethod` |
  | `Source of Verification` | `MoC4 -> BVP(BVP-0001)` gibi; MoC başına bir satır → `sov` (MoC, döküman, numara) |

  Kontroller: MoC'u olmayan gereksinim; Source of Verification karşılığı olmayan MoC; MoC'u Verification
  Method'da olmayan SoV satırı; tekrar eden ID.

Kolon düzeni şimdilik varsayımdır (`ornek/*.xlsx`); gerçek export gelince `CONFIG` ona göre ayarlanacak.

## BUT.json (taslak şema `but.json/0.1`)

```json
{
  "$schema": "but.json/0.1",
  "generatedAt": "…", "generator": { "name": "BUT.json Üretici", "version": "0.1.0" },
  "BUT": {
    "Identification": { "name": "…", "partNumber": "…", "revision": "…" },
    "Connectors": [
      { "name": "J1", "scope": "external", "partNumber": "…", "matingPartNumber": "…",
        "type": "…", "contactCount": 9, "gender": null, "location": "…", "doorsObjectIds": { "6.1": "…", "8": "…" },
        "sourceSections": ["6.1", "8", "6.2"],
        "pins": [ { "index": "1", "nameOnPin": "…", "direction": "…", "relatedPathFunctionality": "…",
                    "scope": "external", "doorsObjectId": null, "raw": { } } ],
        "raw": { "6.1": { }, "8": { } } }
    ],
    "Requirements": [
      { "id": "BRS-102", "type": "Derived", "text": "…", "interface": "Power Interface", "section": "Power Interface",
        "moc": ["MoC1", "MoC4"],
        "verificationMethod": [ { "moc": "MoC1", "name": "Design Review", "text": "MoC1: Design Review" },
                                { "moc": "MoC4", "name": "Laboratory Test", "text": "MoC4: Laboratory Test" } ],
        "sov": [ { "moc": "MoC1", "document": "BDDD", "number": "BDDD-0042", "text": "MoC1 -> BDDD(BDDD-0042)" },
                 { "moc": "MoC4", "document": "BVP", "number": "BVP-0001", "text": "MoC4 -> BVP(BVP-0001)" } ],
        "raw": { } }
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

Hepsi sentetiktir; gerçek bir karta ait değildir. Kasten kusurlu: J3'ün mating'i yok, J4 yalnızca
pin listesinde, BRS-202'nin MoC'u yok.

- `ornek/ornek_bicd.xlsx`, `ornek/ornek_brs.xlsx` — varsayılan DOORS Excel düzeni; sayfaya gömülü,
  **Örnek dosyalarla dene** bunları yükler. Üretmek için: `python3 ornek/ornek_uret.py` (openpyxl).
- `ornek/ornek_bicd.mif` (`tools/mif/test/` ile aynı), `ornek/ornek_brs.mif` — .mif yolu için.

Örnekler değişince sayfaya yeniden gömmek için: `python3 ornek_gom.py`
