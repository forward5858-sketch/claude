# BICD `.mif` ayrıştırıcısı

DOORS'tan FrameMaker (`.mif`) olarak alınan BICD export'unu okur, §6.1 / §6.2 / §8
tablolarını çıkarır ve doğrulama veritabanına yazar.

Şema için: [`../veritabani/`](../veritabani/)

```
python3 -m mifparse kesfet  <dosya.mif>                    # önce bu
python3 -m mifparse cikar   <dosya.mif> --proje P --cikti yukleme.sql
python3 -m mifparse yukle   <dosya.mif> --proje P --dsn postgresql:///dogrulama
```

## Önce `kesfet`

Gerçek bir dosyada **ilk koşulacak komut budur.** Hiçbir şey yazmaz; dosyadaki her
tabloyu, başlık bağlamını, kolonlarını, hangi bölüme eşleştiğini ve her kolonun
hangi alana gittiğini basar:

```
Tablo 1  [✓ 6.1.1 External Connectors]
  Başlık bağlamı : 6.1.1 External Connectors   (PgfTag=Heading3)
  Satır          : 2
  Kolonlar:
    Connector Name                     -> connector_name
    Part Number                        -> part_number
    Notes                              -> (raw'da kalır)
    | J1 | DAMA-9S-A197 | D-Sub 9 | 9 | Ön panel | RS422 bakım hattı
```

Eşleşmeyen tablo ya da kolon varsa rapor bunu söyler. `--json` ile makine okunur
çıktı verir.

## Katmanlar

| Modül | İşi | Belgeye bağımlı mı |
|---|---|---|
| `mif.py` | MIF sözdizimi: sözcük ayırma, ağaç, paragraf metni, kaçışlar, kodlama | Hayır |
| `tables.py` | Tabloları çıkarır, akıştaki `<ATbl>` çapasından başlık bağlamını bulur | Hayır |
| `mapping.py` | Başlık → bölüm, kolon adı → veritabanı alanı | Yapılandırmadan |
| `bicd.py` | Konnektör ve pin kayıtlarını kurar, birleştirir, denetler | Evet |
| `emit.py` | Tek işlemlik SQL üretir | — |
| `load.py` | psycopg ile doğrudan yükler | — |

Ayrımın sebebi: **MIF'in biçimi sabittir, bir kurumun BICD'sindeki başlık ve kolon
adları değildir.** Gerçek dosya geldiğinde kod değil
[`esleme/bicd.varsayilan.json`](esleme/bicd.varsayilan.json) ayarlanır.

## Eşleme yapılandırması

```json
{"bolumler": [
   {"ad": "6.1.1 External Connectors", "desen": "^6\\.1\\.1\\b",
    "tip": "connector", "scope": "external", "bicd_bolum": "6.1"}],
 "kolonlar": {
   "part_number": ["part number", "part no", "pn"]}}
```

- `desen` başlık metnine uygulanır. Başlıklar `<ATbl>` çapasının önündeki en son
  numaralı paragraftan alınır — paragraf etiketi adlarına güvenmez.
- Kolon adları normalleştirilerek karşılaştırılır (küçük harf, noktalama ve fazla
  boşluk atılır), yani `Part Number`, `PART NUMBER`, `Part-Number` aynıdır.
- **Eşleşmeyen kolon atılmaz**, satırın `raw` alanında ham adıyla saklanır.

## Kaynağa sadakat

Adlı alanların yanında her satırın tüm kolonları `raw` içinde durur. Konnektörün
`raw`'ı bölümlere göre gruplanır, çünkü bir konnektör gerçekten iki ayrı tablodan
gelir:

```json
{"6.1": {"Connector Name": "J2", "Contact Count": "13 pos", "Notes": "Güç girişi"},
 "8":   {"Connector Name": "J2", "Mating Part Number": "D38999/26FB35PN"}}
```

Pin tek tablodan geldiği için `raw`'ı düz sözlüktür.

Tür dönüşümü kaybettirmez: `Contact Count` alanı `13 pos` ise `contact_count`
sütununa `13` yazılır, `13 pos` ham hâliyle `raw`'da kalır.

## Yükleme yolları

**SQL dosyası (`cikar`).** Python sürücüsü kurulamayan kısıtlı makineler için.
Üretilen dosya yalnızca `psql -f` ile yüklenir:

```
psql -d dogrulama -v ON_ERROR_STOP=1 -f yukleme.sql
```

Tamamı tek `BEGIN … COMMIT` bloğudur; bir satır bile reddedilirse hiçbir şey yazılmaz.
Sonunda kalite kontrolü raporunu basar.

**Doğrudan (`yukle`).** `psycopg` kuruluysa. Aynı kayıtları yazar; ikisi de aynı
veritabanı durumunu üretir.

Aynı `(kart, doküman no, revizyon)` ikinci kez yüklenmek istenirse reddedilir.
Eşlemeyi ayarlarken tekrar yüklemek için `--taze` verin — sürüm silinip yeniden
yazılır. Baseline alınmış bir sürüm `--taze` ile bile silinemez; veritabanı
tetikleyicisi engeller.

## Yüklemeden önce yakalananlar

Veritabanına gitmeden durdurulur (`hata`): bir bölüme eşleşmiş ama konnektör adı ya
da pin index kolonu bulunamayan tablo · tekrar eden `(konnektör, pin index)`.

Kayda geçer ama durdurmaz (`uyarı`): §6.1'de olmayıp yalnızca pin listesinde geçen
konnektör (taslak satır açılır, SC01/SC02 bulgu olarak işaretler) · aynı alan için
çelişkili iki değer (ilki korunur) · sayıya çevrilemeyen kontak sayısı · kapsamı
belirlenemeyen konnektör.

Yükleme sonrası veritabanının kendi yumuşak kontrolleri (SC01–SC11) koşar ve
sonuç `quality_check` tablosuna yazılır.

## Sınırlar

Ayrıştırıcı **gerçek bir BICD `.mif` dosyası görülmeden** yazıldı. Sınanmış olan
MIF'in *biçimi*; sınanmamış olan bir kurumun BICD'sinin *düzeni*. Örnek dosya
geldiğinde beklenen iş:

1. `kesfet` koşulur, rapora bakılır.
2. `esleme/bicd.varsayilan.json` içindeki desenler ve kolon adları gerçeğine ayarlanır.
3. `vdb.direction_vocabulary` tablosu gerçek yön değerleriyle güncellenir.
4. Gerçek dosyadan türetilmiş, kısaltılmış bir örnek `test/` altına eklenir.

Bilinen belirsizlikler: FrameRoman kodlamalı (UTF-8 olmayan) dosyalarda `\xNN`
kaçışları `mac_roman` ile yaklaşık çözülüyor — Türkçe içerik için export'un UTF-8
olması gerekir · sayfalara bölünmüş uzun tabloların MIF'te tek `<Tbl>` olarak mı
yoksa parçalı mı geldiği doğrulanmadı · `<Variable>` ve `<XRef>` içeriği metne
katılmıyor.

## Testler

```
python3 -m unittest discover -s test -v
```

31 test; `pytest` gerekmez. Sentetik `test/ornek_bicd.mif` kasten kusurlu: J3'ün
mating'i yok, J4 yalnızca pin listesinde geçiyor, hiçbir satırda DOORS nesne
kimliği yok — böylece kontrollerin çalıştığı görülüyor.
