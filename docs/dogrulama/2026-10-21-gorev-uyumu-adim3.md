# Doğrulama: görev uyumu planı, adım 3 (`docs/olcumler.md` "Model tabanlı ölçümler")

Sonuç: **GEÇTİ** (2026-10-21, dogrulayici).

- Sayılar `python -m src.task_fit` çıktısıyla ve val tahminlerinden ayrıca hesaplanan `d` yüzdelikleri / `d < 0`
  oranlarıyla birebir tutuyor (grup n 346 / 346 / 347 / 347; KW p'leri; yığılma sayıları).
- Planın "Rapor dili ve sınırlamalar" maddeleri ve ⚠ kuralları eksiksiz, çelişki yok.
- `docs/kararlar.md` (tam yüzdelik, kaba bant yok, yığılma notu) ile tutarlı.
- Cinsiyet norm, girdi ya da grup olarak geçmiyor; tek geçiş herkese aynı gösterilen sınırlama notunda.
- Doğrulanmadı: ayrışmada logit kullanılsaydı p'nin 0,23 / 0,25 olacağı (`task_fit` çıktısında yok).

Notlar:
- "Bu bölüm adım 3'te tamamlanacak" ifadesi eskimişti; düzeltildi.
- Sınırlama notunun raporda "bölümün hemen altında" durması adım 5'te (rapor kodu) kontrol edilecek.
