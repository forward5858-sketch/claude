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

## Aşama 4 — Test item ihtiyaçlarının belirlenmesi ve tanımlanması

ATE, ITA, Breakout Board, Test Software, Test PLD.

## Aşama 5 — Test item'ların yoruma çıkması ve yayınlanması

## Aşama 6 — BVP yazımı

## Aşama 7 — TISVP yazımı

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
