# Plan Panosu — Arayüz Kuralları ve Düzeltme Kaydı

Canlı plan panosu (https://claude.ai/code/artifact/08b51fed-febf-4855-b04f-6601fc341962) düzenleme yüzeyidir; bu dosya panonun kart arayüzü için kalıcı kuralları ve yapılan düzeltmelerin kaydını tutar. Panoya yapılan her değişiklik bu kurallara uyar; yayınlamadan önce alttaki kontrol listesi uygulanır.

## Kalıcı kurallar

1. **Kart genişliği sabittir (220px, `NODE_W`); içerik kartı asla genişletemez.** Kartın tek grid sütunu `minmax(0, 1fr)` ile tanımlanır ve her satır `min-width: 0` alır. Böylece sığmayan bir satır sütunu büyütemez; ya sarar ya kısalır.
2. **Sığmayan satır ya sarar ya da üç nokta ile kısalır; hiçbir öğe kart sınırının dışına çıkmaz.** Alt satır (`.node-foot`) `flex-wrap: wrap`; alt kutu sayısı ve ↘ düğmesi tek grup (`.node-go`) olarak birlikte ikinci satıra iner ve sağa yaslanır. Başlık ve özet `overflow-wrap: anywhere` ile kırılmaz kelimeleri de sarar.
3. **Metin sabit bir "ch" sınırıyla kırpılmaz.** Grup etiketi (`.tag`) `flex: 0 1 auto; min-width: 0` ile yalnızca satır gerçekten dar kaldığında üç nokta alır; "Koşum ve rapor" gibi uzun etiketler tam görünür.
4. **Sol durum şeridi `--stripe` değişkeninden boyanır.** Hover, seçili ve bağlama durumları `border-color` yazarken `border-left-color: var(--stripe)` ile şeridi korur; durum rengi hiçbir etkileşimde kaybolmaz.
5. **Bağlantı çizgileri kart yüksekliklerine bağlıdır; yükseklikler fontlar yüklendiğinde yeniden ölçülür.** `document.fonts.ready` ve `loadingdone` sonrasında kartlar yeniden ölçülür ve çizgiler yeniden çizilir; ok uçları kart kenarına oturur.
6. **SVG renkleri token'lardan gelir.** Ok uçları ve lejant renkleri CSS sınıfları ve `currentColor` ile verilir; `fill="var(--x)"` gibi sunum öznitelikleri kullanılmaz.
7. **Sürükleme, veri güncellemesinden kopmaz.** Sürükleme sırasında gelen bir veri güncellemesi kartları yeniden çizerse sürükleme canlı elemana yeniden bağlanır.

## Yayın öncesi kontrol listesi

- En uzun durum ("Detaylandırılıyor" ya da "Revize gerekiyor"), iki basamaklı alt kutu sayısı ve en uzun grup etiketi ("Koşum ve rapor") olan bir kart koyu temada %250 yakınlaştırmada incelenir.
- Kartın dışına taşan öğe, kırpılan etiket, hover ya da seçimde kaybolan durum şeridi olmamalı.
- Bağlantı ok uçları kart kenarına oturmalı; lejant ve ok uçları her iki temada görünür olmalı.

## Düzeltme kaydı

### 2026-09-04 — Kart içeriği kart sınırını aşıyordu

- **Belirti:** Kutu 01'de "HAZIRLIK" etiketi ve ↘ düğmesi kartın sağ kenarının dışına taşıyor, başlık kenara yapışıyordu.
- **Kök neden:** Alt satırdaki üç öğe (durum rozeti, "5 alt kutu", ↘ düğmesi) `white-space: nowrap` ile küçülemiyordu. Toplam genişlikleri (yaklaşık 215px) kartın iç genişliğini (195px) aşınca kartın örtük grid sütunu içerik kadar genişledi ve etiket, başlık ve alt satır birlikte sağa taştı. Yalnızca uzun durum etiketi ve alt kutusu olan kartlarda ortaya çıktığı için ilk yükte fark edilmedi.
- **Aynı incelemede bulunan diğer hatalar:** `.tag` üzerindeki `max-width: 12ch` "Koşum ve rapor" (4 kart) ve "Test itemlar" (2 kart) etiketlerini kırpıyordu. `.node:hover` ve `.node.selected` kurallarındaki `border-color` kısayolu sol durum şeridini griye ya da turuncuya boyuyordu. Kart yükseklikleri fontlar yüklenmeden ölçüldüğünde bağlantı uçları kart kenarından kayabiliyordu. Sürükleme sırasında gelen veri güncellemesi sürüklemeyi koparıyordu.
- **Düzeltme:** Yukarıdaki 1–7 numaralı kurallar panoya uygulandı ve kart CSS'inin başına yorum olarak yazıldı.
- **Hata olmayan:** Ekran görüntüsündeki beyaz çapraz çizgi 01→02 "Sonra gelir" bağlantısıdır; Kutu 01 (-8, -272) konumuna taşındığı için çizgi alt kenardan çapraz çıkar.
