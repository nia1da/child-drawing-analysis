# Doğrulama: Çizgi miktarı (metin rapordaki "Detay" yerine)

Sonuç: **GEÇTİ** (2026-11-10, dogrulayici). 87 test geçiyor.

- `git diff e56c599..HEAD -- src` yalnız `src/report.py`: `TEXT_MEASURES` beşinci satırı ve iki not sabiti. `measurements/*`,
  `task_fit.py`, `MEASUREMENT_VERSION`, `SMALL_DRAWING_CANDIDATES`, `SMALL_DRAWING_MEASURES` değişmedi; normlar sürüm 3.
- 3 gerçek train çiziminde rapor çalıştı; JSON'da 26 ölçüm, `kenar_yogunlugu_cizim` ve `cizgi_uzunlugu` yerinde; metin 5 satır.
- Elle yüzdelik (`olcum_normlari.csv`, orta sıra + `tail_shares`) 4 çizimde rapor ve ⚠ kararıyla aynı (örn. 289 → 0,2,
  "1. dilimin altında" ⚠; 4905 → 68,8, ⚠ yok).
- Belge rakamları normlardan yeniden hesaplanınca aynı: Spearman tablosu (doluluk 0,59 en yüksek), doluluk 0,08–0,12
  bandında 5.–95. dilim 967–4435 (n=650), ⚠ oranları %9,8 / %79,6 (n=93) / %8,2, 10860 görüntüden 10848'i 512 x 362.
- Anlam kontrolü (yalnız train): doluluğu benzer düşük 3 çizim (421, 744, 935; tek nesneli, boyama 0,98–1,0) ve yüksek 3
  (4768, 4905, 5033; kafes, şehir, karalama) görünenle uyuşuyor; seyrek taramalı çizimde "çok çizgi" doğru; yoğun
  boyalı çizimde (101-2F-230-M-H, boyama 0,91) çizgi miktarı düşük, not tam bunu söylüyor.
- Küçük çizimde çizgi miktarı ⚠ alıyor, "*" almıyor, "aynı olguyu yansıtır" notu çıkıyor; normal çizimde not yok.
- Val/test görüntüsü açılmadı; test tahmin CSV'sinin hash'i değişmedi.

Gözlem A: tam sayfa boyalı çizimlerde (doluluk > 0,9, train'de 294 çizim, %3,7) iskelet çok kısa kalır ve çizgi miktarı
⚠ alır (örn. 230-8B-43-F-S: iskelet 153, gerçekte karakalem de var). "Azlık = çabasızlık" okunmasın diye
`docs/olcumler.md` sınırlama 11'e eklendi. Gözlem B: düşük çizgi miktarı "az çizgi + boyalı alan" anlamına gelebilir;
boyama oranı yalnız JSON'da, plan bunu kabul etmişti, rapordaki not yeterli.
