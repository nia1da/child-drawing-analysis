# Doğrulama: pilot hazırlığı, öğrenci bölmesi, örnek rapor, fizibilite belgeleri

Tarih: 2026-11-25. Kapsam: `src/handwriting/{pdf_io,splits,pilot,report,example_report}.py`, `features.line_table`, `paths.require_permission`, `viz.annotate_regions`, `synthetic.make_pdf`,
`tests/test_handwriting_io.py`, `docs/el_yazisi_*.md`, karar/plan/durum güncellemeleri. Doğrulayıcı kodu değiştirmedi; düzeltmeleri ana oturum yaptı.

## Sonuç: ŞÜPHELİ (küçük bulgular, engelleyici yok) → bulgular düzeltildi

Doğrulanan: 131 test geçti; 9 bellek içi mutasyondan 8'i testlerce yakalandı (sayfa dönüşü dönüşümü, izin geçidinin etkisizleştirilmesi/`exists`/`approved` gevşetilmesi, öğrenci başına tek satır, pilotta train filtresi, `TAIL`);
izin geçidi: `load_page` ve `run_pilot` izin dosyası olmadan hiçbir PDF açmıyor, `permission.json` ve `pilot/` klasörü yok (pilot çalıştırılmadı); gizlilik: staged dosyalarda öğrenci kodu, gömülü gerçek görüntü, `splits.csv`/`pages.csv` içeriği yok, hook temiz;
`splits.csv` sha256 `docs/kararlar.md` ile aynı, 938 satır/938 benzersiz kod, 656/141/141, `make_splits_with_rule` aynı bölmeyi yeniden üretiyor (dpi farkı 0,0923, dpi tabakası kullanılmadı);
belge sayıları (910 temiz öğrenci, train 334/301, sınıf x grup, dpi dağılımları, kontrol 457, en küçük hücre 61) `pages.csv` ve `splits.csv` ile birebir tutuyor; çizim modülü ve `src/config.py` değişmedi; örnek rapor ve `docs/el_yazisi_ornek_rapor/` yalnız sentetik.

| # | Bulgu | İşlem |
|---|---|---|
| 1 | `MIN_GROUP` kaldırılırsa hiçbir test başarısız olmuyor (test referansı sayfanın kendi değeri etrafında üretiyordu) | Referans sayfanın çok altına kaydırıldı: yeterli grupta uç işareti doğar, 50 satırda doğmaz; `yeterli=False` ve "grup küçük" sınanıyor |
| 2 | `run_pilot(out_dir=...)` kontrolsüz: Drive/OneDrive'a yazabilirdi | `check_data_dir(out_dir)`; testte `H:/My Drive/...` reddediliyor |
| 3 | `render_page` izin geçidi dışında (bilinçli, docstring'de belgeli) ama CLAUDE.md/docs'ta uyarı yok | `CLAUDE.md` ve `docs/el_yazisi_prototip.md`'ye eklendi: gerçek PDF için yalnız `load_page`/`run_pilot` |
| 4 | Raporda "Ne değildir:" etiketi, olumsuzlama olmayan cümlelerin başında anlamı bozuyordu | Etiket "Sınır:" ve bölüm başlığı "yorumlanırken dikkat edilecek sınırı" oldu; test güncellendi |
| 5 | Güç sayısında yuvarlama (938 için 0,18, temiz 910 için 0,19; 301 öğrenci için SE ±2,9/±1,3) | Fizibilite belgesinde aralıklarla verildi |
| 6 | Hook, `docs/el_yazisi_ornek_rapor/` ve `el_yazisi_prototip/` altındaki ikili dosyaların içeriğini taramıyor | Kabul edilen sınır; `docs/el_yazisi_prototip.md`'de yazıldı (bu klasörlere gerçek tarama konmaz) |
| 7 | `CLAUDE.md`: "yardımcı Malaysian" ile "Malaysian arşiv" çelişkisi | "tek veri seti FD-LEX; Malaysian arşiv" |
| 8 | "BHK'de boyutla ilgili madde(ler) olduğu aktarılır" kaynağı belirsiz; .42–.63 güvenirliğin hangi bölümden geldiği belirsiz | İfade "genel bilgi, madde düzeyinde teyit edilemedi" olarak ve .42–.63 "derlemenin Tablo 2'sinden, yardımcı ajan okuması, teyit önerilir" diye düzeltildi |

Kaynak sınırı: web kaynakları (Danna 2023, PubMed 36832352, AJOT 2023) doğrulayıcı tarafından bağımsız doğrulanmadı; belgedeki "kaynak/doğrulanmadı" etiketlemesinin iç tutarlılığı kontrol edildi.
