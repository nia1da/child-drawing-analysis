# Plan

Hedef rapor: `docs/rapor_taslagi.md`. Durum 2026-10-21 itibarıyla.

| Aşama | Yapılacaklar | Bitti sayılması için | Durum |
|---|---|---|---|
| 0. Hazırlık | Veri denetimi, öğrenci ve okul bazında bölme, bölmeyi dondurma | Denetim notları ve bölme dosyası kayıtlı | sürüyor |
| 1. İnce dilim | Basit maske, 3–4 ölçüm, sınıf bazında yüzdelik, JSON, metin rapor | Tek komutla herhangi bir KIDO çiziminden rapor | bitti |
| 2. Parametreler ve normlar | Bütün ölçümler, maske kontrolü, sınıf × görev normları, kalite kuralları | Normlar kayıtlı, maske hataları belgelenmiş | sürüyor |
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
  sınırlamaları, kalite kuralları (soluk renk, küçük grup, küçük çizim) yapıldı. Açık olan:
  - metin rapordaki "detay" tanımı (kenar yoğunluğu çizgi inceliğini ölçüyor; öneri: toplam çizgi uzunluğu,
    karar bekliyor);
  - küçük çizim kuralı commit edilmedi.
- **3. Çizim yaşı ve görev uyumu:** Duygu sınıflandırıcısı (convnext_tiny, val F1 0.8095) bu aşamanın **erken yapılmış
  bir parçası**; 2026-10-19'da donduruldu. Henüz yapılmayanlar:
  - sınıf düzeyi tahmini;
  - görev uyumu ve mutlu–üzgün ayrışmanın rapora bağlanması;
  - bunların test metrikleri.
