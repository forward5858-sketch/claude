# Doğrulama veritabanı

Kart doğrulama sürecinin verisinin durduğu yer. İlk doldurulan bölüm BICD'den
gelen **konnektör ve pin verisi**; şema baştan gereksinim, test item, test case
ve koşum sonuçlarını da alacak şekilde kuruldu.

```
createdb -E UTF8 dogrulama
python3 vdb.py kur --dsn postgresql:///dogrulama
```

| Dosya | Ne yapar |
|---|---|
| `vdb.py` | Yönetim aracı: `kur` · `goc` · `durum` · `arsivle` |
| `gocler/0001_temel_sema.sql` | Tablolar, kısıtlar, tetikleyiciler, roller, göç kütüğü |
| `gocler/0002_arsiv_kaydi.sql` | `archive_record` — üretilmiş arşiv dosyalarının kimliği |
| `tekrarlanabilir/R__gorunumler.sql` | Okuma görünümleri; test item ihtiyacının girdisi |
| `tekrarlanabilir/R__kontroller.sql` | `vdb.run_soft_checks()` — yumuşak kontroller |
| `tekrarlanabilir/R__arsiv.sql` | `vdb.archive_data_sql()` — arşiv dökümü |
| `ornek/ornek_veri.sql` | Temiz örnek yükleme: 2 konnektör, 11 pin, baseline'a kadar |
| `ornek/bozuk_veri.sql` | Kasıtlı bozuk örnek: sert ve yumuşak kontrollerin kanıtı |

`vdb.py` `psql`'i alt süreç olarak çağırır — Python paketi gerektirmez ve
Windows'ta da aynı şekilde çalışır. `psql`in PATH'te olması yeterli.

## Göç yönetimi

İki sınıf var, çünkü tablolar bir kez uygulanır ve geri alınamaz; görünüm ve
fonksiyonlar `CREATE OR REPLACE` olduğu için her seferinde yeniden uygulanabilir.

| | Nerede | Davranış |
|---|---|---|
| **Sürümlü göç** | `gocler/NNNN_ad.sql` | Bir kez uygulanır. **Uygulandıktan sonra değiştirilmez** — özeti tutmazsa `durum` uyuşmazlık bildirir, `goc` reddeder. Şema değişikliği yeni numaralı dosyadır |
| **Tekrarlanabilir** | `tekrarlanabilir/R__ad.sql` | Özeti değişince yeniden uygulanır. Serbestçe düzenlenir |

Uygulanan her şey `vdb.schema_version` tablosuna yazılır: hangi veritabanının
hangi şema sürümünde olduğu oradan okunur. Her göç kendi işleminde koşar;
başarısız olursa hiçbir şey yazılmaz.

```
python3 vdb.py durum --dsn ...          # uygulanmış / bekleyen / uyuşmazlık
python3 vdb.py goc   --dsn ... --kuru   # ne yapacağını yaz, uygulama
python3 vdb.py goc   --dsn ...
```

Roller `NOLOGIN` kurulur; giriş yapacak kullanıcıları IT açar — bu araç şifre
üretmez:

```sql
CREATE ROLE <kullanici> LOGIN PASSWORD '<sifre>';
GRANT vdb_engineer TO <kullanici>;   -- ya da vdb_reader / vdb_loader
```

---

## Model kararı

**İlişkisel model.** Bu verinin asıl değeri birleştirmede: konnektör → pin bir
ana-alt ilişkisi, ve ilerideki izlenebilirlik zinciri (gereksinim ↔ arayüz ↔ MoC
↔ test case ↔ koşum sonucu) baştan sona join demek. Doküman tabanlı bir yapı bu
join'leri kaybettirir; graf veritabanı zincire biçim olarak uyar ama bu veri
hacminde SQL'in recursive CTE'si aynı işi görür, işletme yükü karşılığını vermez.

**Motor: PostgreSQL** — gerçek çok kullanıcılı eşzamanlı yazma, rol bazlı yetki,
`JSONB` ile ham DOORS attribute'larının kayıpsız saklanması, lisanssız, kurum içi
sunucuda standart.

Baseline alınan her BICD sürümü ayrıca **kendine yeten bir `.sql` dosyasına**
dökülür: o sürümün şeması ve yalnızca o sürüme ait satırlar tek metin dosyasında,
SHA-256'lı. Denetçiye gösterilecek somut bir kayıt olur ve herhangi bir
PostgreSQL'e geri yüklenir. Bu, ekibin zaten yaptığı "rel baseline al → HCMP
CSAR'a işler" akışına oturuyor.

### Değerlendirilen diğer motorlar

| Aday | Durum |
|---|---|
| **MariaDB** | En güçlü alternatif. GPL, her yerde kurulu, IT için tanıdık. Bedeli: `JSONB` yok — `raw` kolonu `LONGTEXT` + `JSON_VALID` olur, indeksli erişim için generated column gerekir; dizi tipi yok, `source_sections` JSON dizisine döner. Gerisi birebir aynı |
| **MySQL (Oracle)** | JSON'u MariaDB'den iyi (ikili saklama, multi-valued index) ama Oracle sahipliği kurumsal lisans tedirginliği yaratıyor. Bu ailede MariaDB tercih edilir |
| **Oracle Database XE** | Ücretsiz. 12 GB veri / 2 CPU thread sınırı bu hacimde alakasız, JSON desteği güçlü. Kurumda zaten Oracle varsa IT'nin işi kolay. Kurulum ağır; XE'nin üretim kullanımı için lisans metni IT tarafından okunmalı |
| **Firebird** | Küçük, sunucu modu var, açık kaynak. Topluluğu küçük ve JSON desteği zayıf — on yıl sonra kimin bakacağı sorusu ağır basıyor |
| **SQLite** (canlı ya da arşiv) | **Kullanıcı kararıyla elendi.** Çok kullanıcılı yazımda ağ paylaşımındaki dosya bozulur; arşiv rolünü de `.sql` dökümü üstlendi |
| **DuckDB** | Analitik olarak çok iyi ama dosya formatı sürümler arasında değişti; on yıllık denetim arşivi için uygun değil |
| **Bulut** (Azure SQL, AWS RDS, Supabase, Firebase) | Değerlendirme dışı: mühendislik verisi kurum ağının dışına çıkmaz. Plan panosu bulutta durur ama o süreç modelidir; kart verisi oraya girmez |
| **MongoDB / CouchDB** | Doküman modeli join'leri kaybettirir; izlenebilirlik matrisi baştan sona join |
| **Neo4j** | Zincire biçim olarak uyar, bu hacimde işletme yükü karşılığını vermez |
| **Excel / SharePoint listesi** | Kısıt yok, geçmiş yok, eşzamanlı düzenlemede çakışma var |
| **MS SQL Server** | **Kullanıcı kararıyla elendi** |

Karar PostgreSQL'de sabit. Kurum ileride yalnızca MySQL/MariaDB koşuyorsa şema
MariaDB'ye taşınır — kayıp sadece `raw` kolonunun ergonomisi.

**Tanımlayıcı dili ASCII İngilizce.** Türkçe karakter tablo ve kolon adlarında
ODBC, Excel bağlantıları ve eski araçlarda kodlama sorunu çıkarıyor. Veri
içeriği elbette Türkçe.

---

## Üç katman

Katmanların karışmaması bu tasarımın ana kuralı. Denetimde "bu satır BICD'den mi
geldi yoksa siz mi türettiniz" sorusu tek kelimeyle cevaplanmalı.

**1 — Çapa.** `board`, `bicd_version`. Her veri satırı bir BICD **sürümüne**
asılır; birim kart değil, kartın BICD sürümüdür. Koşulmuş bir testin hangi veriye
dayandığı sonradan sorulacak.

**2 — Kaynak veri (BICD'den birebir).** `connector`, `pin`. Bu iki tabloya
yalnızca yükleyici rol yazar. Elle düzeltilmez — kaynakta hata varsa CR açılır.

**3 — Bizim ürettiğimiz veri.** `mating_check` (mating part number doğrulaması),
`pin_interface` (pinin hangi arayüz tipine düştüğü). İkisi de ekleme günlüğü:
düzeltme yeni satırdır, eski silinmez; güncel hâl görünümden okunur.

**4 — Kayıt.** `import_run`, `quality_check`.

---

## Veri sözlüğü

### `board` — kart
| Kolon | Anlam |
|---|---|
| `name`, `project` | Kart adı ve proje; ikisi birlikte tekil |

### `bicd_version` — BICD sürümü (izlenebilirlik çapası)
| Kolon | Anlam |
|---|---|
| `doc_number`, `revision` | BICD doküman numarası ve revizyonu |
| `doors_baseline` | DOORS baseline adı |
| `view_name` | **Export anındaki DOORS view'ı.** MIF yalnızca o anda açık olan kolonları yazar; hangi view kullanıldığı verinin eksiksizliğinin kanıtı |
| `mif_filename`, `mif_sha256` | Kaynak dosya ve özeti |
| `status` | `draft` → `verified` → `baselined` |

### `connector` — §6.1 Connectors + §8 Constraints
| Kolon | Kaynak |
|---|---|
| `connector_name` | §6.1 — J1, J2 … |
| `scope` | 6.1.1 external / 6.1.2 internal (ayrım **ekipman bazlı**) |
| `part_number` | §6.1 — kartın **kendi** konnektörü |
| `mating_part_number` | §8 — **karşılığı** |
| `connector_type`, `contact_count`, `gender`, `location` | §6.1 (view'da açıksa) |
| `source_sections` | Konnektörün hangi bölümlerde göründüğü: `{'6.1','8'}`. §6.1 ↔ §8 örtüşme kontrolü buradan yapılır |
| `raw` | §6.1'in **tüm** kolonları, ham |

### `pin` — §6.2 Connection List
| Kolon | Kaynak |
|---|---|
| `pin_index` | §6.2 Pin Index — **metin tipi**, çünkü pin numaraları alfanümerik olabiliyor (A1, B12) |
| `name_on_pin` | §6.2 Name on Pin |
| `direction` | §6.2 Direction |
| `related_path_functionality` | §6.2 Related Path Functionality |
| `scope` | 6.2.1 external / 6.2.2 internal |
| `doors_object_id` | Kaynağa geri iz sürmek için |
| `raw` | §6.2'nin **tüm** kolonları, ham |

**`raw` kolonu "değiştirmeden hepsini tutalım" şartının karşılığı.** Adlı
kolonlar günlük işte kullandıklarımız; `raw` ise DOORS'un o satırda verdiği her
attribute'u adıyla ve değeriyle olduğu gibi taşır. Hiçbir şey atılmaz, hiçbir şey
tahmin edilmez — `.mif` geldiğinde beklenmeyen bir kolon çıkarsa şema değişmeden
veri girer; sık kullanılırsa sonradan adlı kolona terfi eder.

```sql
-- Ham attribute'a erişim
SELECT connector_name, raw ->> 'Shell Size' FROM vdb.connector;
```

### `direction_vocabulary`
Yön değerlerinin kapalı sözlüğü. Kodda gömülü liste yok; SC07 kontrolü bu tabloya
bakar. Şu an genel değerlerle dolu (`IN`, `OUT`, `BIDIR`, `POWER`, `GROUND`, `NC`,
`SHIELD`) — **gerçek değerler `.mif` örneği geldiğinde güncellenecek.**

---

## Yürüten kurallar

**Değişmezlik.** Satırlar yerinde güncellenmez. Yeni BICD revizyonu → yeni
`version_id` → yeni satır kümesi; eski sürüm durur. Baseline alınmış bir sürümün
`connector` ve `pin` satırları veritabanı tetikleyicisiyle kilitlidir
(`guard_baselined`) — INSERT, UPDATE ve DELETE reddedilir.

**Roller.**

| Rol | Yetki |
|---|---|
| `vdb_reader` | Salt okuma |
| `vdb_engineer` | Kaynağı okur; yalnızca `mating_check` ve `pin_interface`'e yazar |
| `vdb_loader` | Kaynak tablolara yazan tek rol (`.mif` ayrıştırıcısı bu rolle bağlanır) |
| `vdb_admin` | Tam yetki |

**Sert / yumuşak kontrol ayrımı.** Kaynak dokümanın eksiği yüklemeyi başarısız
etmemeli, ama kayda geçmeli.

| | Kontrol | Davranış |
|---|---|---|
| **Sert** — veritabanı kısıtı | `pin → connector` FK · `UNIQUE(version, connector_name)` · `UNIQUE(connector, pin_index)` · zorunlu alanlar · `contact_count > 0` | Yükleme reddedilir, işlem geri alınır |
| **Yumuşak** — `quality_check`'e yazılır | SC01–SC11 (aşağıda) | Yükleme tamamlanır; bulgu varsa sürüm baseline'a **çıkamaz** (`guard_baseline_promotion`) |

| Kod | Kontrol |
|---|---|
| SC01 | Konnektör §8'de var ama §6.1'de yok |
| SC02 | Konnektör §6.1'de var ama §8'de yok |
| SC03 | Kartın kendi part number'ı boş (§6.1) |
| SC04 | Mating part number boş (§8) |
| SC05 | Konnektörün §6.2'de hiç pin satırı yok |
| SC06 | Name on Pin boş |
| SC07 | Direction değeri sözlükte yok |
| SC08 | Kullanılan pin sayısı kontak sayısını aşıyor |
| SC09 | Related Path Functionality boş — o pin arayüze düşmez |
| SC10 | Pin kapsamı konnektör kapsamıyla çelişiyor |
| SC11 | DOORS nesne kimliği boş |

**Yükleme tek işlem.** `.mif` → ayrıştırma → tek INSERT bloğu → kontroller →
commit. Yarım yüklenmiş sürüm oluşmaz.

---

## Sürüm yaşam döngüsü

```
.mif export  →  yükleme (tek transaction)  →  status = draft
                        ↓
              run_soft_checks()  →  bulgu varsa CR / düzeltme, yeniden yükle
                        ↓  (tüm kontroller pass)
              status = baselined   ← tetikleyici bulgu varsa reddeder
                        ↓
         vdb.py arsivle  →  .sql + SHA-256  →  HCMP  →  CSAR kaydı
```

## Arşiv

```
python3 vdb.py arsivle --dsn ... --surum 3 --dizin /arsiv
```

Yalnızca `baselined` sürümler arşivlenir — arşiv dondurulmuş sürümün kaydıdır,
taslak arşivlenmez. Üretilen dosya **kendine yeter**: önce göç ve tekrarlanabilir
dosyalarının tamamı, sonra o sürüme ait satırların `INSERT`'leri. Boş bir
veritabanına iner:

```
createdb -E UTF8 denetim && psql -d denetim -v ON_ERROR_STOP=1 -f <arsiv>.sql
```

Dosya adı `<proje>_<kart>_<dokno>_<rev>_<YYYYAAGG>.sql`; Türkçe harfler ASCII'ye
çevrilir, dosya iki işletim sisteminde de sorunsuz taşınır. Araç SHA-256'yı
hesaplar, `archive_record` tablosuna yazar (`ON DELETE RESTRICT` bilinçli:
arşivlenmiş bir sürüm silinemez) ve CSAR'a girecek satırı ekrana basar.

Üç incelik:

- Birincil anahtarlar `GENERATED ALWAYS AS IDENTITY` olduğu için `INSERT`'ler
  `OVERRIDING SYSTEM VALUE` ile yazılır; yoksa kimlikler korunmaz ve satırlar
  arası bağlar kayar.
- Sürüm önce `draft` olarak yüklenir, gerçek durumuna **kalite kayıtlarından
  sonra** alınır. İki sebeple: baseline kilidi `baselined` bir sürüme kaynak satır
  yazılmasını engeller, ve terfi kapısı açık bulgu olmadığını o anda doğrular —
  yani kurcalanmış bir arşiv baseline olarak geri yüklenemez.
- Sonda kimlik dizileri satırların ötesine alınır; yoksa geri yüklenmiş arşive
  yeni satır eklenmek istendiğinde birincil anahtar çakışır.

---

## Aşağı akış — bu veri nerede kullanılır

| Nereye | Ne için |
|---|---|
| Aşama 2 — arayüz ve pin tutarlılığı | BICD pinout ile şematik/BDDD çapraz kontrolü |
| Aşama 3 — arayüz tipine göre ayrıştırma | `related_path_functionality` + `name_on_pin` → arayüz tahsisi (`pin_interface`) |
| Aşama 4 — test item ihtiyaç/kabiliyet tablosu | `v_connector_pin_summary`: konnektör başına pin sayısı, yön dağılımı, ayrı yol sayısı → kanal sayısı ve protokol ihtiyacı |
| Aşama 4 — ITA / breakout pin ve kablo listesi | Doğrudan `v_pin`'den üretilir |
| Sipariş ve stok | `v_mating_status`: doğrulanmış mating part number + adet |

```sql
-- Test item kabiliyet ihtiyacının ham girdisi
SELECT connector_name, scope, contact_count, used_pin_count,
       distinct_path_count, direction_breakdown
  FROM vdb.v_connector_pin_summary ORDER BY connector_name;
```

---

## İleride aynı veritabanına eklenecekler

`requirement` (BRS) · `interface` · `moc_allocation` · `test_item` · `test_case` ·
`test_run` · `test_result` · `csar_entry`. İlişkisel modeli seçmenin asıl gerekçesi
bu — izlenebilirlik matrisi tek bir sorguyla çıkacak.

## Açık nokta

Motor kararı verildi: **PostgreSQL**. MS SQL Server ve SQLite kullanıcı kararıyla
elendi. Geriye kalan tek dış bağımlılık, kurumun bir PostgreSQL sunucusu
sağlaması; şema ve araçlar hazır ve gerçek bir PostgreSQL 16 kümesinde uçtan uca
doğrulandı (kurulum, göç, uyuşmazlık reddi, arşiv üretimi ve arşivin boş bir
veritabanına geri yüklenmesi).

`.mif` ayrıştırıcısı henüz yazılmadı: örnek dosya bekleniyor. Hedef şema artık belli.
