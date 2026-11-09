# Durum

Son güncelleme: 2026-11-10. Aşamalar: `docs/plan.md`; kararlar: `docs/kararlar.md`.

## Neredeyiz
- **Aşama 1 (ince dilim):** bitti.
- **Aşama 2 (parametreler ve normlar):** neredeyse bitti. Bütün ölçümler, train normları (ölçüm sürümü 3), maske
  kontrolü, kalite kuralları (soluk renk, küçük grup, küçük çizim) tamam. Kalan: "Detay" → "Çizgi miktarı".
- **Aşama 3 (çizim yaşı ve görev uyumu):** görev uyumu ve mutlu–üzgün ayrışma raporda
  (adım 1–5 bitti, `docs/plan_gorev_uyumu.md`); test metrikleri (adım 6) kaldı. Sınıf düzeyi tahmini henüz planlanmadı.

## Son biten iş
- Küçük çizim kümesi kuralla belirlendi, metin raporda "*" işareti, JSON kalite alanları; dogrulayici: GEÇTİ
  (`docs/dogrulama/2026-10-21-kucuk-cizim-kumesi.md`).
- Maske kontrol sayfası sadece train'den, tarihli klasöre.
- İş akışı CLAUDE.md'ye yazıldı; `docs/kararlar.md` ve bu dosya oluşturuldu.

## Sıradaki adım
Görev uyumu planı adım 2 bitti (2026-10-21; dogrulayici GEÇTİ): normlar eğitim seviyesi x görev, ayrışma olasılık
farkıyla (`docs/olcumler.md`, "Model tabanlı ölçümler"). Yığılma kararı verildi: tam yüzdelik + her raporda not
(`docs/kararlar.md`). Adım 3, 4 ve 5 bitti (dogrulayici GEÇTİ; adım 5: `docs/dogrulama/2026-10-21-gorev-uyumu-adim5.md`, 69 test geçiyor).
Sıradaki: adım 6 (test metrikleri, bir kez, en son). Ayrıca "Detay" → "Çizgi miktarı" için plan.

## Açık sorular
- **Okul bazında bölme:** kararda "öğrenci ve okul bazında" var, uygulanan öğrenci bazında. Test KIDO'nun resmi
  klasörü olduğu için okul bazında ayrım sadece val için yapılabilir; val değişirse referans modelin epoch seçimi ve
  val tabanlı her şey (sınıflandırıcı normları dahil) yeniden ele alınmalı. Yapılacak mı, ne zaman?
- **"Çizgi miktarı":** karar verildi, uygulama ayrı iş (ölçüm değil metin rapor değişikliği; plan → onay akışıyla).
- **Okul bazında sızıntı ölçümü:** bölme değişmese bile aynı okulun train ve val/test'te olmasının etkisi ölçülebilir.
- Aşama 0'daki veri denetimi notları yazılı belge olarak yok.
