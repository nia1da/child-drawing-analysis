# Kararlar

Verilmiş kararlar, tarih sırasıyla. Kullanıcıya sormadan değiştirilmez; değişen karar silinmez, yeni satırla
"önceki kararın yerine" diye eklenir. Tarih kaydı olmayan ilkeler "ilke" olarak başta; kayda geçtikleri tarih
2026-10-21.

## İlkeler

| Karar | Neden |
|---|---|
| Sistem tanı koymaz, risk skoru üretmez (modüller arası birleşik skor da yok); rapor betimleyicidir, yorum uzmana kalır. | Karar destek sistemi; klinik yargının yerine geçmemeli, tanı dili yanlış güven yaratır. |
| Cinsiyet tahmini kapsam dışı. | Klinik değeri yok, etik açıdan sorunlu. |
| Önce ince dilim, sonra modüller. | Her aşamanın sonunda çalışan bir sistem olsun. |
| Ölçümler klasik görüntü işlemeyle (makine öğrenmesi yok). | Yorumlanabilir; klinisyen kâğıt üzerinde kontrol edebilir. |
| Gerçek klinik çocuk verisi repoya girmez; veri ve modeller git'e girmez. | Gizlilik; veri Drive'da kalır. |
| Bölme öğrenci ve okul bazında; test seti son değerlendirmeye kadar kullanılmaz, seçimler val ile yapılır. | Aynı öğrencinin / okulun çizimleri bağımlı; test sonucu iyimser olmasın. **Durum:** öğrenci bazında uygulandı; okul bazında bölme yapılmadı (`docs/durum.md`, açık sorular). |

## Tarihli kararlar

| Tarih | Karar | Neden |
|---|---|---|
| 2026-10-15 | Test seti KIDO'nun resmi `test` klasörü; val train'den öğrenci bazında %15, eğitim seviyesi + cinsiyete göre stratifiye, seed 42. | Resmi test makaleyle kıyas sağlar; öğrenci bazında bölme sızıntıyı önler. |
| 2026-10-15 | Metrik macro F1; hedef makaledeki görüntü modeli (≈ %79 F1). | Sınıflar dengeli, makaleyle aynı ölçüt. |
| 2026-10-15 | Çözünürlük en az 320px. | 320px, 224px'ten ≈ 3 puan iyi. |
| 2026-10-15 | 1 puanın altındaki farklar tek seed'le yorumlanmaz, 2–3 seed ile tekrarlanır. | Seed'ler arası yayılım ≈ 0,5 puan. |
| 2026-10-18 | Gruba özel (cinsiyete göre) eşik kullanılmaz. | Model girdisi olarak cinsiyet gerektirir; etik açıdan sorunlu. |
| 2026-10-19 | Yerel eğitim 16 x 2 gradyan biriktirmeyle. | RTX 4060'ta 448px batch 32 sığmıyor; ConvNeXt LayerNorm kullandığı için 32 x 1'e eşdeğer (BatchNorm'lu modellerde değil). Yerel tekrar 0,8022 verdi; aynı seed'li Colab çalıştırmasının aynı epoch'u 0,8036, aynı aralıkta. |
| 2026-10-19 | Yerel ve Colab aynı anda eğitim yapmaz. | İkisi de Drive'daki aynı `deneyler.csv`'ye yazar, çakışma kopyası oluşur. |
| 2026-10-19 | Kayıtlı dosyalardaki adlar Türkçe kalır; kod adları İngilizce. | Eski kayıtlar (deneyler.csv, tahminler, metadata) bu adlara bağlı. |
| 2026-10-19 | Duygu sınıflandırıcısı "görev uyumu" olarak yeniden tanımlandı; çocuğun ruh hali olarak yorumlanmaz. | Model çizimin hangi göreve çizilmiş çizimlere benzediğini öğrenir, çocuğun duygusunu değil. |
| 2026-10-19 | Sınıflandırıcı donduruldu. Referans: `convnext_tiny_320px_lr0.0001_ls0.1_s42.pt`, val F1 **0,8095** (12 epoch, en iyi epoch 11). | Daha fazla iyileştirme raporu anlamlı biçimde değiştirmez. Not: `deneyler.csv`'deki 0,811'lik 8 epoch'luk satırın ağırlıkları yok (üzerine yazıldı); referans 0,8095'lik dosya. |
| 2026-10-19 | Ölçüm normları sadece train'den, sınıf düzeyi (1–8, dosya adından) x görev bazında. | Val ve test norma girmez; sınıf düzeyi gelişimsel karşılaştırma için. |
| 2026-10-19 | Maske 24 çizimlik kontrol sayfasıyla onaylandı. Bütün çizimleri aynı yönde etkileyen maske hataları kabul; bazılarını etkileyenler kalite bayrağıyla görünür. | Normlar aynı maskeyle hesaplanır; sistematik hata karşılaştırmayı bozmaz. |
| 2026-10-19 | Soluk renk kalite bayrağı (train'de ≈ %8). | Maskenin kaçırdığı soluk renkler bazı çizimleri etkiliyor, raporda görünmeli. |
| 2026-10-19 | ⚠ kuralı kuyruk payıyla (`tail_shares`): akranların %5'inden azı bu kadar uçtaysa. | Orta sıra yüzdelik eşit değerlerde (örn. koyu ton 0) yapay uç üretir. |
| 2026-10-19 | Karşılaştırma grubu 100'den küçükse ⚠ verilmez, "grup küçük" notu. | %5'lik kuyruk 5'ten az çizime dayanırdı. |
| 2026-10-19 | Metin rapor beş ölçüm gösterir, JSON hepsini. | Klinisyen için okunur kalsın; ayrıntı JSON'da. |
| 2026-10-21 | Renklilik ve kenar yoğunluğu çizim piksellerine göre (ölçüm sürümü 3). | Sayfa tabanlı halleri dolulukla 0,76 / 0,87 ilişkiliydi; doluluğu tekrar ediyordu. |
| 2026-10-21 | Metin rapordaki "Detay" yerine "Çizgi miktarı" (toplam çizgi uzunluğu, iskelet). **Uygulanmadı.** | Kenar yoğunluğu / çizim pikseli çizgi inceliğini ölçüyordu (çizgi kalınlığıyla −0,75). |
| 2026-10-21 | Küçük çizim: doluluk < 0,03'te küçük çizim kümesine ⚠ verilmez, metinde "*". Küme kuralla: adaylardan (çizim pikseli tabanlı oranlar ve renk sayısı) küçük çizimlerdeki aralık dışı oranı, doluluk > 0,1 olanlardakinin en az 2 katı olanlar. | Küçük çizimde oransal ölçümler birkaç çizgiye dayanır. Büyüklüğü betimleyen ölçümler (doluluk, kutu, sayfa tabanlı, mutlak, konum) aday değil: uç çıkmaları doğru betimleme. |
| 2026-10-21 | Maske kontrol sayfası sadece train'den seçer; yeni çalıştırmalar tarihli klasöre, onaylı sayfanın üzerine yazmaz. | Test görselleri okunmasın; onaylı kayıt korunsun. |
| 2026-10-21 | Sınıflandırıcı normları (görev uyumu, ayrışma) val'den. | Model train'i gördü, skorları iyimser; test son değerlendirmeye ayrılı. |
| 2026-10-21 | Görev uyumu ve ayrışma ham olasılık değil, yüzdelik olarak sunulur. | Ham olasılık "benzerlik yüzdesi" değil; label smoothing ve kalibrasyon belirsizliği. |
| 2026-10-21 | ML çıktılarına (görev uyumu, ayrışma) ⚠ verilmez; uyarı özetine ve görüşme önerilerine girmez. | %5 kuralı modelin ilkokul erkeklerdeki hatasını ⚠ olarak bu gruba taşırdı; düzeltmek cinsiyet girdisi gerektirir. |
| 2026-10-21 | Model sınırlama notları herkese aynı gösterilir, cinsiyete göre koşullu değil. | Gösterim cinsiyete göre değişmesin. |
| 2026-10-21 | Görev uyumu norm grubu (eğitim seviyesi mi sınıf mı) val tahminlerinden önce yazılmış ölçütle seçilir (`docs/plan_gorev_uyumu.md`). | Veriye bakıp ölçüt seçmek sonucu yönlendirir. |
| 2026-10-21 | Görev uyumu ve ayrışma normları **eğitim seviyesi x görev** (ilkokul 346, ortaokul 347 çizim / öğrenci); ayrışma olasılık farkıyla. | Önceden yazılmış ölçüt: 6 hücrenin hiçbirinde sınıf eğilimi hem anlamlı (p < 0,05/6) hem ≥ 10 puan değil. Sınırda: ortaokul üzgün, düzeltmesiz p 0,030, sapma 11,8. İki skoru aynı uçta çift %5,9 (logit eşiği %25). |
| 2026-10-21 | İş akışı: plan → denetleyici → kullanıcı onayı → uygulama → dogrulayici → kapanış (commit, push, belge güncelleme). Planlama ve kararlar Claude Code oturumlarında; ayrı planner subagent yok. Commit ve push'u Claude yapar. | Kararlar tek yerde, izlenebilir kalsın (CLAUDE.md, iş akışı). |
