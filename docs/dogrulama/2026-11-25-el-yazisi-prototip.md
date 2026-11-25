# Doğrulama: El yazısı prototipi (sentetik)

Tarih: 2026-11-25. Kapsam: `src/handwriting/*`, `tools/check_no_student_data.py`, `tools/install_hook.py`, `tests/test_handwriting.py`, `tests/test_check_no_student_data.py`.
Doğrulayıcı kodu değiştirmeden denetledi; düzeltmeleri ana oturum yaptı.

## Tur 1: sonuç ŞÜPHELİ (başarısız değil)

Doğrulanan: 109 testin tamamı geçti; `docs/el_yazisi_prototip.md` sayısal tabloları yeniden çalıştırmayla tutarlı (demo ve koşul tablosu, x-yüksekliği %0,6 / %5,6, taban 0,02–0,19 mm, demo PNG'leri yeniden üretilebilir); çizim modülü ve `src/config.py` değişmedi;
`data/` git dışı, repoda öğrenci kodu/gömülü gerçek görüntü/kullanıcı adı izi yok; mantık yönünden işaret/birim hatası bulunmadı (taban uzaklığı pozitif = yukarıda, eğim pozitif = sağa aşağı, mm/px = 25,4/dpi);
boş/siyah/küçük sayfa çökmüyor.

| # | Bulgu | Önem | Düzeltme (tur 1 sonrası) |
|---|---|---|---|
| 1 | 56–70 mm genişliğindeki kod kutusunun üst/alt kenarı "çizgi" sayılıyor (n_rules 25, `code_box_found=False`, satır indeksi 2 kayıyor); bayrak yok (testteki 50 mm'lik kutu eşiğin 52,5 mm altında kalıyordu) | orta, sessiz | Bir bant sayfa genişliğinin ≥ %50'sini kaplamalı (`find_rules(min_span_frac)`); aralık/ızgara bayrakları (`rule_spacing_off`, `rule_grid_irregular`); 56 ve 70 mm kutulu testler. Düzeltme olmadan hatanın yeniden üretildiği ayrıca görüldü (filtre kapalı: 25 çizgi, 9 satır; açık: 23 çizgi, 8 satır) |
| 2 | `paths.check_data_dir` belgenin dediğinden dar: `/content/drive/MyDrive/fd_lex`, `.../MyDrive/x`, `/mnt/gdrive/x` kabul ediliyordu; testteki örnek yalnız "bitirme" yüzünden reddediliyordu; `COLAB_RELEASE_TAG` dalı sınanmıyordu | orta | `mydrive`, `gdrive`, `/content/drive` eklendi; test bu kalıpları ve `COLAB_RELEASE_TAG`'i sınıyor. (`fd_lex_dir` henüz hiçbir veri okuma koduna bağlı değil: okuma kodu yok) |
| 3 | Zayıf/boş assert'ler: `hw & box_mask == 0` ve `hw & overlay == 0` totoloji; skew testi `abs()` ile işareti yakalamıyor; maske testi %60–140 ve `(150/150)**2` etkisiz; x-yüksekliği toleransı %15 (kabul taslağı %10); eksik çizgi tamamlama ve `find_code_box` uçtan uca test yok | orta-düşük | Totoloji yerine gerçek vuruş maskesinin 3 px dilatasyonu dışındaki piksel (sızıntı) < %1; işaretli skew testi (−0,4); maske oranı 0,85–1,25; tolerans %10; eksik çizgi silinip tamamlanması (`rules_filled=1`) ve geniş kutu uçtan uca testleri; `regularize` birim testleri |
| 4 | `regularize` kırılgan: yarım aralıkta sahte çizgi ızgarayı yarılıyor (15 çizgilik sahte ızgara), 3 px'e bölünmüş çizgi `d.min=3` ile hiçbir şey eklemiyor, başta/sonda eksik tamamlanmıyor, mevcut çizgilerin y'si ızgaraya kayıyor (1,6 mm'ye kadar) | düşük | Aralık = ardışık farkların medyanı; aynı ızgara noktasındaki çizgilerden ızgaraya yakın olan kalır, uymayanlar atılır; bulunan çizgilerin y'si korunur. Baştaki/sondaki eksik tamamlanmaz (belgelendi) |
| 5 | Köprüleme çizgi bandının ±2 px'lik parçalarını el yazısına katabilir (hw/gerçek ≈ 1,10) | düşük | Belgelendi (köprü şişmesi) |
| 6 | `overlay_boxes` float olunca TypeError; `roi_cut_ink_px` yanıltıcı ad; hook `grad_proj.ipynb` için yanlış pozitif verir (staged olursa) | düşük | `int(round())` dönüşümü; `dark_outside_roi_px`; `notebooks/grad_proj.ipynb` muaf, görüntü/PDF/zip/xlsx dosyaları yalnız `docs/el_yazisi_prototip/` altında izinli |
| 7 | Belge eksikleri: kutu genişliği kırılganlığı, kurşun+JPEG 40'ta ≈ %22–26 mürekkep kaybı, `skew_deg` düzeltme açısı, çizgi ızgarası sınırları | düşük | `docs/el_yazisi_prototip.md` sınırlamalar 8–10 ve özellik tablosu güncellendi |

## Tur 2 (bağımsız doğrulayıcı, düzeltmeler sonrası): ŞÜPHELİ (hafif; engelleyici bulgu yok)
Doğrulanan: 114 testin tamamı geçti; geniş kod kutusu (56 ve 70 mm) ile 23 çizgi, kutu bulundu, 8 satır, temiz sayfada yanlış bayrak yok; yol koruması (`/content/drive/MyDrive/...`, `/mnt/gdrive`, `D:/MyDrive`, OneDrive, `COLAB_RELEASE_TAG`, `CIZIM_ENV=colab`) reddediyor,
yerel yol kabul; `regularize` senaryoları (sahte yarım aralık, bölünmüş çizgi, iç boşluk, baştaki eksik, temiz girdi) beklendiği gibi, 200 rastgele düzensiz girdide çökme yok; hook geçici git deposunda ikili dosyayı izinli klasör dışında reddediyor,
`docs/el_yazisi_prototip/` içinde kabul ediyor; çizim modülü, `src/config.py`, `src/measurements`, `src/report.py` değişmedi; repoda öğrenci kodu/kullanıcı satırı/gömülü görüntü yok. Mutasyon denemesi: 6 mutasyonu testler yakaladı
(`min_span_frac=0`, `regularize` aralığı min, sahte çizgi atmama, `~box_mask` kaldırma, `mydrive` ve `/content/drive` kalıpları).

Kalan bulgular ve işlemleri:
| Bulgu | İşlem |
|---|---|
| "Bulunan çizgilerin y'si korunur" iddiasını hiçbir test sınamıyor (ilgili satır silinince test geçti) | Izgaradan ±2 px sapan girdide çıktının girdiyle birebir aynı olduğunu sınayan test eklendi |
| Belgede eski ifadeler ("%60–140", "sızıntı 0 piksel") | Güncellendi (oran 0,85–1,25, sızıntı < %1) |
| `regularize` eklenen çizgi sayısına üst sınır yok (bir rastgele girdi 12 çizgiden 45'lik ızgara kurdu) | Üst sınır eklendi: eksik çizgi > max(3, bulunanların %30'u) ise tamamlama yapılmaz; test eklendi |
| Degenere girdide (`sp=0`) NumPy RuntimeWarning | Kabul (sonuç değişmiyor; gerçek taramada beklenmiyor) |

Sonuç: tur 1 bulguları kapandı; kalan üç madde düzeltildi (sınır testi dahil 23 handwriting testi geçiyor).
