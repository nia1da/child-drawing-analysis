# Durum

Son güncelleme: 2026-11-25. Aşamalar: `docs/plan.md`; kararlar: `docs/kararlar.md`.

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

## El yazısı modülü (2026-11-25)
- **DiaGraMo deneyleri (2026-11-27):** DiaGraMo ana veri seti; FD-LEX ve Malaysian pasif/arşiv. 525 kullanılabilir yazma kaydı PNG'ye dönüştürüldü; 43 geometrik özellik (koordinatlarla doğrulandı); HLS üç madde (sayfa düzeni, harf biçimi, düzeltmeler) için okul bazlı bölme ve modeller: Model A (geometrik özellik) test QWK 0,41 / 0,38 / 0,40, Model B (ResNet18 gömme) 0,33 / 0,19 / 0,09; test kümesi **kullanıldı** (kilit). Klinik grup sınıflandırması ertelendi (şehir yoluyla sızıntı). Modeller render ayarlarına duyarlı; gerçek fotoğrafta doğrulama yok. Ayrıntı `docs/el_yazisi_diagramo_deney.md`; kod `src/handwriting/diagramo/`.
- **DiaGraMo araştırması (2026-11-26):** EDA, etiket analizi, koordinat → PNG prototipi ve model fizibilitesi tamam (`docs/el_yazisi_diagramo_eda.md`; kod `src/handwriting/diagramo/`, `tests/test_diagramo.py`); 16 örnek görüntü yerelde. Rolü (FD-LEX için etiketli doğrulama kümesi mi, model eğitimi mi) kullanıcı kararı bekliyor; ilk öneri: kendi geometrik özelliklerimizi HLS maddeleriyle karşılaştırmak.
- **Bilimsel hedef (netleşti):** grafomotor gelişimle ilişkili biçimsel/görsel-mekânsal özellikleri ölçmek, referanslarla karşılaştırmak, uzmana açıklanabilir rapor sunmak; motor beceriyi doğrudan ölçtüğümüzü ve BHK vb. puan ürettiğimizi iddia etmeyiz; okunabilirlik, disgrafi sınıflandırması, risk skoru kapsam dışı. **Yalnız FD-LEX; Malaysian arşiv.**
- **Son iş:** `docs/el_yazisi_bilimsel_temel.md` (özellik–kaynak haritası; BHK madde düzeyi doğrulanamadı), `docs/el_yazisi_pilot_protokolu.md` + `src/handwriting/pilot.py` (20 öğrenci, izin geçidi `permission.json`; çalıştırılmadı),
  `docs/el_yazisi_arastirma_fizibilite.md` (5 soru; v1'de ML yok), `docs/el_yazisi_ornek_rapor.md` (sentetik örnek rapor + işaretli bölgeler), `docs/el_yazisi_gelecek_calisma.md` (transkriptler), öğrenci bazlı bölme donduruldu (hash `docs/kararlar.md`'de).
- **Karar:** ana veri seti **FD-LEX Scriptoria** (kullanım iznine bağlı); Malaysian yardımcı olarak korunur. EDA belgeleri: `docs/fd_lex_dataset_analysis.md`,
  `docs/handwriting_dataset_analysis.md`. Plan: `docs/plan_el_yazisi.md` (taslak v2: denetleyici bulguları işlendi; kullanıcı onayı bekliyor; uygulama başlamadı).
- **Prototip (2026-11-25):** `src/handwriting/` sentetik görüntülerle çalışıyor (`docs/el_yazisi_prototip.md`: ölçek/eğiklik, çizgi-kod kutusu-XXX ayrıştırma, el yazısı maskesi, satır segmentasyonu, bileşen boyutu, hiza, sayfa kullanımı, görselleştirme, 23 test); pre-commit veri denetimi kurulu. Kabul edilen kararlar: 150 dpi, 70/15/15 öğrenci bazlı bölme, kayıpsız çıkarma, izin geçidi. **Henüz yok:** gerçek sayfa pilotu (izin), 100 sayfalık işaretleme, istatistiksel doğrulama, A1 (çıkarma/manifest), A7 (bölme dondurma).
- **Kural:** FD-LEX verisi ve türevleri izin netleşmeden Drive, Colab veya GitHub'a gitmez, yalnız yerel. Notebook çıktıları (öğrenci taramaları, kodlar) commit'ten önce temizlenir.
- **Kapsam dışı:** kelime aralığı, okunabilirlik skoru; `Rating` etiket değil.
- **Açık:** (1) kullanım izni ve lisans (FD-LEX / Mercator-Institut'a sorulacak, kullanıcı); (2) kod kitabı (Rating, AlphabetTask, SLS, Wortschatz); (3) plandaki onay bekleyen kararlar
  (çalışma çözünürlüğü, bölme, elle işaretleme, kabul ölçütleri); (4) belirsiz görev/zaman: 27 öğrenci + tekrar eden sayfanın öğrencisi (tekilleştirince 5 sayfa) = **28**; çözünürlük–sınıf ilişkisi (planda ele alındı, v2).

## Sıradaki adım
0. **El yazısı:** FD-LEX izin yanıtı (`permission.json` kullanıcıdan); izin gelirse 20 öğrencilik pilot (`docs/el_yazisi_pilot_protokolu.md`), gözlenen sorunlara göre düzeltme, sonra plan A1 (kayıpsız çıkarma, manifest), elle işaretleme (A3) ve ölçüm güvenilirliği. Rapor tasarımı ve fizibilite belgeleri uzman/kullanıcı geri bildirimine hazır. A3'e izin gelmeden geçilmez.
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
