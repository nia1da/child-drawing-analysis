# Durum

Son güncelleme: 2026-10-21. Aşamalar: `docs/plan.md`; kararlar: `docs/kararlar.md`.

## Neredeyiz
- **Aşama 1 (ince dilim):** bitti.
- **Aşama 2 (parametreler ve normlar):** neredeyse bitti. Bütün ölçümler, train normları (ölçüm sürümü 3), maske
  kontrolü, kalite kuralları (soluk renk, küçük grup, küçük çizim) tamam. Kalan: "Detay" → "Çizgi miktarı".
- **Aşama 3 (çizim yaşı ve görev uyumu):** görev uyumu ve mutlu–üzgün ayrışma planı onaylandı
  (`docs/plan_gorev_uyumu.md`); uygulama başlıyor. Sınıf düzeyi tahmini henüz planlanmadı.

## Son biten iş
- Küçük çizim kümesi kuralla belirlendi, metin raporda "*" işareti, JSON kalite alanları; dogrulayici: GEÇTİ
  (`docs/dogrulama/2026-10-21-kucuk-cizim-kumesi.md`).
- Maske kontrol sayfası sadece train'den, tarihli klasöre.
- İş akışı CLAUDE.md'ye yazıldı; `docs/kararlar.md` ve bu dosya oluşturuldu.

## Sıradaki adım
Görev uyumu planı, adım 2: val analizi; önce `d` için olasılık / logit seçimi, sonra önceden yazılmış ölçütle norm
grubu kararı. Adım 1 bitti (2026-10-21): referans modelin val tahminleri Drive
`tahminler/convnext_tiny_320px_lr0.0001_ls0.1_s42_val.csv`; val macro F1 0,8095, kayıtla aynı.

## Açık sorular
- **Okul bazında bölme:** kararda "öğrenci ve okul bazında" var, uygulanan öğrenci bazında. Test KIDO'nun resmi
  klasörü olduğu için okul bazında ayrım sadece val için yapılabilir; val değişirse referans modelin epoch seçimi ve
  val tabanlı her şey (sınıflandırıcı normları dahil) yeniden ele alınmalı. Yapılacak mı, ne zaman?
- **"Çizgi miktarı":** karar verildi, uygulama ayrı iş (ölçüm değil metin rapor değişikliği; plan → onay akışıyla).
- **Okul bazında sızıntı ölçümü:** bölme değişmese bile aynı okulun train ve val/test'te olmasının etkisi ölçülebilir.
- Aşama 0'daki veri denetimi notları yazılı belge olarak yok.
