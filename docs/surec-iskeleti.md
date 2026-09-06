# Kart Doğrulama Otomasyonu — Süreç İskeleti

Tasarım dosyalarının okunmasıyla başlayıp raporun yayınlanmasıyla biten aşamalar.
Bu dosya yalnızca aşama başlıklarını içerir; her aşamanın detayı (girdi/çıktı, yapay zeka rolü, kontrol noktası) ayrı ayrı planlanacaktır.

**Canlı plan panosu:** https://claude.ai/code/artifact/08b51fed-febf-4855-b04f-6601fc341962

Pano düzenleme yüzeyidir; bu depo kalıcı kayıttır. Pano iç içe bir akış tuvalidir: her aşama bir kutudur, kutunun içine girilip alt kutular tanımlanabilir (sınırsız derinlik). Kutular aynı seviyede tipli bağlantılarla ilişkilendirilir:

- **Sonra gelir** — sıralama (A → B: B, A'dan sonra gelir)
- **Besler** — A'nın çıktısı B'ye girdi olur
- **Geri besleme verir** — A, B'ye geri besleme verir
- **Bloklar** — A tamamlanmadan B başlayamaz
- **Diğer** — serbest etiketli ilişki

Kutu detayları (girdiler, çıktılar, yapay zekanın rolü, kodun rolü, kontrol noktası, notlar) ve durumlar panoda düzenlenir; depo dosyaları panodaki veriden üretilir.

## Aşama 1 — Tasarım dosyalarının okunması ve yapılandırılması

BICD, BRS, BCDD ve BDDD dökümanları ile şematik/netlist ve FPGA constraint dosyaları içeri alınır; yapılandırılmış veriye dönüştürülür.

İçeri alınan dökümanlar (panoda Aşama 1'in içindeki kutular) ve bölümleri:

- **BICD — Arayüz dökümanı:** Kartın konnektörleri ve pinleri tek tek verilir; kartı mekanik açıdan değerlendiren bir mekanik bölümü de vardır.
  - Konnektörler ve pinler — kartın her konnektörü ve pini tek tek listelenir.
  - Mekanik bölümü — kartın mekanik açıdan değerlendirilmesi.
- **BRS — Gereksinim dökümanı:** Kartın gereksinimleri arayüz arayüz bölümlenmiştir; her gereksinim için doğrulama yöntemi (MoC) ve doğrulama kaynağı (Source of Verification) verilir.
  - Arayüz bazlı gereksinimler — gereksinimler arayüz arayüz bölümlenmiştir.
  - Doğrulama yöntemleri (MoC) — her gereksinimin doğrulama yöntemi; ör. MoC1, MoC4.
  - Source of Verification — gereksinimin nereden doğrulanacağı; ör. MoC1 gereksinim → şematik, MoC4 gereksinim → BVP.
- **BCDD — Kavramsal tasarım dökümanı:** Kartın kavramsal (conceptual) tasarımı.
- **BDDD — Nihai tasarım dökümanı:** Kartın nihai tasarım bilgileri: hangi entegreler hangi sebeple seçildi; karttaki özellikler yol yol (path path) açıklanır.
  - Entegre seçimleri — hangi entegreler hangi sebeple seçildi.
  - Kart özellikleri (path path) — karttaki özellikler yol yol açıklanır.

## Aşama 2 — Gereksinim ve tasarım dökümanı incelemesi (yorum üretimi)

BRS, BICD, BCDD ve BDDD kontrol listesi ve teknik tutarlılık kontrolleriyle incelenir; yorumlar Crucible ya da JIRA + Excel üzerinden iletilir ve kapatılır. Bu sırada arayüzler kaba okunup test item ön çalışması başlar.

- **Girdiler:** Aşama 1'den yapılandırılmış BRS, BICD, BCDD, BDDD · ~20 maddelik inceleme kontrol listesi · önceki projelerin kabul edilmiş yorumları ve karşılıkları (checklist iyileştirme için)
- **Çıktılar:** Döküman başına yorum listesi (Crucible / JIRA review sayfası + Excel yorum tablosu) · ön çalışma notları: kaba arayüz listesi, test item ihtiyaçları, cihaz siparişleri
- **Yapay zekanın rolü (öneri):** Kontrol listesi maddelerini döküman üzerinde otomatik uygulayıp bulgu taslağı çıkarmak; gereksinim kalitesi, MoC/SoV, tasarım↔gereksinim ve pin tutarlılığı bulgularını yorum taslağı olarak yazmak; önceki kabul edilmiş yorumlardan checklist değişiklik talebi önermek.
- **Kodun rolü (öneri):** Link/referans varlığı, ID tekilliği, pin tablosu çapraz kontrolü gibi deterministik kontroller; yorumların Excel/JIRA formatına dönüştürülmesi ve kapanış takibi.
- **Kontrol noktası (öneri):** Yorumlar iletilmeden önce mühendis onayı; checklist değişiklik talepleri kullanıcı onayı olmadan işlenmez.

Aşama 2'nin içindeki kutular:

- **Kontrol listesi ile inceleme:** Yaklaşık 20 maddelik kontrol listesi (gramer hataları, linklerin varlığı vb.) dört dökümana uygulanır.
  - Kontrol listesi maddeleri (~20) — maddeler ileride tek tek girilecek.
  - Checklist iyileştirme sekansı (ileride) — bkz. Hatırlatmalar. Maddelere "geri besleme verir" (değişiklik talebi).
- **Gereksinim kalitesi:** Belirsiz ifade, eksik değer/tolerans/birim, test edilebilirlik, çelişen gereksinimler.
- **MoC ve Source of Verification kontrolü:** Doğrulama yöntemi uygun mu; doğrulama kaynağı (şematik, BVP vb.) doğru adresi gösteriyor mu.
- **Tasarım ↔ gereksinim tutarlılığı:** BCDD/BDDD her gereksinimi karşılıyor mu; entegre seçimleri gereksinimle uyumlu mu.
- **Arayüz ve pin tutarlılığı:** BICD pinout ile BDDD/şematik ve BRS arayüz gereksinimleri birbirini tutuyor mu; mekanik uyum.
- **Yorumların iletilmesi ve takibi:** Beş inceleme kutusunun bulguları buraya akar ("besler").
  - Crucible üzerinden review.
  - JIRA review sayfası + Excel yorum tablosu.
- **Ön çalışma: arayüz okuma ve test item hazırlığı:** Yorum aşamasındayken arayüzler kaba haliyle okunur; gerekecek testler (ör. fiber optik) araştırılır, eksik cihaz siparişleri verilir. Kök seviyede Aşama 2 → Aşama 4 "besler" bağlantısı olarak gösterildi.
- **Olgunluk şartı (resmi koşum için):** Resmi koşum ve rapor için gereksinimler Rel Baseline ile yayınlanmış ve tasarım donmuş olmalı. Donan tasarıma yeni revizyon gelirse iki yol: (1) doğrulama faaliyetleri yeni revizyona göre revize edilir; (2) mevcut haliyle devam edilir, yeni revizyon için doğrulama ileride tekrarlanır. Ön çalışma bu şartı beklemez.

## Aşama 3 — Arayüz ve MoC analizi (kartın parçalara ayrılması)

Gereksinimler arayüz tipine göre gruplanır; her gereksinimin MoC'u ve doğrulama kaynağı netleştirilir. Çıktı: tahsis tablosu, izlenebilirlik matrisi, BVP bölüm iskeleti, kaba test item ihtiyaç listesi.

- **Girdiler:** Aşama 1'den yapılandırılmış BRS (arayüz bazlı gereksinimler, MoC, Source of Verification), BICD (konnektör/pin listesi), BDDD (özellikler/yollar) · Aşama 2 ön çalışma notları
- **Çıktılar:** Gereksinim–arayüz–MoC tahsis tablosu · İzlenebilirlik matrisi (VCRM/RTM) · BVP bölüm iskeleti (arayüz arayüz) · Kaba test item ihtiyaç listesi (arayüz başına ATE/ITA/breakout/test SW/test PLD)
- **Yapay zekanın rolü (öneri):** Gereksinimleri arayüz tipine göre sınıflandırmak; BRS'deki MoC ve SoV'yi okuyup tahsis tablosunu doldurmak; MoC/SoV tutarsızlıklarını ve arayüze düşmeyen gereksinimleri işaretlemek; her arayüz için test item ihtiyacını taslak olarak önermek.
- **Kodun rolü (öneri):** Tahsis tablosunu ve izlenebilirlik matrisini gereksinim listesinden deterministik üretmek; her gereksinimin tam bir arayüze ve tek bir MoC'a atandığını doğrulamak (kapsama %100); BVP bölüm iskeletini arayüz listesinden şablonla üretmek.
- **Kontrol noktası (öneri):** Tahsis tablosu mühendis onayından geçmeden BVP iskeleti ve test item ihtiyaç listesi üretilmez.

MoC tanımları (kurum):

- **MoC1 — Design Review:** tasarım/şematik incelemesiyle doğrulama; kaynak: şematik / tasarım dökümanı.
- **MoC2 — Analiz / Hesaplama:** analiz veya hesap (calculation) raporuyla doğrulama.
- **MoC4 — Fonksiyonel Test:** lab ortamında gerçek test; kaynak: BVP.
- **MoC7 — Inspection:** muayene ile doğrulama.
- MoC3, MoC5 ve MoC6 tanımı verilmedi; kurumda kullanılıyorsa eklenecek.

Sorumluluk: MoC4 (BVP) dışındaki gereksinimlerin doğrulanması da doğrulama ekibinin sorumluluğundadır; kanıt kaydını ekip tutar.

Aşama 3'ün içindeki kutular:

- **Arayüz tipine göre ayrıştırma:** Kart arayüz tipine göre parçalara ayrılır; her gereksinim bir arayüze düşer. Arayüz tipleri ileride tek tek girilecek.
- **MoC atama:** Her gereksinimin doğrulama yöntemi (içinde MoC1, MoC2, MoC4, MoC7 kutuları).
- **Doğrulama kaynağı (SoV) ve sorumluluk:** Her gereksinimin nerede doğrulanacağı (şematik, analiz raporu, BVP, muayene).
- **Gereksinim–arayüz–MoC tahsis tablosu** (çıktı): Üç analiz kutusu bunu "besler".
- **İzlenebilirlik matrisi (VCRM/RTM)**, **BVP bölüm iskeleti**, **Kaba test item ihtiyaç listesi** (çıktılar): Tahsis tablosu bunları "besler".
- Kök seviyede Aşama 3 → Aşama 6 (BVP yazımı) "besler" bağlantısı: BVP bölüm iskeleti + izlenebilirlik matrisi.

## Aşama 4 — Test item ihtiyaçlarının belirlenmesi ve tanımlanması

Aşama 3'teki kaba ihtiyaç listesinden her arayüz için gerekli test itemlar (ATE, ITA, Breakout Board, Test Software, Test PLD) ve kabiliyetleri belirlenir; her item tanımlanır. Tasarımı doğrulama ekibi yapar; üretim bazen dış firmaya verilir.

- **Girdiler:** Aşama 3 kaba test item ihtiyaç listesi ve tahsis tablosu · BICD konnektör/pin listesi · BDDD (FPGA, özellikler) · Aşama 2 ön çalışma notları (cihaz siparişleri) · standart ATE kabiliyet envanteri
- **Çıktılar:** Test item ihtiyaç/kabiliyet tablosu · ITA / breakout pin ve kablo listesi · Test SW fonksiyon listesi · Test PLD fonksiyon ve pin listesi
- **Yapay zekanın rolü (öneri):** Arayüz ihtiyacından item kabiliyetlerini türetmek (kanal sayısı, protokol, seviye, ölçüm aralığı); standart ATE envanteriyle eşleyip eksikleri (proje özel ATE, sipariş) işaretlemek; Test SW ve Test PLD fonksiyon listelerini arayüz tiplerinden taslak önermek.
- **Kodun rolü (öneri):** BICD pin listesinden ITA/breakout pin ve kablo listesini deterministik üretmek; ihtiyaç ↔ kabiliyet eşlemesini doğrulamak (her ihtiyaç bir kaynağa düşüyor mu); listeleri tablo/şablona dökmek.
- **Kontrol noktası (öneri):** Kabiliyet tablosu ve pin/kablo listesi mühendis onayından geçmeden item tasarımına geçilmez; üretim dış firmaya verilecekse teknik paket onayı.

Kurallar:

- **ATE politikası:** Her projeyi destekleyen standart ATE'ler vardır; proje özelinde spesifik ATE ihtiyacı doğabilir. Proje için üretilen ATE ileride genel ATE olarak diğer projelerde kullanılabilir.
- **Tasarım ve üretim sorumluluğu:** Tüm itemları doğrulama ekibi tasarlayabilir; bazen üretim ayrı bir firmaya verilir.

Aşama 4'ün içindeki kutular ve akış:

- **Test item ihtiyaç/kabiliyet tablosu** (çıktı): Arayüz → hangi item → hangi kabiliyet. Beş test item kutusunu "besler".
- **Test itemlar:** ATE — Otomatik test ekipmanı · ITA — Arayüz test adaptörü · Breakout Board · Test Software · Test PLD. Her birinin alt itemları kullanıcı tarafından verilecek (bkz. Hatırlatmalar).
- **ITA / breakout pin ve kablo listesi** (çıktı): ITA ve Breakout Board kutuları bunu "besler"; BICD pinlerinden ATE kaynaklarına eşleme.
- **Test SW fonksiyon listesi** (çıktı): Test Software kutusu "besler".
- **Test PLD fonksiyon ve pin listesi** (çıktı): Test PLD kutusu "besler".
- Kök seviyede Aşama 4 → Aşama 7 (TISVP yazımı) "besler" bağlantısı: test item seti ve kabiliyetleri.

## Aşama 5 — Test item'ların yoruma çıkması ve yayınlanması

Her test item kendi alt itemlarıyla yoruma çıkar; yorumlar dökümanlarla aynı kanaldan (Crucible / JIRA + Excel) yürütülür ve kapatılır; item, konfigürasyon kaydı (baseline) ve döküman numarası + revizyonla yayınlanır. Tüm itemlar yayınlanmadan BVP yoruma çıkmaz.

- **Girdiler:** Aşama 4'te tanımlanan test itemlar ve alt itemları (kullanıcı verecek) · ihtiyaç/kabiliyet tablosu · pin/kablo listeleri ve fonksiyon listeleri
- **Çıktılar:** Item başına yorum listesi ve kapanış kaydı · yayınlanmış test item seti: konfigürasyon kaydı (baseline) + döküman numarası/revizyon
- **Yapay zekanın rolü (öneri):** Item ürünlerine ön-review: ihtiyaç/kabiliyet tablosu ↔ item tasarımı eşleşiyor mu, pin/kablo listesi ↔ BICD/şematik tutarlı mı; yorum taslağı yazmak; yorum cevaplarını triyaj etmek.
- **Kodun rolü (öneri):** Pin/kablo listesi ↔ BICD çapraz kontrolü; yorum kapanış takibi; yayın kontrol listesi (tüm yorumlar kapalı mı, baseline alındı mı, döküman no/rev atandı mı); "tüm itemlar yayınlandı" kapısını hesaplamak.
- **Kontrol noktası (öneri):** Her item için yorum kapanışı ve yayın onayı mühendiste; beş item'ın tamamı yayınlanmadan BVP yorum kapısı açılmaz.

Kurallar:

- **İncelenen ürünler:** Her item'ın kendi alt itemları; item'a göre farklılık gösterir. Alt itemlar geldiğinde netleşecek (bkz. Hatırlatmalar).
- **Yayınlanma tanımı:** Hem konfigürasyon kaydı (baseline) hem döküman numarası + revizyon.
- **Sıralama kuralı:** Tüm test itemlar yayınlanmadan BVP yoruma çıkmaz. Kök seviyede Aşama 5 → Aşama 8 (BVP ve TISVP yorum döngüsü) "bloklar" bağlantısı.

Aşama 5'in içindeki kutular ve akış:

- **Item yorum turu (item başına)** → "besler" (yorumlar) → **Yorumların işlenmesi ve kapatılması**.
- **Yorum kanalı: Crucible / JIRA + Excel** (dökümanlarla aynı kanal).
- Kapanıştan sonra **Konfigürasyon kaydı (baseline)** ve **Döküman numarası + revizyon**; ikisi birlikte **Yayınlanmış test item seti** çıktısını "besler".

## Aşama 6 — BVP yazımı

BVP araçta (DOORS / Polarion / Jira sınıfı; hangisi olduğu belirtilmedi) yazılır. Bir test case birden çok gereksinimi kapsayabilir. BVR, BVP'nin sonuç alanları doldurulmuş halidir (kök seviyede Aşama 6 → Aşama 13 "besler").

- **Girdiler:** Aşama 3: tahsis tablosu, izlenebilirlik matrisi, BVP bölüm iskeleti · Aşama 5: yayınlanmış test item seti · BRS (gereksinimler, toleranslar) · önceki BVP'ler
- **Çıktılar:** BVP taslağı (araçta) · coverage analiz tablosu · test case seti (MoC4/MoC1/MoC7) · ölçüm tabloları (BVR'de doldurulacak) · izlenebilirlik matrisi eki
- **Yapay zekanın rolü (öneri):** Aşama 3 tahsis tablosundan test case taslakları üretmek (amaç, özet, pass/fail kriteri, adımlar, ölçüm tablosu); birden çok gereksinimi kapsayan test case'leri gruplamak; toleransların kaynağını (BRS / mühendislik yaklaşımı) işaretlemek; önceki BVP'lerden benzer test case'leri önermek.
- **Kodun rolü (öneri):** Coverage analiz tablosunu ve izlenebilirlik matrisini deterministik üretmek; test feature → TISVP ve tolerans → test case linklerini kurmak; araca aktarım / şablona dökme; kapsanmayan gereksinim uyarısı.
- **Kontrol noktası (öneri):** Her test case mühendis onayı; coverage tablosunda kapsanmayan MoC4 gereksinimi varsa BVP yoruma çıkmaz.

### BVP resmi bölüm yapısı

1. **Introduction**
   - 1.1 Document Identification
   - 1.2 Purpose
   - 1.3 Scope
   - 1.4 Abbreviations
   - 1.5 Glossary
   - 1.6 Applicable Documents and Test Items
   - 1.7 Reference Documents
2. **BUT Identification**
   - 2.1 Functional Description
   - 2.2 Physical Characteristics
   - 2.3 Connector Layout
3. **Verification Activities Summary** — doğrulama faaliyetlerinin tablosuz özeti: her bölümün adı, hangi test feature'ı ve hangi test setup'ı kullandığı.
4. **Coverage Analysis** — MoC tipi başına kaç gereksinim var, hangi testte hangisi kaç tane. BVR'de pass/fail sayıları, oranları ve coverage oranları doldurulur. *(Teyit: izlenebilirlik matrisi (VCRM/RTM) bu bölümde mi, yoksa ayrı bir ek mi?)*
5. **Test Features** — kullanılan test feature'ları; bu bölümden TISVP'ye link gider.
6. **Verification Environment**
   - 6.1 Verification Environment Block Diagram
   - 6.2 Test Item Sets
   - 6.3 Preparation of Verification Environment
7. **Detailed Verification Instructions**
   - 7.1 Run Sequence
   - 7.2 Pre-Check
   - 7.3 Initialize
   - 7.4… x Test, y Test, … (if MoC4 applicable) — her MoC4 testi ayrı alt bölüm
   - 7.n-2 Design Review (if MoC1 applicable)
   - 7.n-1 Physical Inspections (if MoC7 applicable)
   - 7.n Post-Check
8. **Result Assessment** — BVP'de boş bırakılır, BVR'de doldurulur.
   - 8.1 Raw Test Result Data Location — Test Software raw test datası (Excel + PDF); SVN commit adresi ve numarası
   - 8.2 Test Cases Result Assessment — pass/fail; fail'ler için açılan CR linkleri
   - 8.3 Physical Inspection Result Assessment
   - 8.4 Design Review Result Assessment
   - 8.5 Uncovered Requirements and Cases Assessment
   - *(Not: kaynak listede 8.3 iki kez geçti; burada sıralı numaralandı.)*
9. **Appendix**
   - 9.1… Tolerances in x Test, y Test — ilgili test case'de tolerans değeri varsa açılır; tolerans BRS'den mi mühendislik yaklaşımıyla mı üretilmiş, ilgili test case'e link
   - 9.n-2 Configuration Check Form
   - 9.n-1 Calibration Form
   - 9.n Verification Procedure Attendance Form

### Test case formatı

Her test case (panoda 7. bölümün içinde): **Amaç** → **Nasıl yapıldığının özeti** → **Pass/Fail kriteri** → **Adım adım prosedür** (çok detaylı, her adım) → **Ölçüm tablosu** (ölçülecek sinyaller ve beklenen değerler; BVR'de ölçümler işlenir). Format, 7.4… MoC4 test alt bölümlerini "besler".

## Aşama 7 — TISVP yazımı

TISVP, BVP'nin sabitlediği test item setinin kendi doğrulamasıdır. Resmi 5 ana bölüm: Introduction, Test Item Set Identification, Self-Verification Activities, Detailed Self-Verification Instructions, Appendix.

- **Girdiler:** Aşama 4/5: yayınlanmış test item seti ve kabiliyetleri · BVP'nin Test Features bölümünden gelen link · item tasarım ürünleri (pin/kablo listeleri, fonksiyon listeleri)
- **Çıktılar:** TISVP taslağı: item set tanımı, inspection ve review talimatları, ATE ve GUI self-verification testleri, tolerans ve form ekleri
- **Yapay zekanın rolü (öneri):** Item kabiliyet tablosundan inspection/review adımlarını ve ATE/GUI self-verification testlerini taslak üretmek; toleransların kaynağını işaretlemek.
- **Kodun rolü (öneri):** ITA/breakout pin ve kablo listesinden süreklilik/izolasyon kontrol adımlarını deterministik üretmek; item seti ↔ BVP Test Features çapraz kontrolü; her item için en az bir doğrulama adımı var mı kontrolü.
- **Kontrol noktası (öneri):** Doğrulama adımları mühendis onayı; item setindeki her item kapsanmadan TISVP yoruma çıkmaz.

TISVP bölümleri (sırayla; panoda Aşama 7'nin içindeki kutular):

1. **Introduction** — 1.1 Document Identification · 1.2 Purpose · 1.3 Scope · 1.4 Abbreviations · 1.5 Glossary · 1.6 Applicable Documents and Test Items · 1.7 Reference Documents · **1.8 Safety** (BVP'de yok, TISVP'ye özel)
2. **Test Item Set Identification** — 2.1 {BUT} Board Verification Test Item Set (başlıktaki {BUT} kart adıyla değişir)
3. **Self-Verification Activities**
4. **Detailed Self-Verification Instructions**
   - 4.1 Inspection — 4.1.1 ATE inspection · 4.1.2 ITA inspection · 4.1.3 Breakout Board inspection
   - 4.2 Review — 4.2.1 Test Software Review
   - 4.3 Self Verification Tests for the ATE and GUI in the Test Item Set
5. **Appendix** — 5.1… Tolerances in Feature x / y Test (ilgili feature testinde tolerans varsa) · 5.n-2 Configuration Check Form · 5.n-1 Calibration Form · 5.n Verification Procedure Attendance Form (üç form da TISVP'de yalnızca başlık; TISVR'de doldurulur)

BVP'den farklar: 1.8 Safety yalnızca TISVP'de · TISVP'de Coverage Analysis ve Result Assessment ana bölümü yok; sonuçlar TISVR'de · Appendix formları TISVP'de yalnızca başlık.

Kök seviyede Aşama 7 → Aşama 11 (TISVR) "besler" bağlantısı: sonuçlar ve formlar TISVR'de doldurulur.

Açık teyitler: (a) 4.1/4.2'de ATE, ITA, Breakout ve Test Software var; **Test PLD** için inspection/review alt bölümü yok — Test PLD nasıl doğrulanıyor? (b) TISVP'de sonuç değerlendirme bölümü hiç yok mu; TISVR ayrı bir şablon mu, yoksa TISVP'ye sonuç bölümü mü ekleniyor?

## Aşama 8 — BVP ve TISVP yorum döngüsü (yorumların işlenmesi)

## Aşama 9 — Konfigürasyon kaydı ve yayın (baseline)

## Aşama 10 — TISVP koşumu

## Aşama 11 — TISVR yazımı ve yayını

## Aşama 12 — BVP koşumu

## Aşama 13 — BVR yazımı, yorumu ve yayını

---

Aşamalara yayılan ortak konular (veri modeli, izlenebilirlik, yapay zeka katmanı, belge üretimi, konfigürasyon yönetimi) aşama detayları netleştikten sonra ayrıca planlanacaktır.

## Hatırlatmalar — ileride detaylandırılacak

- **Checklist iyileştirme sekansı** (Aşama 2 › Kontrol listesi ile inceleme): Kullanıcı önceki dönemlerde yapılmış ve kabul edilmiş yorumları ve karşılıklarını verecek. Sistem her yorum için checklist'te karşılığı var mı / olmalı mı diye değerlendirecek; ekleme, çıkarma ve değişiklik talebi açacak. Kullanıcı onayladıktan sonra değişiklikler checklist'lere işlenecek. Sekans otomatik yürüyecek. **Ne zaman:** Aşama 8 (yorum döngüsü) detaylandırılırken ya da kullanıcı istediğinde gündeme getirilecek; detaylı planlanacak.
- **Test item alt itemları** (Aşama 4): Kullanıcı her test item (ATE, ITA, Breakout Board, Test Software, Test PLD) için kendine has alt itemları detaylı verecek. Geldiğinde ilgili kutuların içine alt kutu olarak işlenecek.
