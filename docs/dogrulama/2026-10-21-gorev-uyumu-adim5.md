# Doğrulama: görev uyumu planı, adım 5 (rapora bağlama)

Sonuç: **GEÇTİ** (2026-10-21, dogrulayici). 68 test geçiyor (düzeltmelerden sonra 69).

- `model_olcumleri` JSON'da, iki görüntülü komut ve aynı öğrenci / sıra kontrolü çalışıyor; train çizimine "skor iyimser",
  val çizimine "grubun içinde" notu çıkıyor; model yokken bölüm "çalışmadı", 26 ölçüm yerinde.
- Görev uyumu mutlu görevinde 1−p, üzgünde p; yüzdelik `model_normlari.csv`'den elle hesaplananla aynı (örnek:
  101-1C-103 mutlu 97,7 / üzgün 7,5 → rapor 8 / `d` 0,0774, 23,4). Yüzdelik normdan, iki görüntü val'den.
- ⚠ yok; sınırlamalar koşulsuz, cinsiyete göre koşullu değil, "Görev uyumu" satırının altında; tanı dili yok.
- Val tahmin CSV'si ile `score_image` farkı: 60 val çiziminde en çok 2,6e-4 (CUDA fp16); CPU–GPU farkı 2,5e-5.
  Gösterilen yüzdelik tamsayısını değiştirmez; yığılma bölgesinde sınırda 1 yüzdelik oynayabilir (nota dahil).
- Test görüntüsü ya da test tahmini kullanılmadı.

Gözlemler ve çözümü (aynı gün):
1. Çift raporunda iyimserlik / "grubun içinde" notu yoktu → `separation_section` `notlar` üretiyor.
2. İki yolda model normu yoksa CLI duruyordu → ölçüm raporları çıkıyor, ayrışma "çalışmadı".
3. `score_image` iki kez çalışıyordu → `lru_cache`.
