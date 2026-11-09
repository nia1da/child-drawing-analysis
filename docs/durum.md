# Durum

Son güncelleme: 2026-11-10. Aşamalar: `docs/plan.md`; kararlar: `docs/kararlar.md`.

## Neredeyiz
- **Aşama 1 (ince dilim):** bitti.
- **Aşama 2 (parametreler ve normlar):** bitti. Bütün ölçümler, train normları (ölçüm sürümü 3), maske
  kontrolü, kalite kuralları (soluk renk, küçük grup, küçük çizim) tamam; metin rapor beşinci satırı "Çizgi miktarı" (2026-11-10).
- **Aşama 3 (çizim yaşı ve görev uyumu):** görev uyumu ve mutlu–üzgün ayrışma raporda
  (adım 1–5 bitti, `docs/plan_gorev_uyumu.md`); test metrikleri (adım 6) da bitti. Sınıf düzeyi tahmini henüz planlanmadı.

## Son biten iş
- **Aşama 2 kapandı** (2026-11-10): metin rapordaki "Detay" yerine "Çizgi miktarı" (toplam çizgi uzunluğu; `docs/plan_cizgi_miktari.md`,
  dogrulayici GEÇTİ, `docs/dogrulama/2026-11-10-cizgi-miktari.md`). Aşama sonu denetimi: uyumlu; belge düzeltmeleri yapıldı.
- **Görev uyumu ve mutlu–üzgün ayrışma** (`docs/plan_gorev_uyumu.md`, tamamlandı 2026-11-10): val normları, rapora bağlama,
  test metrikleri (`docs/plan_test_metrikleri.md`; test AUC 0,889, norm aktarımı makul, ilkokul erkek mutlu→üzgün %28,3).
  Test seti görev uyumu için bir kez kullanıldı (hash `docs/kararlar.md`'de); bir daha bakılmaz.
- **Görüntü modülü taslak olarak donmuş sayılır** (2026-11-10, kullanıcı kararı): ölçümler, normlar, kalite kuralları, görev uyumu
  ve ayrışma tamam. Performans iyileştirmesi uçtan uca ilk sistem görüldükten sonra.

## Sıradaki adım
1. **İlk uçtan uca dilim** planı (plan modunda): ortak modül JSON sözleşmesi (`modul`, durum, ölçümler, kalite, not), Gradio
   arayüz iskeleti (taslak: görüntü modülünü gösterir), Yazı ve Konuşma modüllerinin ilk ölçümleri. Plan.md'deki aşama sırası
   (arayüz aşama 7'deydi) bu plan onaylanınca güncellenir. Kullanıcı Yazı/Konuşma veri setlerini inceliyor.
2. Sınıf düzeyi tahmini (aşama 3'ün kalanı) beklemede. Dikkat: betimleyici dil (gelişimsel gerilik ima edilmez, ⚠ yok); normlar
   sınıfa göre olduğu için döngüsel doğrulama riski; test setini yeniden kullanmak ayrı karar; yeni model gerekirse okul
   bazında bölme kararı önce; cinsiyet girdi değil.
3. Küçük işler: okul bazında sızıntı ölçümü, aşama 0 veri denetimi notlarını tek belgede toplamak.
4. Aşama 8 / erken klinisyen turunda sorulacaklar: "görev uyumu" adı, ilkokul erkek notu, yığılma notu, iki ⚠'nin tek olgu
   olduğu notu anlaşılıyor mu, küçük çizimde mutlak ölçümler ⚠ alırken oransal olanlar "*" alıyor (fark kafa karıştırıyor mu),
   sınıf düzeyi tahmini satırı işe yarar mı.

## Açık sorular
- **Tam sayfa boyalı çizimde çizgi miktarı ⚠** (doluluk > 0,9, train'de %3,7): iskelet kısa kaldığı için "çizgi azlığı" gibi
  okunabilir. Not ve `olcumler.md` sınırlama 11 var. Karar bekliyor: "kabul edildi, aşama 8'de klinisyene sorulur" mu,
  yoksa "çözülecek" mi (çözülecekse küçük çizim gibi tabloyla sabitlenen bir kural gerekir). Çizgi miktarı mutlak piksel sayısı;
  yükleme arayüzüne görüntü boyutu uyarısı eklenmeli (512 x 362 dışında norm geçersiz).
- **Okul bazında bölme:** kararda "öğrenci ve okul bazında" var, uygulanan öğrenci bazında. Test KIDO'nun resmi
  klasörü olduğu için okul bazında ayrım sadece val için yapılabilir; val değişirse referans modelin epoch seçimi ve
  val tabanlı her şey (sınıflandırıcı normları dahil) yeniden ele alınmalı. Yapılacak mı, ne zaman?
- **Okul bazında sızıntı ölçümü:** bölme değişmese bile aynı okulun train ve val/test'te olmasının etkisi ölçülebilir.
- Aşama 0'daki veri denetimi notları yazılı belge olarak yok.
