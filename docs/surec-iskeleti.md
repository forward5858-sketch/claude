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

Panonun sayfa kaynağı `tools/plan-panosu.html` altındadır; aynı dosya Artifact'a yayınlanınca yukarıdaki bağlantı güncellenir. Veri (kutular ve bağlantılar) panonun kendi veritabanında tutulur, sayfa kaynağında değil — sayfa yeniden yayınlansa da veri korunur.

## Süreç grupları

12 aşama panoda dört üst grup altında toplanmıştır (kökte bu dört kutu görünür; aşamalar grupların içindedir):

| Grup | Aşamalar |
|---|---|
| **Tasarım Dökümanlarının Analizi** | 1 — Tasarım dosyalarının okunması · 2 — Döküman incelemesi · 3 — Arayüz ve MoC analizi |
| **Test Item'larının Hazırlanması** | 4 — Test item ihtiyaçları ve tanımlanması · 5 — Test item'ların yoruma çıkması ve yayınlanması |
| **Procedure'lerin Hazırlanması** | 6 — BVP yazımı · 7 — TISVP yazımı · 8 — Yorum döngüsü, konfigürasyon kaydı ve yayın |
| **Koşulması ve Raporlanması** | 9 — TISVP koşumu · 10 — TISVR · 11 — BVP koşumu · 12 — BVR |

Kökte gruplar arası bağlantılar: Tasarım Analizi → Test Itemları → Procedure Hazırlama → Koşum ve Raporlama ("sonra gelir"), ayrıca Tasarım Analizi → Procedure Hazırlama ("besler": BVP bölüm iskeleti + izlenebilirlik matrisi).

Pano yalnızca aynı tuvaldeki kutular arasında çizgi çizebildiği için, gruplar arası kalan ilişkiler ilgili aşama kutusunun **notlar** alanında yazılıdır:

- Aşama 2 → Aşama 4 (besler): ön çalışma çıktısı — arayüz okuma, test item ihtiyacı, cihaz siparişi.
- Aşama 3 → Aşama 4 (sonra gelir).
- Aşama 3 → Aşama 6 (besler): BVP bölüm iskeleti + izlenebilirlik matrisi.
- Aşama 4 → Aşama 7 (besler): test item seti ve kabiliyetleri.
- Aşama 5 → Aşama 6 (sonra gelir).
- Aşama 5 → Aşama 8 (bloklar): tüm itemlar yayınlanmadan BVP yoruma çıkmaz.
- Aşama 6 → Aşama 12 (besler): BVP'nin sonuç bölümleri BVR'de doldurulur.
- Aşama 7 → Aşama 10 (besler): TISVP'nin sonuçları ve formları TISVR'de doldurulur.
- Aşama 8 → Aşama 9 (sonra gelir): yayınlanmış TISVP olmadan koşum başlamaz.
- Aşama 9 → Aşama 11 (sonra gelir): BVP koşumu TISVR'yi beklemez.
- Aşama 10 → Aşama 12 (bloklar): TISVR, BVR'den önce yayınlanır.
- Aşama 11 → Aşama 12 (besler): ham veri, ölçümler ve fail CR'ları BVR'de toplanır.

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

BVP araçta (DOORS / Polarion / Jira sınıfı; hangisi olduğu belirtilmedi) yazılır. Bir test case birden çok gereksinimi kapsayabilir. BVR, BVP'nin sonuç alanları doldurulmuş halidir (kök seviyede Aşama 6 → Aşama 12 "besler").

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

Kök seviyede Aşama 7 → Aşama 10 (TISVR) "besler" bağlantısı: sonuçlar ve formlar TISVR'de doldurulur.

Açık teyit: 4.1/4.2'de ATE, ITA, Breakout ve Test Software var; **Test PLD** için inspection/review alt bölümü yok — Test PLD nasıl doğrulanıyor?

Kapandı: TISVR ayrı bir şablon değil, TISVP'nin sonuç alanları doldurulmuş halidir (bkz. Aşama 10).

## Aşama 8 — BVP ve TISVP yorum döngüsü, konfigürasyon kaydı ve yayın

Önce BVP, sonra TISVP yoruma çıkar (iki ayrı tur; BVP kapanınca TISVP yoruma çıkar). Yorum sayfası süreç ekibi onayıyla açılır, min 3 iş günü yorum toplanır; yazar cevaplar, yorumcular Verified/Rejected'a çeker, çözülemeyen yorum üst yöneticiye taşınır. Tüm yorumlar kapanınca moderatör işlemleri; ardından konfigürasyon kaydı (rel baseline) alınıp döküman yayınlanır.

- **Girdiler:** BVP taslağı (Aşama 6) · TISVP taslağı (Aşama 7) · yorum sayfası (JIRA/Crucible) · inceleme kontrol listesi
- **Çıktılar:** Kapatılmış yorum listesi (Verified/Rejected) · revize edilmiş BVP ve TISVP · rel baseline kaydı · döküman numarası + revizyon · yayın duyurusu
- **Yapay zekanın rolü (öneri):** Yoruma çıkmadan önce ön-review bulguları üretmek; gelen yorumları triyaj etmek (tip, şiddet, hedef bölüm); yazar cevabı taslağı; kabul edilen yorumun dökümana doğru işlenip işlenmediğini karşılaştırmak.
- **Kodun rolü (öneri):** Yorum durumlarının takibi (Open/Answered/Verified/Rejected), min 3 iş günü süre kontrolü, kapanmayan yorum listesi, katılımcı listesinin role göre kontrolü, kapanış kontrol listesi; baseline manifestosunu derlemek ve eksik alan varsa yayını durdurmak.
- **Kontrol noktası (öneri):** Süreç ekibi onayı olmadan yorum süreci başlamaz; tüm yorumlar kapanmadan moderatör kapanışı ve rel baseline yapılamaz; baseline manifestosu eksikse yayın duyurusu çıkmaz.

Katılımcılar:

| Rol | BVP | TISVP |
|---|---|---|
| Doğrulama ekibi (peer) | ✓ | ✓ |
| Tasarım ekibi | ✓ | — |
| HPAR (süreç sorumlusu) | ✓ | ✓ |
| HCMP (konfigürasyon sorumlusu) | ✓ | ✓ |
| Safety | ✓ | — |
| Kalite | ✓ | — |
| Sistem | ✓ | — |

Yorum durumları: Open → yazar cevabı (kabul / red) → Verified (kabul edilen, doğru işlenmiş) veya Rejected (red sebebi kabul edilmiş) → Closed. Uzlaşılmayan yorum açık kalır.

Yorum turu adımları (panoda Aşama 8'in içindeki kutular, sırayla bağlı):

1. **Yorum sayfasının süreç ekibi kontrolü** — yorum sayfası (JIRA / Crucible) önce süreç ekibince kontrol edilir.
2. **Onay ve yorum toplama** — onay gelince süreç başlar; en az 3 iş günü yorum toplanır.
3. **Yazarın yorumları cevaplaması** — her yorum kabul edilir ya da gerekçesiyle reddedilir.
4. **Yorumcu kontrolü ve Verified** — kabul edilen yorumlar gerçekten ve doğru işlenmiş mi kontrol edilip Verified'a çekilir.
5. **Red edilen yorumların değerlendirilmesi** — red sebebi kabul edilirse yorum Rejected işaretlenip kapatılır; kabul edilmezse cevap yazılır, yorum açık kalır.
6. **Yazarın kapanmayan yorumları tekrar ele alması** — kabul/red süreci yeniden işler (3. adıma "geri besleme verir").
7. **Çözülemeyen yorumun üst yöneticiye taşınması** — orada çözümlenir.
8. **Moderatör işlemleri** — kontroller; yorum sürecinde yapılan hataların düzeltilmesi. Buradan sonrası aşağıdaki konfigürasyon ve yayın bloğudur.

Açık teyit: Moderatör kim — HPAR mı, ayrı bir rol mü?

### Konfigürasyon kaydı ve yayın

Yorum turu kapandıktan sonra işleyen blok (panoda Aşama 8'in içinde ayrı bir kapsayıcı kutu). Sıralama yorum turlarıyla aynı: **önce BVP, sonra TISVP**.

**Baseline kapsamı — ne donduruluyor.** Rel baseline dört kümeyi birden kaydeder:

| Küme | İçerik |
|---|---|
| Döküman | BVP / TISVP içeriği, ekleri, izlenebilirlik matrisi |
| Test item seti sürümleri | ATE · ITA · Breakout Board · Test Software · Test PLD |
| Tasarım dökümanı revizyonları | BICD · BRS · BCDD · BDDD |
| Araç ve ortam sürümleri | Döküman aracı, test yazılımı sürümü, PLD bit dosyası |

Sonradan tasarım değişirse etki analizi bu kayda göre yapılır.

**Yayınlanma tanımı:** Hem konfigürasyon kaydı (rel baseline) hem döküman numarası + revizyon — test itemların yayın tanımıyla (Aşama 5) aynı.

Bloğun adımları:

1. **Yazarın rel Baseline alması** — yazar baseline'ı alır ve aldığını yorum sayfasına yazar.
2. **Moderatörün yorum sayfasını kapatması** — baseline kaydı sayfaya işlendikten sonra.
3. **Yayın duyuru maili (HCMP)** — konfigürasyon sorumlusu döküman numarası ve revizyonuyla duyuruyu atar; ilgili itemlar yayınlanmış olur.

**Yayın sonrası değişiklik — CR süreci.** Yayınlanmış bir BVP/TISVP'nin değişmesi gerekirse (tasarım revizyonu, bulunan hata, koşumdan gelen geri besleme) değişiklik talebi (CR) açılır. CR onaylanınca döküman yeni revizyonla güncellenir, yeni baseline alınır ve yeniden yayınlanır — panoda CR kutusundan rel baseline adımına "geri besleme" bağlantısı.

- **Yapay zekanın rolü (öneri):** Baseline manifestosunu taslak halinde çıkarmak; döküman içindeki atıflarla (item sürümleri, tasarım revizyonları) manifesto arasındaki uyuşmazlıkları bulmak; CR geldiğinde etkilenen bölüm ve test case'leri işaretlemek.
- **Kodun rolü (öneri):** Baseline manifestosunu deterministik derlemek ve dondurmak; yayın kontrol listesini hesaplamak (tüm yorumlar kapalı mı, baseline alındı mı, döküman no/rev atandı mı, duyuru çıktı mı); revizyon geçmişini ve CR → revizyon izini tutmak.
- **Kontrol noktası (öneri):** Baseline'ı yazar alır, sayfayı moderatör kapatır, duyuruyu HCMP çıkarır; üçü tamamlanmadan döküman yayınlanmış sayılmaz.

Kök seviyede Aşama 8 → Aşama 9 (TISVP koşumu) "sonra gelir": yayınlanmış prosedür olmadan koşum başlamaz.

Açık teyitler: (a) CR'ı kim açar/onaylar (HPAR mı, konfigürasyon kurulu mu) ve onaylı CR yeni bir yorum turu gerektiriyor mu? (b) Aşama 10'daki TISVR yayınında HCMP kaydı **CSAR**'a işliyor — aynı adım BVP/TISVP yayınında da var mı?

## Aşama 9 — TISVP koşumu

Yayınlanmış TISVP, yayınlanmış test item seti üzerinde koşulur: kartı doğrulamadan önce doğrulama takımının kendisi doğrulanır. Kayıt iki kanaldan yürür — Test Software'in ürettiği otomatik Excel logu ve elle yazım. Çıktısı Aşama 10'un (TISVR) ham verisidir.

- **Girdiler:** Yayınlanmış TISVP (Aşama 8) · yayınlanmış test item seti ve baseline'daki sürümleri (ATE, ITA, Breakout Board, Test Software, Test PLD) · kalibrasyon kayıtları · TISVP ekindeki üç form (Configuration Check, Calibration, Verification Procedure Attendance)
- **Çıktılar:** Test Software'in ürettiği otomatik Excel logu · elle doldurulmuş ve imzalanmış adım kayıtları · doldurulmuş üç form · bulgu ve karar kayıtları · TISVR'in ham verisi
- **Yapay zekanın rolü (öneri):** Otomatik Excel logunu TISVP adımlarıyla eşleştirip atlanan/eksik adımı bulmak; ölçüm değerlerini tolerans tablosuyla karşılaştırıp pass/fail önerisi üretmek; fail bulgusunu sınıflandırmak (item hatası / prosedür hatası / kabul edilebilir sapma) ve gerekçe taslağı yazmak; koşum biter bitmez TISVR taslağını doldurmak.
- **Kodun rolü (öneri):** Excel logunu ayrıştırıp adım-sonuç tablosuna çevirmek; tolerans kontrolünü deterministik yapmak; konfigürasyon kontrol formunu Aşama 8'deki baseline manifestosuyla karşılaştırmak (koşulan item sürümleri baseline'dakilerle aynı mı); kalibrasyon geçerlilik tarihi kontrolü; katılımcı listesinin role göre kontrolü; kapanmamış bulgu listesi.
- **Kontrol noktası (öneri):** Konfigürasyon kontrolü ve kalibrasyon geçerliliği doğrulanmadan koşum başlamaz; her adımın sonucu kayıtlı olmadan TISVR yazılmaz; fail bulgularının kararı kapanmadan TISVR yayına gitmez.

Katılımcılar:

| Rol | Katılım |
|---|---|
| Doğrulama ekibi | Zorunlu |
| HPAR (süreç sorumlusu) | Zorunlu |
| HCMP (konfigürasyon sorumlusu) | Zorunlu |
| Kalite | Zorunlu |
| Sistem | Duruma göre |
| Proje sorumlusu | Katılabilir |
| SOI-3 denetimini yapan CV'ler | Katılabilir |

Katılım, TISVP ekindeki Verification Procedure Attendance Form'a işlenir.

**Kayıt biçimi.** İki kanal birlikte yürür ve TISVR ikisinin birleşiminden doğar:

| Kanal | Kapsam |
|---|---|
| Otomatik Excel logu | Test Software'in ürettiği çıktı; ATE ve GUI self-verification testleri (TISVP 4.3) |
| Elle yazım | Inspection ve review adımları (4.1, 4.2), ölçüm değerleri, imzalar |

**Fail durumunda karar.** Duruma göre üç yol:

1. **Item hatası** — item düzeltilir, etkilenen adımlar yeniden koşulur; kayıt her iki koşumu da içerir.
2. **Prosedür hatası** — CR açılır, TISVP revize edilip yeniden yayınlanır (Aşama 8); yeni revizyonla koşulur.
3. **Kabul edilebilir sapma** — gerekçesiyle kaydedilir ve TISVR'de belirtilir.

**Koşum sıklığı.** Bir kez koşulur; item seti değişirse (yeni revizyon / onaylı CR) ya da kalibrasyon süresi dolarsa tekrarlanır. (Bkz. Süreç geri bildirimleri.)

Koşum adımları (panoda Aşama 9'un içindeki kutular, sırayla bağlı):

1. **Koşum öncesi hazırlık ve konfigürasyon kontrolü** — item seti kurulur; koşulan item sürümleri baseline manifestosuyla karşılaştırılır, Configuration Check Form doldurulur.
2. **Kalibrasyon kontrolü** — ölçüm cihazlarının geçerliliği kontrol edilir, Calibration Form doldurulur; geçerliliği dolmuş cihazla koşum yapılmaz.
3. **Inspection adımları (TISVP 4.1)** — ATE, ITA ve Breakout Board inspection.
4. **Review adımları (TISVP 4.2)** — Test Software Review.
5. **ATE ve GUI self-verification testleri (TISVP 4.3)** — Test Software üzerinden koşulur, otomatik Excel logu üretilir.
6. **Bulguların değerlendirilmesi ve karar** — yukarıdaki üç yoldan biri seçilir; düzeltme sonrası ilgili adımlar 3'ten itibaren tekrar koşulur ("geri besleme verir").
7. **Kayıtların toplanması ve formların doldurulması** — iki kanalın kaydı birleştirilir, üç form tamamlanır; bu set TISVR'i besler.

Açık teyitler: (a) Fail kararını kim verir — doğrulama mühendisi mi, süreç ekibi mi, HPAR mı? (b) Kalibrasyon geçerlilik süresi ne kadar ve takibini kim yapıyor? (c) Aşama 7'den devreden soru koşuma da yansıyor: Test PLD'nin inspection/review alt bölümü olmadığı için koşumda da karşılığı yok.

## Aşama 10 — TISVR yazımı ve yayını

TISVR, TISVP'nin sonuç alanları doldurulmuş halidir — ayrı bir şablon değil (BVR ↔ BVP ilişkisinin aynısı). Aşama 9'un koşum kayıtları ve ekteki üç form rapora işlenir. Yorum turuna çıkmaz: yazar rel Baseline alır, HCMP'ye bildirir, HCMP CSAR'a işleyip yayın duyurusunu atar.

- **Girdiler:** Aşama 9 koşum kayıtları (otomatik Excel logu + elle tutulan adım kayıtları) · doldurulmuş üç form (Configuration Check, Calibration, Attendance) · bulgu ve karar kayıtları · yayınlanmış TISVP (şablon ve atıf)
- **Çıktılar:** TISVR — TISVP'nin doldurulmuş hali · rel baseline kaydı · CSAR kaydı · yayın duyuru maili
- **Yapay zekanın rolü (öneri):** Koşum kayıtlarından raporu doldurmak (adım sonuçları, ölçüm değerleri, formlar); kaydı olmayan ya da boş kalan adımı işaretlemek; fail ve sapma gerekçelerinin rapora doğru geçtiğini kontrol etmek.
- **Kodun rolü (öneri):** Excel logunu TISVP adım numaralarıyla eşleştirip rapor alanlarına deterministik yazmak; her adımın bir sonucu var mı kontrolü; üç formun eksiksizliği; baseline manifestosu ile TISVR'deki konfigürasyon bilgisinin karşılaştırılması; yayın kontrol listesi.
- **Kontrol noktası (öneri):** Kaydı olmayan adım varsa TISVR yayına gitmez; baseline alınmadan HCMP bildirimi yapılmaz; CSAR işlenmeden yayın duyurusu çıkmaz.

**Şablon.** TISVR ayrı bir döküman şablonu değildir; yayınlanmış TISVP'nin kopyası üzerinde şu alanlar doldurulur: adım sonuçları (pass/fail), ölçüm değerleri, Configuration Check Form, Calibration Form, Verification Procedure Attendance Form, bulgu ve sapma kayıtları. (Aşama 7'de açık kalan "TISVR ayrı şablon mu" sorusu burada kapandı.)

**Yorum turu yok.** TISVR yorum sayfasına açılmaz; yazılır ve doğrudan yayınlanır. Resmi yorum turu yalnızca BVP, TISVP ve BVR için işler.

Yayın akışı (panoda Aşama 10'un içindeki kutular, sırayla bağlı):

1. **TISVR yazımı** — koşum kayıtları TISVP kopyasına işlenir.
2. **Yazarın rel Baseline alması** — rapor tamamlanınca.
3. **HCMP'ye baseline ve yayın bildirimi** — yazar mail atar: ilgili TISVR için baseline alındı, yayınlanması gerekiyor.
4. **HCMP'nin CSAR'a işlemesi** — konfigürasyon sorumlusu kaydı CSAR'a geçer.
5. **Yayın duyuru maili (HCMP)** — TISVR yayınlanmış olur.

**Sıralama kuralı.** TISVR, BVP koşumunu bloklamaz: TISVP koşumu (Aşama 9) başarıyla bittiyse BVP koşumu (Aşama 11) başlayabilir, TISVR yazımı paralel yürür. Ancak TISVR, BVR'den önce yayınlanır — kök seviyede Aşama 10 → Aşama 12 "bloklar" bağlantısı.

Açık teyitler: (a) CSAR'ın açılımı ve kapsamı nedir? (b) Aynı CSAR adımı Aşama 8'deki BVP/TISVP yayınında da işliyor mu?

## Aşama 11 — BVP koşumu

Yayınlanmış BVP, tek bir BUT üzerinde laboratuvarda koşulur. Bu aşama BVP'nin 7. bölümünü yürütür: Run Sequence → Pre-Check → Initialize → MoC4 test case'leri → Post-Check. Ham veri Excel + PDF olarak üretilip SVN'e commit edilir; fail olan test case'ler için CR açılır. Çıktısı Aşama 12'nin (BVR) ham verisidir.

- **Girdiler:** Yayınlanmış BVP (Aşama 8) · TISVP ile doğrulanmış test item seti · BUT (tek kart: seri numarası, donanım revizyonu, üzerindeki yazılım/PLD sürümleri) · kalibrasyon kayıtları · BVP §9 formları (Configuration Check, Calibration, Attendance)
- **Çıktılar:** Ham test verisi (Excel + PDF) ve SVN commit adresi/numarası · adım ve ölçüm kayıtları · doldurulmuş üç form · fail'ler için açılan CR'lar · BVR'nin ham verisi
- **Yapay zekanın rolü (öneri):** Ölçüm değerlerini BVP'nin ölçüm tablosu ve tolerans ekiyle karşılaştırıp pass/fail önerisi üretmek; koşulmayan ya da atlanan test case'i bulmak; fail bulgusunu sınıflandırmak (kart tasarım hatası / prosedür hatası / test item hatası / kabul edilebilir sapma) ve CR taslağı yazmak; koşum biter bitmez BVR §8 taslağını doldurmak.
- **Kodun rolü (öneri):** Ham veriyi BVP test case ve adım numaralarıyla eşleştirmek; tolerans kontrolünü deterministik yapmak; SVN commit adresi ve numarasını kaydetmek; konfigürasyon kontrol formunu baseline manifestosu ve BUT seri no/revizyonuyla karşılaştırmak; kalibrasyon geçerlilik kontrolü; katılımcı listesi kontrolü; BVR §4 için pass/fail ve coverage sayılarını hesaplamak.
- **Kontrol noktası (öneri):** Pre-Check geçmeden test dizisi başlamaz; konfigürasyon ve kalibrasyon doğrulanmadan koşum başlamaz; her test case'in sonucu ve ham veri atfı olmadan BVR yazılmaz; fail için CR açılmadan test case kapanmaz.

Katılımcılar:

| Rol | Katılım |
|---|---|
| Doğrulama ekibi | Zorunlu |
| HPAR (süreç sorumlusu) | Zorunlu |
| HCMP (konfigürasyon sorumlusu) | Zorunlu |
| Kalite | Zorunlu |
| Sistem | Duruma göre |
| Tasarım ekibi | Katılabilir |
| Proje sorumlusu | Katılabilir |
| SOI-3 denetimini yapan CV'ler | Katılabilir |

SOI-3 CV katılımı TISVP koşumu (Aşama 9) için de geçerlidir.

**MoC kapsamı.** Bu aşamada yalnızca laboratuvardaki **MoC4** fonksiyonel testleri koşulur. MoC1 (design review), MoC2 (analiz/hesaplama) ve MoC7 (physical inspection) ayrı zamanlarda yürütülür; sonuçları BVR §8.3 (Physical Inspection Result Assessment) ve §8.4 (Design Review Result Assessment) bölümlerinde toplanır.

**BUT kaydı.** Tek kart koşulur. Kayıt altına alınanlar: kartın seri numarası, donanım revizyonu ve üzerindeki yazılım/PLD sürümleri; bu bilgi Configuration Check Form'a girer.

**Fail durumunda karar.** Duruma göre dört yol:

1. **Kart tasarım hatası** — tasarıma döner; yeni revizyon sonrası ilgili test case'ler tekrar koşulur.
2. **Prosedür hatası** — BVP için CR açılır; revizyon sonrası tekrar koşulur.
3. **Test item hatası** — item düzeltilir, TISVP koşumuna (Aşama 9) dönülür.
4. **Kabul edilebilir sapma** — gerekçesiyle kaydedilir.

Her fail, BVR §8.2'de açılan CR'ın linkiyle görünür.

Koşum adımları (panoda Aşama 11'in içindeki kutular, sırayla bağlı):

1. **Hazırlık ve konfigürasyon kontrolü** — doğrulama ortamı BVP §6.3'e göre kurulur; BUT kimliği ve item sürümleri baseline manifestosuyla karşılaştırılıp Configuration Check Form doldurulur.
2. **Kalibrasyon kontrolü** — Calibration Form doldurulur.
3. **Run Sequence ve Pre-Check (§7.1–7.2)** — Pre-Check geçmeden test dizisi başlamaz.
4. **Initialize (§7.3)**
5. **MoC4 test case'lerinin koşulması (§7.4…)** — adım adım prosedür, ölçüm tabloları, Test Software ham veriyi üretir.
6. **Post-Check (§7.n)**
7. **Ham verinin SVN'e commit edilmesi (§8.1)** — commit adresi ve numarası kaydedilir.
8. **Bulguların değerlendirilmesi ve CR açılması (§8.2)** — düzeltme sonrası ilgili test case'ler 5. adımdan itibaren tekrar koşulur ("geri besleme verir").
9. **Kayıtların toplanması ve formların doldurulması** — bu set BVR'yi besler.

Açık teyitler: (a) BVP §7'de "Design Review (if MoC1 applicable)" ve "Physical Inspections (if MoC7 applicable)" alt bölümleri prosedürün içinde duruyor; bu adımlar ne zaman ve kim tarafından yürütülüyor? (b) MoC2 analiz sonuçları rapora nasıl giriyor? (c) Fail sınıflandırma kararını kim veriyor?

## Aşama 12 — BVR yazımı, yorumu ve yayını

BVR, BVP'nin sonuç alanları doldurulmuş halidir ve doğrulama kampanyasının kapanış belgesidir. Aşama 11'in koşum çıktıları §4 ve §8'e işlenir. Aşama 8'in yorum mekanizması dar katılımla bir kez daha işler; ardından Aşama 10'un yayın akışı yürür.

- **Girdiler:** Aşama 11 koşum çıktıları (ham veri + SVN commit adresi/numarası, ölçüm kayıtları, doldurulmuş üç form, fail CR'ları) · MoC1, MoC2 ve MoC7 aktivite sonuçları · yayınlanmış BVP (şablon) · yayınlanmış TISVR
- **Çıktılar:** BVR — BVP'nin doldurulmuş hali · kapatılmış yorum listesi · rel baseline kaydı · CSAR kaydı · yayın duyuru maili
- **Yapay zekanın rolü (öneri):** Koşum kayıtlarından §4 Coverage Analysis ve §8 Result Assessment bölümlerini doldurmak; §8.5 için kapsanmayan gereksinimlerin gerekçe taslağını yazmak; gelen yorumları triyaj edip yazar cevabı taslağı üretmek.
- **Kodun rolü (öneri):** §4 pass/fail ve coverage sayılarını izlenebilirlik matrisinden deterministik hesaplamak; her test case'in bir sonucu ve ham veri atfı var mı kontrolü; CR linklerinin geçerliliği; üç formun eksiksizliği; yayın kontrol listesi.
- **Kontrol noktası (öneri):** Sonucu ya da ham veri atfı olmayan test case varsa BVR yorum turuna çıkmaz; §8.5'te gerekçesiz kapsanmayan gereksinim kalamaz; tüm yorumlar kapanmadan baseline alınmaz.

**Şablon.** BVR ayrı bir şablon değildir; BVP kopyası üzerinde şu bölümler doldurulur:

| Bölüm | Doldurulan |
|---|---|
| §4 Coverage Analysis | Pass/fail sayıları, oranları ve coverage oranları |
| §8.1 Raw Test Result Data Location | Ham veri (Excel + PDF); SVN commit adresi ve numarası |
| §8.2 Test Cases Result Assessment | Test case başına pass/fail; fail'ler için açılan CR linkleri |
| §8.3 Physical Inspection Result Assessment | MoC7 sonuçları |
| §8.4 Design Review Result Assessment | MoC1 sonuçları |
| §8.5 Uncovered Requirements and Cases | Kapsanmayan/koşulamayan gereksinimler, gerekçeleriyle |
| §9 Appendix | Configuration Check, Calibration ve Attendance formları |

**Yorum turu.** Aşama 8'deki mekanizmanın aynısı işler (yorum sayfası, min 3 iş günü, yazar cevabı, Verified/Rejected, çözülemeyen yorumun üst yöneticiye taşınması, moderatör kapanışı) ama katılım dardır:

| Rol | BVP turu | BVR turu |
|---|---|---|
| Doğrulama ekibi (peer) | ✓ | ✓ |
| HPAR | ✓ | ✓ |
| HCMP | ✓ | ✓ |
| Kalite | ✓ | ✓ |
| Tasarım ekibi | ✓ | — |
| Safety | ✓ | — |
| Sistem | ✓ | — |

Moderatörün yorum sayfasını kapatması bu turun son adımıdır; yayın ondan sonra başlar.

**Kapsanmayan gereksinimler.** Kapsanamayan ya da koşulamayan gereksinim çıkarsa §8.5'te gerekçesiyle raporlanır; ayrı bir sapma/muafiyet kaydı gerekmez ve BVR bu haliyle yayınlanabilir.

**Açık CR'lar.** Aşama 11'de fail'ler için açılan CR'ların kapanması beklenmez; BVR fail'leri ve açık CR linklerini raporlar, CR'lar kendi süreçlerinde kapanır.

Yayın akışı (Aşama 10'un aynısı):

1. **BVR yazımı** — sonuç alanlarının doldurulması.
2. **Yorum turu** — dar katılım, moderatör kapanışına kadar.
3. **Yazarın rel Baseline alması**
4. **HCMP'ye baseline ve yayın bildirimi**
5. **HCMP'nin CSAR'a işlemesi**
6. **Yayın duyuru maili (HCMP)** — BVR yayınlanır, kampanya kapanır.

Açık teyit: BVR yorum turunda tasarım, safety ve sistem ekiplerinin bulunmaması bilinçli mi (BVP turunda katılıyorlardı)?

---

12 aşamanın tamamı detaylandırıldı. Sıradaki iş: aşamalara yayılan ortak konuların planlanması — veri modeli, izlenebilirlik, yapay zeka katmanı, belge üretimi ve konfigürasyon yönetimi. Ayrıca açık teyitlerin toplanıp cevaplanması ve Hatırlatmalar'daki maddelerin ele alınması.

## Süreç geri bildirimleri

Süreci uygularken fark edilen, mevcut uygulamanın dışında kalan iyileştirme fikirleri. Karar verildikçe ilgili aşamaya işlenir.

- **TISVP koşum sıklığı** (Aşama 9): Mevcut uygulama "bir kez koş, değişince tekrarla". Önerilen — TISVP'nin **her BVP kampanyası öncesi** koşulması; item setinin kampanya anında hâlâ geçerli olduğunu gösterirdi. Henüz karara bağlanmadı.

## Hatırlatmalar — ileride detaylandırılacak

- **Checklist iyileştirme sekansı** (Aşama 2 › Kontrol listesi ile inceleme): Kullanıcı önceki dönemlerde yapılmış ve kabul edilmiş yorumları ve karşılıklarını verecek. Sistem her yorum için checklist'te karşılığı var mı / olmalı mı diye değerlendirecek; ekleme, çıkarma ve değişiklik talebi açacak. Kullanıcı onayladıktan sonra değişiklikler checklist'lere işlenecek. Sekans otomatik yürüyecek. **Ne zaman:** Aşama 8 (yorum döngüsü) detaylandırılırken ya da kullanıcı istediğinde gündeme getirilecek; detaylı planlanacak.
- **Test item alt itemları** (Aşama 4): Kullanıcı her test item (ATE, ITA, Breakout Board, Test Software, Test PLD) için kendine has alt itemları detaylı verecek. Geldiğinde ilgili kutuların içine alt kutu olarak işlenecek.
- **Süreç Sorumlusu Agent**: Sistem tamamlandıktan sonra tüm süreci (12 aşama, kutular, tipli bağlantılar, kontrol noktaları, açık teyitler ve süreç geri bildirimleri) baştan sona gözden geçirip olası sıkıntıları ve iyileştirmeleri raporlayan bir ajan. Ne zaman çalışacağı, hangi girdileri okuyacağı ve raporun biçimi sistem bitince planlanacak.
