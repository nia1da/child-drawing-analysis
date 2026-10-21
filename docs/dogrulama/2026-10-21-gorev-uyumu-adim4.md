# Doğrulama: görev uyumu planı, adım 4 (norm dosyası `normlar/model_normlari.csv`)

Sonuç: **GEÇTİ** (2026-10-21, dogrulayici).

- Alanlar plandakiyle aynı, cinsiyet sütunu yok. Boşluklar yalnız çift satırlarında (dosya, gorev, olasilik_uzgun).
- 1386 çizim + 693 çift; grup n'leri 346 / 346 / 347 / 347, çiftler 346 / 347. Val tahminlerinden yeniden hesaplananla
  çizim ve öğrenci kümeleri birebir aynı, skor farkı en çok 1e-16.
- `load_model_norms` yanlış model adında ve bozulmuş sürümde `RuntimeError` veriyor.
- Yalnız val okundu, test tahminlerine dokunulmadı. 61 test geçiyor.

Notlar: `olcumler.md`'de `ayrisma_skoru` değeri yanlış yazılmıştı (`olasilik`; dosyada `d_olasilik`), düzeltildi.
Testler `ayrisma_skoru` ve çiftlerdeki `skor` değerlerini doğrulamıyor, yalnız satır sayılarını (adım 6'da
test metrikleriyle birlikte güçlendirilebilir).
