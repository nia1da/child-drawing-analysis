# Plan

Hedef rapor: `docs/rapor_taslagi.md`. Durum 2026-11-25 itibarıyla.
Bu tablo **Çizim/görüntü modülünün** aşamalarıdır; El yazısı modülünün aşamaları aşağıdaki "El yazısı modülü" bölümünde (`docs/plan_el_yazisi.md`).

| Aşama | Yapılacaklar | Bitti sayılması için | Durum |
|---|---|---|---|
| 0. Hazırlık | Veri denetimi, öğrenci ve okul bazında bölme, bölmeyi dondurma | Denetim notları ve bölme dosyası kayıtlı | sürüyor |
| 1. İnce dilim | Basit maske, 3–4 ölçüm, sınıf bazında yüzdelik, JSON, metin rapor | Tek komutla herhangi bir KIDO çiziminden rapor | bitti |
| 2. Parametreler ve normlar | Bütün ölçümler, maske kontrolü, sınıf × görev normları, kalite kuralları | Normlar kayıtlı, maske hataları belgelenmiş | bitti |
| 3. Çizim yaşı ve görev uyumu | Sınıf düzeyi tahmini, görev uyumu, mutlu–üzgün ayrışma | Test metrikleri raporlandı, rapora eklendi | sürüyor (erken parça) |
| 4. Açıklama metinleri | Kelime sayısı, duygu kelimeleri, yazım hatası yoğunluğu ve normları | Rapora eklendi | başlamadı |
| 5. Çağrışım | Benzer çizim arama, tema listesi, çizim → tema modeli | Arama çalışıyor; tema modeli şansın üstünde mi belli | başlamadı |
| 6. Sahne betimleme | Görsel-dil modeliyle yapılandırılmış form, 200 çizim elle etiketleme, alan bazında doğruluk | Doğruluk oranları rapora yazılıyor | başlamadı |
| 7. Arayüz ve kayıt | Görüşme önerisi kuralları, Gradio arayüzü, SQLite ile kayıt ve ziyaretler | Klinisyen kayıt açıp çizim yükleyebiliyor | başlamadı |
| 8. Klinisyen değerlendirmesi | Örnek raporlar üzerinde geri bildirim | Notlar ve düzeltme listesi | başlamadı |

## Durum notları

- **0. Hazırlık:** Bölme yapıldı ve kayıtlı (`data/kido_metadata.csv`, `bolum` sütunu; `splits.stratified_split`):
  test KIDO'nun resmi `test` klasörü, val train'den öğrenci bazında %15, seed 42. Eksik olanlar:
  - **okul bazında** bölme yok; aynı okulun öğrencileri hem train'de hem val/test'te olabilir;
  - veri denetimi notları yazılı bir belge olarak yok.
- **1. İnce dilim:** 2026-10-19'da bitti: maske, doluluk, renk sayısı, koyu ton, train normları, JSON + metin rapor.
- **2. Parametreler ve normlar:** Bütün ölçümler, normlar (ölçüm sürümü 3), maske kontrol sayfası, maske
  sınırlamaları, kalite kuralları (soluk renk, küçük grup, küçük çizim) yapıldı. Küçük çizim kümesi kuralla
  belirlendi ve commit edildi (2026-10-21). Metin rapordaki "Detay" yerine "Çizgi miktarı" (toplam çizgi uzunluğu,
  iskelet) 2026-11-10'da uygulandı (`docs/plan_cizgi_miktari.md`, dogrulayici GEÇTİ). Açık iş kalmadı.
- **3. Çizim yaşı ve görev uyumu:** Duygu sınıflandırıcısı (convnext_tiny, val F1 0.8095) bu aşamanın **erken yapılmış
  bir parçası**; 2026-10-19'da donduruldu. Görev uyumu ve mutlu–üzgün ayrışma rapora bağlandı
  (`docs/plan_gorev_uyumu.md` adım 1–5, dogrulayici GEÇTİ, 2026-10-21); test metrikleri ölçüldü ve belgelendi (adım 6,
  `docs/plan_test_metrikleri.md`, dogrulayici GEÇTİ, 2026-11-10). Henüz yapılmayan tek parça: **sınıf düzeyi tahmini**
  (rapor taslağında "sınıf düzeyi tahmini" satırı; planlanmadı, klinisyen geri bildirimine kadar bekleyebilir).

## El yazısı modülü (ayrı ve bağımsız; ana veri seti FD-LEX Scriptoria, kullanım iznine bağlı)

Plan: `docs/plan_el_yazisi.md` (taslak v2; denetleyici bulguları işlendi, kullanıcı onayı bekliyor). Kararlar: `docs/kararlar.md` (2026-11-25). Çizim modülüne dokunulmaz.

| Aşama | Yapılacaklar | Bitti sayılması için | Durum |
|---|---|---|---|
| H0. Veri seçimi ve EDA | Malaysian EDA, FD-LEX EDA (denetim + ön fizibilite) | EDA belgeleri kabul edildi | **bitti** (`docs/handwriting_dataset_analysis.md`, `docs/fd_lex_dataset_analysis.md`) |
| H1. İzin ve yerel koruma (A0) | Kullanım izni sorusu, yerel-only koruma, commit öncesi veri denetimi | İzin yanıtı kayıtlı; koruma testleri | **koruma ve denetim bitti** (`paths.py`, pre-commit kancası, testler); **izin yanıtı bekleniyor** |
| H1c. Pilot hazırlığı, rapor tasarımı, fizibilite | Bilimsel temel, 20 öğrencilik pilot protokolü ve kodu (izne bağlı), sentetik örnek rapor, referans/ML fizibilitesi, bölme dondurma | Belgeler ve kod hazır; bölme dondurulmuş | **bitti** (2026-11-25); pilot izin sonrası |
| H1b. Prototip (sentetik) | Ölçek/eğiklik, çizgi-kutu-XXX ayrıştırma, el yazısı maskesi, satır segmentasyonu, bileşen boyutu, hiza, sayfa kullanımı, görselleştirme | Sentetik testler geçiyor; sonuçlar görselleştirildi (`docs/el_yazisi_prototip.md`) | **bitti** (2026-11-25); gerçek sayfa pilotu izin sonrası |
| H2. Çıkarma ve bölme (A1, A7) | Kayıpsız sayfa çıkarma, manifest, tekilleştirme, 27 belirsiz öğrencinin görev/zaman eşlemesi, öğrenci bazlı bölme dondurma | Manifest 5656 satır, `splits.csv` dondurulmuş | başlamadı (plan onayı bekliyor) |
| H3. Normalizasyon ve ayrıştırma (A2–A4) | Fiziksel ölçek, çizgi/kod kutusu/XXX maskeleri, yazı alanı ve satır segmentasyonu, elle işaretli 60 sayfa | Maske ve segmentasyon kabul ölçütleri geçti | başlamadı |
| H4. Özellikler ve dayanıklılık (A5, A6) | Harf boyutu, satır hizası, eğim, sayfa kullanımı; çözünürlük/kalem/tarama dayanıklılığı | Her özellik "kararlı / koşullu / dışlandı" | başlamadı |
| H5. Referans dağılımlar ve rapor | Sınıf x görev x zaman referansları (train), betimleyici rapor | "Bu örneklemde akranlara göre" raporu | başlamadı |

Kapsam dışı: kelime aralığı, okunabilirlik tahmini, disgrafi sınıflandırması, psikolojik risk skoru, `Rating` etiketi, model eğitimi, yeni veri seti araştırması. **Bilimsel hedef** (2026-11-25): grafomotor gelişimle ilişkili biçimsel ve görsel-mekânsal özellikleri ölçmek, referans gruplarıyla karşılaştırmak, uzmana açıklanabilir rapor sunmak (`docs/el_yazisi_bilimsel_temel.md`). Malaysian veri seti **arşiv**. Transkriptler gelecek çalışma (`docs/el_yazisi_gelecek_calisma.md`).

