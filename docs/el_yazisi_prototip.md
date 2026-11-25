# El yazısı prototipi: önişleme ve özellik çıkarma (sentetik sayfalarla)

Durum: **prototip, yalnız sentetik görüntülerle** (2026-11-25). Gerçek FD-LEX sayfalarına dokunulmadı; kullanım izni netleşince 10–20 sayfalık pilot yapılacak.
Plan: `docs/plan_el_yazisi.md`. 100 sayfalık elle işaretleme ve kapsamlı istatistiksel doğrulama **başlamadı**. Çizim modülü değişmedi.

## Ne var (`src/handwriting/`)

| Dosya | İş |
|---|---|
| `paths.py` | Sabitler (150 dpi, 10,8 mm); FD-LEX koruması: Colab'da ve Drive/OneDrive yolunda reddeder |
| `normalize.py` | 150 dpi'ye alan ortalamasıyla indirme (büyütme yok, <150 dpi `low_resolution`), arka plan düzeltme, eğiklik tahmini ve düzeltme |
| `masks.py` | Basılı çizgiler (bant maskesi, eksik çizgiyi düzenli ızgarayla tamamlama, harfin çizgiyi kestiği yerde köprü), kod kutusu (içi boş büyük çerçeve), metin katmanı kutuları (XXX, telif satırı), yazı alanı (ROI), el yazısı maskesi, kalem rengi özeti |
| `segment.py` | Çizgi bantları satır; her bağlı bileşen ağırlık merkeziyle bir satıra atanır |
| `features.py` | Bileşen boyutu ve tutarlılığı, taban çizgisi uzaklığı/eğimi/dalgalanması, sayfa kullanımı ve yazı yoğunluğu, kalite bayrakları |
| `pipeline.py` | `analyze_page(rgb, dpi, overlay_boxes)` tek giriş noktası |
| `synthetic.py` | Bilinen gerçek değerli sentetik A4 sayfalar (mm cinsinden düzen, sonra dpi/kalem/eğiklik/gürültü/JPEG ile render) |
| `viz.py`, `demo.py` | Beş panelli karşılaştırmalı görselleştirme (orijinal, önişlenmiş, maskeler, satırlar, ölçümler), rapor için işaretli bölgeler (`annotate_regions`); `python -m src.handwriting.demo` |
| `pdf_io.py` | PDF'ten sayfa render (dönüşlü sayfalar dahil) ve metin katmanı kutuları (XXX, telif, kod). `render_page` saf fonksiyondur (sentetik PDF testleri için, **izin geçidi yok**: gerçek PDF'ler için çağrılmaz); gerçek PDF için `load_page` izin geçidinden geçer |
| `splits.py` | Öğrenci bazlı tabakalı bölme + dpi dengesi kuralı (yalnız meta veri); `splits.csv` yerel |
| `pilot.py` | 20 öğrencilik seçim, `run_pilot` (izin gerekir), otomatik başarısızlık işaretleri (`docs/el_yazisi_pilot_protokolu.md`) |
| `report.py`, `example_report.py` | Uzman raporu (metin + JSON) ve sentetik örnek (`docs/el_yazisi_ornek_rapor.md`) |
| `tests/test_handwriting.py` | 23 sentetik test (yol koruması [Colab, Drive, OneDrive, MyDrive], ölçek, eğiklik işareti, satırlar, el yazısı maskesi sızıntısı, dpi/kalem/JPEG dayanıklılığı, atlanan satır, geniş kod kutusu, eksik çizgi tamamlama, aralık bayrakları, `regularize` durumları, sıra korunumu, boş sayfa) |
| `tools/check_no_student_data.py`, `tools/install_hook.py` | Commit öncesi veri denetimi (öğrenci kodu, gömülü görüntü, kapak kullanıcı satırı, `data/handwriting/` yolu; **görüntü/PDF/zip/xlsx dosyaları yalnız `docs/el_yazisi_prototip/` altında** izinli); `python tools/install_hook.py` ile pre-commit kancası (kurulu). `notebooks/grad_proj.ipynb` (eski KIDO arşivi, base64 gürültüsü) muaf |

Kullanım: `PY -m src.handwriting.demo` (çıktı `docs/el_yazisi_prototip/*.png`, yalnız sentetik); testler: `PY -m unittest tests.test_handwriting tests.test_check_no_student_data`.
Gerçek sayfa (izin sonrası, yerel): `analyze_page(rgb, dpi, overlay_boxes)`; `overlay_boxes` PDF metin katmanındaki kelime kutuları (PyMuPDF `page.get_text("words")`, görüntü pikseline çevrilmiş).

## Özellikler (prototip tanımı)

| Aile | Özellik | Tanım |
|---|---|---|
| Boyut | `xheight_mm`, `xheight_cv_lines`, `xheight_iqr_ratio_within` | "Gövde bileşenleri" (satır medyan yüksekliğinin 0,6–1,4 katı) yüksekliği medyanı; satırlar arası CV; satır içi IQR/medyan |
| Boyut | `comp_h_mm_median`, `comp_h_iqr_ratio`, `comp_w_mm_median`, `n_components` | Tüm bağlı bileşenler (karşılaştırma için) |
| Hiza | `baseline_offset_mm_median/_sd` | Çizgi − taban çizgisi (satır başına Theil–Sen doğrusu), pozitif: taban çizginin üstünde; SD satırlar arası |
| Hiza | `baseline_slope_deg_median/_sd`, `baseline_wobble_mm_median` | Taban çizgisi eğimi (pozitif: sağa aşağı); satır içi kalıntı MAD'ı |
| Sayfa | `used_lines`, `used_frac`, `first/last_used_line`, `left/right_margin_mm`, `ink_bbox_*`, `ink_density`, `ink_mm2_per_used_line`, `mean_line_fill_frac`, `overflow_last_line` | Yazı alanı ve satır kullanımı |
| Kalite | `skew_deg`, `low_resolution`, `no_rules`, `rules_filled`, `code_box_found`, `overlay_masked_px`, `bridged_px`, `speckle_px`, `pen_colored_frac`, `pen_blue_share`, `dark_outside_roi_px` (ROI dışındaki bütün karanlık pikseller: kutu, başlık, kenar; "kesilen mürekkep" değil), `rule_spacing_off` (aralık 10,8 mm'den >0,8 mm sapıyor), `rule_grid_irregular` (çizgi aralıkları >%15 düzensiz). `rules_filled` = ızgarayla tamamlanan + atılan çizgi sayısı. `skew_deg` = **uygulanan düzeltme açısı** (+0,4° eğik sayfa için −0,4) | Her sayfada bayrak olarak döner |

## Sentetik sonuçlar (gerçek veri değil)

Gerçek değerler `synthetic.make_layout` içinden bilinir (ölçülen değerler mürekkep kalınlığını içerir: x-yüksekliği + 0,45 mm, taban −0,225 mm).

| Senaryo | x-yüksekliği (ölç. / gerçek) | Çizgi uzaklığı (mm) | Eğim (°) | Satır |
|---|---|---|---|---|
| Kolay (150 dpi, mavi kalem, eğiklik 0,4°) | 3,43 / 3,45 | 0,69 / 0,61 | 0,26 / 0,30 | 8 / 8 |
| Zor (200 dpi, kurşun kalem, JPEG 40, gürültü, eğiklik −0,5°, 1 satır atlanmış, titrek taban) | 3,01 / 2,85 | 1,77 / 1,84 | −0,59 / −0,60 | 8 / 8 |

Aynı sayfa farklı koşullarda (`seed=2`, gerçek mürekkep x-yüksekliği 3,45 mm, taban uzaklığı 0,73 mm, eğim 0,2°):

| Koşul | x-yük. (mm) | Taban uzaklığı (mm) | Eğim (°) | Dalgalanma (mm) | Sol boşluk (mm) | Satır |
|---|---|---|---|---|---|---|
| 150 dpi (referans) | 3,39 | 0,84 | 0,13 | 0,25 | 21,7 | 8 |
| 200 dpi → 150 | 3,39 | 0,76 | 0,16 | 0,24 | 21,7 | 8 |
| 300 dpi → 150 | 3,47 | 0,77 | 0,17 | 0,22 | 21,8 | 8 |
| kurşun kalem | 3,39 | 0,92 | 0,14 | 0,25 | 21,7 | 8 |
| siyah kalem | 3,56 | 0,76 | 0,12 | 0,25 | 21,7 | 8 |
| JPEG 40 + gürültü + gradyan | 3,39 | 0,84 | 0,08 | 0,25 | 21,7 | 8 |

Okuma: 150 dpi'de 1 piksel = 0,17 mm; x-yüksekliği farkları (±0,1–0,2 mm) çoğunlukla bu nicemlemedir. Sayfa kullanımı ve satır sayısı koşullardan etkilenmedi; eğim ve taban uzaklığı ±0,1° ve ±0,1 mm dalgalandı. `ink_density` kalem kalınlığına duyarlı (kurşun 0,014, siyah 0,020, mavi 0,017: tek başına karşılaştırılmamalı).

Görseller (sentetik): `docs/el_yazisi_prototip/sentetik_kolay.png`, `sentetik_zor.png` (önişlenmiş sayfa, maskeler, satırlar ve taban çizgileri, özellik tablosu).

**Hook sınırı:** `docs/el_yazisi_prototip/` ve `docs/el_yazisi_ornek_rapor/` altına konan ikili dosyaların içeriği taranmaz (yalnız sentetik görsellere izin verilir); bu klasörlere gerçek tarama konulmamalıdır.

## Bu sürümde bulunup düzeltilen sorunlar (sentetik testlerden)
- Telif satırı ROI'ye giriyordu → metin katmanı kutuları (XXX ve telif satırı) birlikte maskeleniyor (`overlay_boxes`).
- Çizgi uçları/basamaklı kırık parçalar el yazısı sanılıyordu (200 dpi'de 8 yerine 12–19 "kullanılan satır") → çizgi bandı tümüyle maskeleniyor, kesişen harfler köprüleniyor; en az 2 mm² mürekkepli bant "satır" sayılıyor.
- Soluk çizgi + JPEG 40'ta 23 çizgiden 14'ü bulunuyordu, eksik çizgi bütün satır atamasını kaydırıyordu → çizgi için daha izin verici eşik (200) ve düzenli ızgarayla tamamlama (`rules_filled` bayrağı).
- **Doğrulayıcı bulguları (2026-11-25, `docs/dogrulama/2026-11-25-el-yazisi-prototip.md`):** (a) 56–70 mm genişliğindeki kod kutusunun üst/alt kenarı çizgi sayılıp satır indekslerini 2 kaydırıyordu (sessiz) → bir bant sayfa genişliğinin ≥ %50'sini kaplamalı; geniş kutulu testler eklendi; (b) yol koruması `MyDrive`, `/content/drive`, `gdrive` yollarını kaçırıyordu → genişletildi ve test edildi; (c) totoloji assert (`hw & box_mask == 0`) yerine gerçek vuruş maskesinden 3 px uzak piksel (sızıntı) ölçümü, eğiklik işareti testi, x-yüksekliği toleransı %15 → %10, eksik çizgi tamamlama uçtan uca test; (d) `regularize` sahte yarım aralıklı çizgi ve bölünmüş çizgide yanlış ızgara kuruyordu → aralık medyandan, ızgaraya uymayan çizgi atılır, bulunan çizgilerin y'si korunur; (e) `roi_cut_ink_px` yanıltıcı adı `dark_outside_roi_px`; float `overlay_boxes` kabul edilir; hook ikili dosyaları reddeder.

## Sınırlamalar (açık)
1. **Sentetik ≠ gerçek.** Sentetik harfler ayrık ve düzenli; gerçek el yazısı bitişik, eğik, üzeri çizili, çizgiye değen ve renk/kalınlık açısından çok değişken. Yukarıdaki sayılar kod doğruluğunu gösterir, gerçek sayfadaki doğruluğu değil.
2. **Bileşen ≠ harf.** Bitişik yazıda bir bileşen birden çok harf; "gövde bileşenleri" süzgeci ve x-yüksekliği gerçek sayfada başarısız olabilir. Planlanan profil tabanlı x-yüksekliği (A5.1 b) henüz uygulanmadı; gerçek sayfada karşılaştırılacak.
3. **Çizgi bandı maskesi** bandın (≈ 0,9 mm) tamamını siler; çizgiye oturan harflerin alt kenarı kırpılabilir, taban çizgisi uzaklığı hafif yukarı kayar (köprüleme yalnız çizgiyi kesen vuruşları kurtarır). Gerçek sayfada kayıp miktarı ölçülmedi.
4. **Düzenli çizgi varsayımı** (eksik çizgiyi ızgarayla tamamlama) tek basılı form içindir; tüm sayfalarda doğrulanmadı.
5. **Kod kutusu** "içi boş büyük çerçeve" kuralıyla bulunur; gerçek kutu soluksa ya da el yazısıyla birleşmişse kaçabilir (`code_box_found=False` bayrağı).
6. **XXX / telif satırı** PDF metin katmanından gelir; telefon fotoğrafında bu katman olmaz (fotoğraf hattı ayrı iş).
7. Mürekkep eşiği kurşun kalem ve çok soluk mürekkep için gerçek sayfada denenmedi; renkli sayfa/gri sayfa ayrımı yalnız `pen_colored_frac` ile bayraklanır.
8. **Kurşun kalem + JPEG 40'ta mürekkep kaybı:** el yazısı maskesi gerçek piksellerin ≈ %22–26'sını kaçırıyor (ölçülen/gerçek ≈ 0,77), temiz sayfada ≈ 1,09 (köprü şişmesi). x-yüksekliği ve eğim korunsa da `ink_density`, `ink_mm2_per_used_line` bu koşullarda düşük çıkar.
9. **Çizgi ızgarası sınırları:** baştaki/sondaki eksik çizgi tamamlanmaz; ızgaraya uymayan (≥ 0,15 aralık) çizgiler atılır; eksik çizgi sayısı max(3, bulunanların %30'u)'nu aşarsa tamamlama yapılmaz; çok bozuk çizgi kümelerinde (örn. bir sürü sahte yatay çizgi) bayrak (`rule_grid_irregular`) dışında koruma yok. Gerçek kod kutusu genişliği EDA'da ölçülmedi (sentetik 50 mm); ≥ %50 genişlik kuralı gerçek sayfada sınanacak.
10. 150 dpi nicemleme ±0,17 mm; küçük harfte göreli hata büyük. 200/300 dpi ile duyarlılık testi gerçek sayfada yapılacak (kararlaştırıldı: çalışma 150 dpi).
11. Kapsam dışı: kelime aralığı, okunabilirlik, harf eğimi, `Rating`.

## Kabul ölçütleri (taslak, **kesinleştirilmedi**)

Plan §A3/A5/A6/A7'den; gerçek sayfa pilotundan ve kullanıcı onayından sonra donacak. "Prototip" sütunu yalnız sentetik durumdur.

| Alan | Ölçüt (taslak) | Prototip (sentetik) |
|---|---|---|
| Ölçek | Çizgi aralığı ≥ %98 sayfada ±%2 (10,8 mm) | 10,84 mm (≈ %0,3 sapma); gerçek sayfada ölçülmedi |
| Eğiklik | Düzeltme sonrası |açı| ≤ 0,1° (≈ 0,26 mm / satır) | Geri kazanım ±0,1° içinde |
| Çizgi / mürekkep maskesi | IoU ≥ 0,90 (elle işaretli) | Ölçülmedi (elle işaretleme yok); testlerde maske/gerçek piksel oranı 0,85–1,25 (temiz sayfada ≈ 1,09) ve gerçek vuruşlardan 3 px uzak piksel < %1 |
| Kod kutusu, XXX | Bulma oranı; ilk satırda harf kaybı ≤ %2 | Sentetikte bulundu (50–70 mm kutu); kutu/XXX/telif sızıntısı testte < %1, doğrulayıcının bağımsız ölçümünde 0 piksel |
| Satır sayısı | Uyum ≥ %95 | 8/8 (sentetik); gerçek sayfada ölçülmedi |
| Taban çizgisi | Medyan hata ≤ 0,5 mm | 0,02–0,19 mm (sentetik, koşula göre; kurşun kalemde en büyük) |
| x-yüksekliği | Medyan hata ≤ %10 | %0,6 ve %5,6 (sentetik) |
| Çözünürlük/kalem duyarlılığı | Spearman ≥ 0,90; medyan fark ≤ %5; kayma ≤ IQR'nin %25'i | Tek sayfa, sıra korunumu sentetik testte geçti; istatistik yok |
| dpi–sınıf karışıklığı | Eşdeğerlik: %90 GA ±0,2 SD içinde | Gerçek veri gerekli |
| Görev/zaman varsayımı (910 öğrenci) | Köşegen farkı ≥ 0,15; başlık uyumu ≥ %98 | Gerçek veri gerekli |

## Sıradaki adım
1. **İzin yanıtı** (FD-LEX / Mercator-Institut): gelmeden gerçek sayfaya dokunulmaz.
2. İzin sonrası **10–20 sayfalık pilot**: PyMuPDF'ten (yerel) sayfa + metin katmanı kutuları → `analyze_page` → görsel inceleme (çıktılar yerel, commit'e girmez). Pilotta özellikle: çizgi bandı kaybı, bileşen/harf ilişkisi, kod kutusu bulma, soluk/gri/ikili sayfalar, 150/200/300 dpi farkı.
3. Pilot sonucuna göre özellik tanımları (x-yüksekliği yöntemi) ve eşikler güncellenir; ardından plan A1 (kayıpsız PNG çıkarma, manifest, bölme) ve A3 elle işaretleme.
