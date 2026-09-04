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
