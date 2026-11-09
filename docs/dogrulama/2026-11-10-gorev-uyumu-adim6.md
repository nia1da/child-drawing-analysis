# Doğrulama: görev uyumu planı, adım 6 (test metrikleri)

Sonuç: **GEÇTİ** (2026-11-10, dogrulayici). 85 test geçiyor.

- Test tahmin CSV'sinin sha256'sı (`ac410b6f…98c1`) `ozet.json` ve `docs/kararlar.md` ile aynı; 1632 satır, 816 öğrenci.
  Dosya, plan commit'inden (514b3a4) sonra yazıldı. "Tek çalıştırma" dosya zamanlarından ve koruma kodundan çıkarıyor
  (kesin kanıt değil); `deneyler.csv` değişmedi.
- `git diff 38218fb..HEAD`: norm / eşik / tanım / model kodu (`task_fit` norm kısımları, `analysis`, `report`,
  `training`, `model_normlari.csv`, `MODEL_NORM_VERSION`) değişmedi; çalışma ağacında yalnız `LIMITATIONS` sayısı
  (448px %33,7 → 320px %28,3). `stats.confidence_intervals` değişmedi (iki fonksiyon eklendi).
- Bağımsız yeniden hesap (sklearn ve ayrı yüzdelik fonksiyonu): AUC, macro F1, `d > 0`, alt grup AUC'leri, hata yönü
  ve norm aktarımı oranları CSV'lerle birebir; kendi seed'iyle bootstrap GA'ları tutuyor (AUC 0,872–0,905 / 0,872–0,904).
- Plana uyum: birincil metrikler, hüküm kuralı, ≤ 5 / ≥ 95 tanımı, alt gruplarda "anlamlı" yok, cinsiyet yalnız
  değerlendirme alt grubu. `docs/olcumler.md` sayıları CSV'lerle tutuyor.

Not: Colab'da eşzamanlı yazma olmadığı dosya zamanlarından görünüyor, kesin doğrulanamadı. "8 hücrenin 7'si makul"
ifadesi uç bazlıydı; düzeltildi (16 uçtan 15'i makul).
