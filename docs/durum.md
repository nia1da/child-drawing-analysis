# Durum

Son güncelleme: 2026-11-10. Aşamalar: `docs/plan.md`; kararlar: `docs/kararlar.md`.

## Neredeyiz
- **Aşama 1 (ince dilim):** bitti.
- **Aşama 2 (parametreler ve normlar):** neredeyse bitti. Bütün ölçümler, train normları (ölçüm sürümü 3), maske
  kontrolü, kalite kuralları (soluk renk, küçük grup, küçük çizim) tamam; metin rapor beşinci satırı "Çizgi miktarı" (2026-11-10).
- **Aşama 3 (çizim yaşı ve görev uyumu):** görev uyumu ve mutlu–üzgün ayrışma raporda
  (adım 1–5 bitti, `docs/plan_gorev_uyumu.md`); test metrikleri (adım 6) da bitti. Sınıf düzeyi tahmini henüz planlanmadı.

## Son biten iş
- **Görev uyumu ve mutlu–üzgün ayrışma** (`docs/plan_gorev_uyumu.md`, tamamlandı 2026-11-10): val normları, rapora bağlama,
  test metrikleri (`docs/plan_test_metrikleri.md`; test AUC 0,889, norm aktarımı makul, ilkokul erkek mutlu→üzgün %28,3).
  Dogrulayici: adım 2–6 GEÇTİ (`docs/dogrulama/`). Aşama sonu denetimi: uyumlu; öneriler (rapor taslağı hizalama,
  temkinli iyimserlik ifadesi, kapanış kayıtları, CLAUDE.md sonuçları) işlendi.
- Test seti görev uyumu için bir kez kullanıldı (hash `docs/kararlar.md`'de); bir daha bakılmaz.

## Sıradaki adım
1. "Detay" → "Çizgi miktarı" (metin rapor değişikliği; plan → denetim → onay). Ölçüm sürümü artarsa
   `model_normlari.csv` etkilenmemeli (val ve modelden gelir), planda teyit edilecek.
2. Sınıf düzeyi tahmini (aşama 3'ün kalanı) planı. Dikkat: betimleyici dil (gelişimsel gerilik ima edilmez, ⚠ yok);
   normlar sınıfa göre olduğu için döngüsel doğrulama riski; test setini yeniden kullanmak ayrı bir karar olur;
   yeni model gerekirse okul bazında bölme kararı önce verilmeli; cinsiyet girdi değil.
3. Aşama 8'de klinisyene sorulacaklar: "görev uyumu" adı, ilkokul erkek notu, yığılma notu anlaşılırlığı.

## Açık sorular
- **Okul bazında bölme:** kararda "öğrenci ve okul bazında" var, uygulanan öğrenci bazında. Test KIDO'nun resmi
  klasörü olduğu için okul bazında ayrım sadece val için yapılabilir; val değişirse referans modelin epoch seçimi ve
  val tabanlı her şey (sınıflandırıcı normları dahil) yeniden ele alınmalı. Yapılacak mı, ne zaman?
- **"Çizgi miktarı":** karar verildi, uygulama ayrı iş (ölçüm değil metin rapor değişikliği; plan → onay akışıyla).
- **Okul bazında sızıntı ölçümü:** bölme değişmese bile aynı okulun train ve val/test'te olmasının etkisi ölçülebilir.
- Aşama 0'daki veri denetimi notları yazılı belge olarak yok.
