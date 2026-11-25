# Gelecek çalışma: Scriptoria transkriptleri

Tarih: 2026-11-25. **Şimdilik implementasyona dahil değil.** Transkript dosyaları `data/handwriting/fd_lex/transcripts/` altında saklanacak (klasör henüz boş; biçim ve adlandırma **bilinmiyor**).
Kullanım izni ve yerel-only kuralı transkriptler için de geçerli (öğrenci metni kişisel veri içerebilir). Yayında FD-LEX'in el yazısı taramalarının yanında **ortografik olarak normalize edilmiş transkriptler** sunduğu
yazıyor **[yayında]**; bu çalışmada dosyalar incelenmedi.

## 1. Potansiyel kullanım alanları

| Alan | Ne sağlar | Ne gerekir | Riskler / sınırlar |
|---|---|---|---|
| **Metin uzunluğuna göre özellik normalizasyonu** | Sayfa kullanımı özelliklerini (`used_frac`, `ink_mm2_per_used_line`, doluluk) gerçek karakter/kelime sayısına göre düzeltmek; şimdi yalnız Excel'deki `Textlänge` (kelime sayısı **[yayında]**) var | Transkripti sayfaya/yazıya eşlemek; kelime/karakter sayımı; Excel `Textlänge` ile tutarlılık denetimi | Normalize transkriptte yazım hataları düzeltilmiş olabilir: çocuğun yazdığı karakter sayısı ≠ transkript karakter sayısı |
| **Karakter / kelime segmentasyonu** | Bitişik yazıda bileşen ≠ harf sorununu çözmek: gerçek x-yüksekliği, harf başına boyut, kelime başına özellikler (kelime aralığı şu an kapsam dışı) | Satır düzeyinde görüntü–metin hizalama (zorunlu hizalama / CTC hizalama); segmentasyon doğrulaması (elle) | Hizalama hatası ölçümü bozar; ML bileşeni (HTR) gerektirir |
| **HTR model eğitimi** | Tanıma modeli; segmentasyon ve hizalama için araç (okunabilirlik skoru değil) | Satır kırpmaları + satır metinleri; öğrenci bazlı bölme (mevcut `splits.csv`); yüzlerce bin karakter ölçeği yeterli mi: **bilinmiyor** | Hedef, çocuk yazısı + normalize transkript: yazım hatalarının ve silinmelerin temsili yok; model başarımı "okunabilirlik" ile karıştırılmamalı (kapsam dışı) |
| **Görev/zaman eşlemesini sağlamlaştırma** | 28 belirsiz öğrencinin sayfa → (görev, zaman) eşlemesi transkript uzunluğu/içeriğiyle çözülebilir (Textlänge ile aynı fikir, daha güçlü sinyal) | Transkript kimlikleri + görev/zaman etiketi | Transkript yoksa ya da çok sayfalı yazılarda eşleme belirsiz |
| **Dilsel analiz** | Kelime sayısı, kelime dağarcığı, yazım hatası (transkripte bağlı) gibi içerik özellikleri | Normalize transkriptin ham halle ilişkisi | **Kapsam dışı** (el yazısı geometrisi projesi); ayrı bir "Yazı/Açıklama" modülü işi (plan aşama 4) |

## 2. Gerekli görüntü–transkript eşleştirmeleri

1. **Yazı düzeyi:** (öğrenci kodu, görev, ölçüm zamanı) → transkript dosyası/kaydı. Anahtar: Excel `Code` + `Ber/Arg` + `MZP1–3`. Transkriptlerin bu anahtarı nasıl taşıdığı **bilinmiyor** (dosya adı mı, içinde mi).
2. **Sayfa düzeyi:** bir yazı birden çok sayfada olabilir (190 sayfa/28 belirsiz öğrenci; ek sayfalar). Transkripti sayfalara bölmek için satır/kelime sayısı ve sayfa mürekkep miktarıyla hizalama (dinamik programlama, sıra korumalı) gerekir.
3. **Satır düzeyi:** basılı çizgi bantları (mevcut `segment.py`) ↔ transkript satırları. Transkriptlerde satır sonu bilgisi yoksa metin satırlara tahmini hizalama (kelime uzunluğu) ile bölünür; doğrulama için elle işaretli örnek şart.
4. **Kelime/karakter düzeyi (HTR için):** satır görüntüsü ↔ satır metni; hizalama ML ile (CTC/zorunlu hizalama) yapılır; elle doğrulanan alt küme gerekir.
5. **Anonimleştirme:** sayfa metin katmanındaki `XXX` (imza vb.) transkriptte nasıl temsil ediliyor? Hizalamada `XXX` ve başlık/kod kutusu metni çıkarılmalı.
6. **Normalizasyon farkı:** transkript ortografik olarak normalize **[yayında]**; çocuğun gerçek yazımı ile arasındaki farklar hizalamada hata kaynağıdır (hata modeli: yazım düzeltmeleri, silinen kelimeler transkriptte yok).

## 3. Transkriptler eklendiğinde yapılacaklar (kontrol listesi, uygulama değil)
1. Envanter: dosya sayısı/biçimi, adlandırma, kodlama, anahtar alanları; Excel kodlarıyla eşleşme oranı (938 öğrenci x 6 yazı = 5628 beklenir).
2. Tutarlılık: transkript kelime sayısı ↔ Excel `Textlänge`; çok sayfalı ve belirsiz öğrencilerde eşleme.
3. Gizlilik: transkriptlerde isim/yer var mı; yerel-only ve commit denetimi (`tools/check_no_student_data.py` kapsamına transkript dosya türleri eklenmeli).
4. Bölme: mevcut `splits.csv` (öğrenci bazlı) aynen kullanılır; transkript tabanlı herhangi bir eğitim yalnız train'de.
5. Önce en küçük değer katan iş: Excel `Textlänge` yerine transkript sayımı ile uzunluk normalizasyonu ve belirsiz öğrencilerin çözümü; HTR/segmentasyon ancak elle doğrulama planı ve ayrı plan (`docs/plan_<konu>.md`) onaylanınca.

## 4. Açık sorular
- Transkript biçimi ve anahtarları? Satır sonu bilgisi var mı? Normalizasyonun kapsamı (yalnız yazım mı, noktalama/büyük harf mi)?
- Yayın koşullarında transkriptler için ayrı bir kullanım izni var mı?
- HTR için yeterli satır sayısı ve çocuk yazısı çeşitliliği; ölçüm için gerekli doğruluk düzeyi.
