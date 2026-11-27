# DiaGraMo: veri hazırlama ve deneysel model geliştirme

Tarih: 2026-11-27. Önceki aşama: `docs/el_yazisi_diagramo_eda.md` (EDA, etiketler, prototip). Bu belge gerçek veri üzerindeki deneyleri ve ölçülebilir sonuçları içerir.
Veri, görüntüler, özellik/etiket tabloları ve raporlar **yerel** (`data/handwriting/diagramo/`, git dışı). Etiketler: **[ölçüldü]** bu çalışmada hesaplandı; **[varsayım]** doğrulanmamış varsayım.

## 0. Sonuç özeti

- **Veri seti:** 525 kullanılabilir yazma kaydı (dikte 259, kopya 266 geçerli hedefli), 267 çocuk, 35 okul; hepsi koordinattan PNG'ye dönüştürüldü (iki görünüm: tablet tuvali ve kırpılmış).
- **Hedefler:** HLS'nin üç bağımsız maddesi (sayfa düzeni, harf biçimi, düzeltmeler; 1–5 tam sayı); toplam puan, okunabilirlik ve çaba kullanılmadı.
- **Özellikler:** görüntüden 43 geometrik özellik; koordinatlardan doğrudan hesaplananlarla doğrulandı (kutu boyutları ρ = 1,00, satır sayısı %88 aynı).
- **İlişkiler (eğitim bölümü, okul-içi ve kısmi korelasyonlarla kontrol edilmiş):** yazı boyutu ve taban dalgalanması sayfa düzeni ve harf biçimiyle ρ ≈ 0,4–0,65; kalın/üst üste binmiş mürekkep ve karalama özellikleri düzeltmelerle ρ ≈ 0,4–0,45.
- **Model A (geometrik özellik):** test kümesinde (bir kez kullanıldı) QWK **0,41** (sayfa düzeni), **0,38** (harf biçimi), **0,40** (düzeltmeler); medyan baseline QWK 0. Güven aralıkları geniş (örn. 0,26–0,49).
- **Model B (ResNet18 sabit gömme):** test QWK **0,33 / 0,19 / 0,09**: Model A'dan zayıf; CNN eğitimi/ince ayar yapılmadı.
- **Klinik grup:** `group` ile disgrafi bayrağı birebir aynı değil (geliştirme kümesinde 4/227 farklı); yalnız şehir bilgisi `group`'u AUC 0,98 ile tahmin ediyor, geometrik özellikler AUC 0,58: **klinik sınıflandırma ertelendi**.
- **Uyarı:** modeller render ayarlarına duyarlı (çizgi kalınlığını 3 → 5 px yapınca harf biçimi QWK'si 0,56 → 0,13): gerçek fotoğrafa aktarım doğrulanmadı. Render rastgeleleştirmeli eğitim (yalnız eğitim kümesinde) en kötü durumu 0,13 → 0,51'e çıkardı (val).
- **Model, deneysel tahmindir;** gerçek uzman değerlendirmesi ya da klinik tanı modeli değildir.

## 1. Veri seti stratejisi

DiaGraMo ana el yazısı veri seti. **FD-LEX Scriptoria ve Malaysian pasif/arşiv** (dosya ve kod silinmedi: `src/handwriting/` önceki hat, `docs/fd_lex_*`, `docs/handwriting_dataset_analysis.md`, `docs/plan_el_yazisi.md` ve ilgili testler yerinde). Çizim ve konuşma modüllerine, diğer veri setleriyle entegrasyona dokunulmadı.
Akademik dayanak: kullanıcı kararı (araştırma amaçlı kullanım için yeterli); veri setinin sınırlamaları `docs/el_yazisi_diagramo_eda.md` ve aşağıda.

## 2. Koordinat → görüntü dönüşümü

Mevcut `render.py` kullanıldı (`src/handwriting/diagramo/dataset.py`). Her kayıt iki görünümde 4 piksel/tablet birimi ve 3 piksel çizgi kalınlığıyla üretildi:
`processed/images/tablet/` (tablet etkin alanı 348,16 x 203,2 tb tam tuval: yazının tablet üzerindeki konumu ve boyutu korunur; 1393 x 813 px) ve `processed/images/crop/` (yazı sınırlarına kırpılmış, 8 tb kenarlık).
En-boy oranı, yazı boyutu ve mekânsal ilişkiler korunur (ölçekleme yok, kayıtlar bağımsız).

**Kırpmanın sayfa düzeni değerlendirmesine etkisi [ölçüldü]:** kâğıdın tablet üzerindeki konumu ve boyutu veri setinde **yok**; bu yüzden "orijinal yazma alanı" yalnız tablet alanı olarak korunabiliyor (kâğıt kenarları değil). Model A'yı üç özellik kümesiyle denedik (geliştirme: CV + val, seçim puanı):

| hedef | config | bayraklilar_cikarildi | crop_oznitelikleri | extra_content_cikarildi | tablet_konumsuz | tablet_tum |
|---|---|---|---|---|---|---|
| alter | OL_secilen_C0.3 | 0.330 | 0.394 | 0.325 | 0.407 | 0.360 |
| alter | RF_tum | 0.340 | 0.376 | 0.340 | 0.404 | 0.402 |
| layout | OL_secilen_C0.3 | 0.519 | 0.534 | 0.538 | 0.554 | 0.547 |
| layout | RF_tum | 0.529 | 0.548 | 0.528 | 0.570 | 0.551 |
| letter | OL_secilen_C0.3 | 0.538 | 0.504 | 0.532 | 0.536 | 0.570 |
| letter | RF_tum | 0.541 | 0.554 | 0.537 | 0.559 | 0.556 |

Mutlak konum/kenar boşluğu özelliklerini çıkarmak (tablet_konumsuz) ya da yalnız kırpılmış görüntüden hesaplanan özellikleri kullanmak sonucu bozmadı (seçim puanı farkı −0,07 … +0,05). Yani bu etiketler için kırpma, sayfa düzeni derecelendirmesinin ihtiyaç duyduğu bilgiyi yok etmiyor; ama bu, kâğıt kenar boşluklarının önemsiz olduğu anlamına gelmez (kâğıt konumu bilinmiyor [varsayım]).
Kırpılmış görüntüler Model B'de de benzer sonuç verdi (tablet ile kırpma arasında seçim puanı farkı ±0,06).

**Birim:** README koordinat birimini yazmıyor; mm olduğu yalnız dolaylı (hız, satır aralığı, tablet boyutu). Bu yüzden özellikler **tb (tablet birimi)** ya da oran olarak raporlandı; "doğrulanmış mm" iddiası yok.

**`extra_content` işaretli kayıtlar (yazma görevlerinde 38; kullanılabilir 525'te 33) [ölçüldü + görsel]:** 12 örnek görsel incelendi: tarih/imza gibi ek yazı, kâğıt dışı lekeler, köşede spiral/çizim, yoğun karalama ve metin üzerine siyah doldurma. Bunlar aynı zamanda **daha kötü HLS puanı** almış (düzeltmeler ort. 3,64 vs 2,87, Mann–Whitney p < 0,001; harf biçimi 3,52 vs 3,03; sayfa düzeni 2,79 vs 2,45) ve daha yüksek yazı kutusu yüksekliği (medyan 155 vs 69 tb). Karar: **kullanılabilir, bayraklı** (hedefleri geçerli; ayıklamak "düzeltmeler" ile ilişkili gerçek bilgiyi atardı); duyarlılık analizi (bayraklıları çıkarmak) sonucu fazla değiştirmedi (yukarıdaki tablo, QWK farkı ≤ 0,07, "düzeltmeler" hedefinde daha düşük). Dışlanan: `not_complete` (1 kayıt). Dağılım: 28 eğitim, 4 val, 1 test.

Kalite kontrol sonrası: 530 yazma kaydı → 526 hedefli → **525 kullanılabilir**; hepsi PNG'ye dönüştürüldü. **Manifest:** `manifests/images.csv` (katılımcı, görev, görüntü yolları, SVC yolu, tuval boyutları, koordinat referans niceliklerini, bayraklar, üç hedef ve meta veri: sınıf, yaş, cinsiyet, okul, şehir, toplama yeri, grup, tanı bayrakları).

## 3. Hedef değişkenler [ölçüldü]

HLS maddeleri **1–5 tam sayı** (kod kitabıyla uyumlu; ondalık değer yok). Dikte kayıtları `hls_dictat_*`, kopya kayıtları `hls_transcript_*` ile eşleşir; görevi olmayan çocuklarda HLS değeri yok (0 uyumsuzluk). Madde yönleri (kod kitabı): sayfa düzeni 1 = çok iyi düzen … 5 = çok kötü; harf biçimi 1 = iyi biçimli … 5 = kötü biçimli; düzeltmeler 1 = ek öğe yok … 5 = çoğu kelimede ek öğe.

| aile | hedef | geçerli | eksik | d1 | d2 | d3 | d4 | d5 | ort |
|---|---|---|---|---|---|---|---|---|---|
| copy | sayfa düzeni (c) | 266 | 0 | 22 | 120 | 84 | 28 | 12 | 2.580 |
| copy | harf biçimi (d) | 266 | 0 | 13 | 57 | 101 | 71 | 24 | 3.140 |
| copy | düzeltmeler (e) | 266 | 0 | 16 | 105 | 72 | 43 | 30 | 2.870 |
| dictation | sayfa düzeni (c) | 259 | 0 | 35 | 122 | 79 | 20 | 3 | 2.360 |
| dictation | harf biçimi (d) | 259 | 0 | 16 | 68 | 99 | 57 | 19 | 2.980 |
| dictation | düzeltmeler (e) | 259 | 0 | 3 | 97 | 93 | 39 | 27 | 2.960 |

Notlar: uç sınıflar seyrek (sayfa düzeni 5: dikte 3, harf biçimi 1: 13–16, düzeltmeler 1: dikte 3); maddeler birbiriyle ilişkili (dikte: düzen–harf ρ = 0,63, harf–düzeltme 0,56, düzen–düzeltme 0,44) ama ayrı hedeflerdir; aynı maddenin dikte ve kopya puanları orta düzeyde ilişkili (0,51–0,68). Derecelendirici kimliği ve güvenirliği **belirtilmemiş**.

## 4. Geometrik özellikler

Kod: `geom.py` (kural çizgisiz görüntüde satır bölütleme, x-yüksekliği/taban çizgisi, bileşenler, iskelet düğümleri, kalınlık ölçüleri). Mevcut Scriptoria hattındaki kavramlar (x-yüksekliği, taban çizgisi eğimi/dalgalanması, sayfa kullanımı, bileşen boyutu) yeniden kullanıldı; satır bölütleme çizgisiz görüntü için yeniden yazıldı (Scriptoria hattı basılı kâğıt çizgisine dayanıyordu).
43 özellik (46 sütundan, ≥ %90 dolu ve ≥ 6 farklı değerli olanlar); girdide hız, basınç, zaman, vuruş sırası **yoktur**.

| Aile | Özellikler | İlişkili olabileceği HLS maddesi (hipotez; §5 test eder) |
|---|---|---|
| Boyut ve değişkenlik | `xh_tb`, `xh_over_pitch`, `xh_cv_lines`, `comp_h_med_tb`, `comp_h_iqr_ratio`, `comp_w_med_tb`, `n_comps` | harf biçimi, sayfa düzeni |
| Satır eğimi, hizalama | `slope_med_deg`, `slope_abs_med_deg`, `slope_sd_deg`, `wobble_med_tb`, `wobble_over_xh`, `pitch_cv`, `left_edge_sd_over_xh`, `right_edge_sd_over_width`, `line_len_*` | sayfa düzeni |
| Aralık (kelime/harf, bileşenler arası boşluk) | `gap_med_over_xh`, `gap_cv`, `wide_gap_share` | sayfa düzeni, harf biçimi (**güvenilirlik sınırlı**: bitişik yazıda kelime/harf ayrımı yok) |
| Kesişim, örtüşme | `junction_density`, `valley_ink_frac`, `tall_comp_frac` | düzeltmeler, sayfa düzeni |
| Karalama / düzeltme görselleri | `thick_frac`, `blob_frac`, `largest_blob_tb2`, `ink_area_tb2`, `skel_len_tb`, `ink_per_line_tb2` | düzeltmeler |
| Alan kullanımı | `bbox_*`, `rbbox_*`, kenar boşlukları (tablet), `rbbox_area_frac`, `n_lines`, `pitch_tb` | sayfa düzeni |

**Koordinatlarla doğrulama [ölçüldü]:** aynı kayıtların koordinatlarından doğrudan hesaplanan statik nicelikler görüntü özellikleriyle karşılaştırıldı (n = 525):

| özellik | n | mae | median_err | spearman |
|---|---|---|---|---|
| yazı kutusu genişliği (tb) | 525.000 | 0.658 | 0.680 | 1.000 |
| yazı kutusu yüksekliği (tb) | 525.000 | 0.596 | 0.590 | 1.000 |
| sol kenar (tb) | 525.000 | 0.343 | -0.340 | 0.998 |
| iskelet uzunluğu / koordinat yol uzunluğu | 525.000 | 1705.488 | -1564.913 | 0.981 |
| satır sayısı | 525.000 | 0.223 | 0.000 | 0.930 |
| satır aralığı (tb) | 525.000 | 0.425 | 0.000 | 0.817 |

Kutu boyutları çizgi kalınlığı kadar (≈ 0,6 tb) şişer; iskelet uzunluğu koordinat yol uzunluğunun medyan %67'si (üst üste binen yollar ve iskeletleme), sıralaması aynı (ρ = 0,98); satır sayısı %88 aynı, %93+ ±1 (karalamalı sayfalarda bölütleme hatası). Satır aralığı koordinatlarla ρ = 0,82. **Bilinen sınırlama:** `n_comps`, `thick_frac`, `blob_frac`, `junction_density`, `gap_*` çizgi kalınlığına ve çözünürlüğe duyarlı (§7).

## 5. İstatistiksel analiz (yalnız eğitim bölümü: 369 kayıt, 187 çocuk, 23 okul)

Yöntem: Spearman ρ; **okul-küme bootstrap %95 GA** (300 tekrar); çocuk düzeyinde Fisher GA ayrıca CSV'de; **kısmi ρ** (sınıf, yaş, cinsiyet, görev sürümü sıra-kontrollü); **okul-içi ρ** (okul ortalaması çıkarılmış); Benjamini–Hochberg q (258 test birlikte). Dikte ve kopya ayrı analiz edildi (her çocuk bir ailede bir kez: bağımsız çocuklar; aynı okulun kümelenmesi bootstrap ve okul-içi ρ ile ele alındı). Metin uzunluğu veri setinde yok; metin sınıfa göre sabit olduğundan görev sürümü (3/4) kovaryat olarak kullanıldı.

**Özet:** 258 test; q<0.05: 196; q<0.10: 204; |rho|>=0.3: 100; |rho|>=0.5: 7

| hedef | aile | özellik | n | rho | GA_okul | kısmi_rho | okul_içi_rho | q |
|---|---|---|---|---|---|---|---|---|
| alter | copy | thick_frac | 184 | 0.450 | 0.34…0.56 | 0.440 | 0.420 | 1.7e-09 |
| alter | copy | largest_blob_tb2 | 184 | 0.420 | 0.31…0.51 | 0.400 | 0.380 | 2.6e-08 |
| alter | copy | blob_frac | 184 | 0.420 | 0.30…0.53 | 0.400 | 0.380 | 3.1e-08 |
| alter | copy | ink_area_tb2 | 184 | 0.400 | 0.26…0.51 | 0.450 | 0.340 | 9.4e-08 |
| alter | dictation | blob_frac | 179 | 0.440 | 0.28…0.58 | 0.450 | 0.470 | 9.6e-09 |
| alter | dictation | thick_frac | 179 | 0.440 | 0.27…0.58 | 0.450 | 0.470 | 1.2e-08 |
| alter | dictation | largest_blob_tb2 | 179 | 0.370 | 0.24…0.52 | 0.380 | 0.400 | 1.6e-06 |
| alter | dictation | ink_area_tb2 | 179 | 0.290 | 0.17…0.43 | 0.310 | 0.350 | 2.1e-04 |
| layout | copy | xh_tb | 184 | 0.650 | 0.55…0.74 | 0.620 | 0.580 | 6.6e-21 |
| layout | copy | wobble_med_tb | 184 | 0.640 | 0.54…0.70 | 0.620 | 0.560 | 4.2e-20 |
| layout | copy | xh_over_pitch | 184 | 0.510 | 0.37…0.62 | 0.470 | 0.470 | 7.0e-12 |
| layout | copy | skel_len_tb | 184 | 0.490 | 0.35…0.61 | 0.600 | 0.440 | 4.5e-11 |
| layout | dictation | wobble_med_tb | 179 | 0.530 | 0.43…0.65 | 0.520 | 0.540 | 9.5e-13 |
| layout | dictation | xh_tb | 179 | 0.480 | 0.38…0.61 | 0.460 | 0.470 | 1.3e-10 |
| layout | dictation | xh_over_pitch | 179 | 0.440 | 0.33…0.57 | 0.420 | 0.420 | 7.4e-09 |
| layout | dictation | skel_len_tb | 179 | 0.440 | 0.33…0.59 | 0.470 | 0.470 | 1.2e-08 |
| letter | copy | wobble_med_tb | 184 | 0.590 | 0.49…0.67 | 0.560 | 0.520 | 8.0e-17 |
| letter | copy | xh_tb | 184 | 0.560 | 0.43…0.67 | 0.510 | 0.480 | 6.4e-15 |
| letter | copy | xh_over_pitch | 184 | 0.460 | 0.31…0.57 | 0.410 | 0.380 | 1.3e-09 |
| letter | copy | n_comps | 184 | -0.440 | -0.56…-0.30 | -0.470 | -0.350 | 4.6e-09 |
| letter | dictation | wobble_med_tb | 179 | 0.510 | 0.41…0.62 | 0.480 | 0.500 | 1.4e-11 |
| letter | dictation | xh_tb | 179 | 0.490 | 0.35…0.61 | 0.450 | 0.430 | 1.2e-10 |
| letter | dictation | n_comps | 179 | -0.410 | -0.55…-0.26 | -0.450 | -0.340 | 7.3e-08 |
| letter | dictation | xh_over_pitch | 179 | 0.390 | 0.21…0.56 | 0.360 | 0.400 | 2.7e-07 |

- **Boyut/dalgalanma:** x-yüksekliği ve taban dalgalanması (tb) sayfa düzeni ve harf biçimiyle yüksek (ρ ≈ 0,4–0,65; okul-içi ve kısmi ρ aynı düzeyde): büyük ve dalgalı yazı daha yüksek (kötü yönlü) puan alıyor. Normalize hali (oran) daha zayıf (ρ ≈ 0,4–0,5).
- **Düzeltmeler:** kalın/üst üste binmiş mürekkep özellikleri (`thick_frac`, `blob_frac`, `largest_blob_tb2`) ρ ≈ 0,4–0,45.
- **Karıştırıcılar (eğitim):** cinsiyet harf biçimiyle (ρ = −0,24/−0,26; kızlar daha düşük puan), sınıf ve yaş ile ilişki ≈ 0 (|ρ| < 0,12); okul etkisi anlamlı (Kruskal p = 0,0001–0,03; düzeltmeler dikte hariç); `group` kopya görevi puanlarıyla ρ ≈ 0,32–0,38 (şehir/toplama yeri karıştırıcısı olabilir). Okul-içi ρ'ler marjinal ρ'lere yakın: ilişkiler okul farkıyla açıklanmıyor.
- **Yedeklilik (|ρ| > 0,85):** `thick_frac`~`blob_frac`; `skel_len_tb`~`ink_area_tb2`; `bbox_h`~`rbbox_h`~alt boşluk~alan oranı; `bbox_w`~`rbbox_w`~sağ boşluk; `left_margin_tb`~`left_margin_raw_tb`; `right_edge_sd`~`line_len_cv`; `gap_med`~`wide_gap_share`. Her kümeden hedefle en güçlü ilişkili tek temsilci seçildi.
- **Özellik seçimi (yalnız eğitim, her CV katında yeniden):** en az bir ailede BH q < 0,10 ve iki ailede işaret uyumu; sayfa düzeni 30, harf biçimi 28, düzeltmeler 26 özellik. İlişkisiz özellikler (örn. `slope_med_deg` işaretli eğim) modele alınmadı.
- Çoklu karşılaştırma: 258 testin 196'sı q < 0,05; özellikler birbirine bağlı olduğundan bu sayı bağımsız bulgu sayısı değildir.

## 6. Makine öğrenmesi deneyleri

**Bölme (özellik seçiminden önce, yalnız meta veriye göre, seed 42):** okul bazlı (aynı okul tek bölümde): train 187 çocuk / 23 okul, val 40 / 5, test 40 / 7 (kayıt: 369 / 78 / 78). Dengesizlik: sınıf ve grup dengesi için rastgele aday arama (hedeflere bakılmadı). `manifests/splits.csv` sha256: **`a0d7a267f57478ea6c8b878a07d70b699b5c07c47a9b7446f4a538b0b4014cd8`**. Genelleme sınırlaması: okul bazlı bölme uygulandı (35 okul, uygulanabilir); ancak tipik çocukların tamamı tek şehirden, val/test okul sayısı az (5 / 7), güven aralıkları geniş.

**Seçim kuralı (sonuçlardan önce yazıldı):** hedef başına yapılandırma, eğitimde okul-gruplu 5 katlı CV ortalama QWK'si ile val QWK'sinin ortalamasına göre; test kümesi yalnız son adımda, kilit dosyasıyla **bir kez** (ikinci kullanım kodla engelli).

### Model A: geometrik özellik tabanlı (girdi: özellikler + görev türü; cinsiyet/yaş/sınıf girdi değil)

Baseline (eğitim medyanı), Ordinal Logistic Regression (Frank–Hall; L2), Random Forest (regresyon + yuvarlama); her HLS maddesi için bağımsız model. Önişleme: medyan doldurma + normal dağılıma nicel dönüşüm (eğitimde öğrenilir).

| hedef | config | cv_mae | cv_qwk | cv_spearman | val_mae | val_qwk | val_spearman | n_ozellik | secim_puani |
|---|---|---|---|---|---|---|---|---|---|
| layout | baseline_medyan | 0.864 | -0.118 | -0.192 | 0.590 | 0.165 | 0.211 | 0 | 0.024 |
| layout | OL_secilen_C0.1 | 0.474 | 0.554 | 0.581 | 0.436 | 0.554 | 0.663 | 30 | 0.554 |
| layout | OL_secilen_C0.3 | 0.477 | 0.557 | 0.573 | 0.462 | 0.537 | 0.664 | 30 | 0.547 |
| layout | OL_tum_C0.03 | 0.474 | 0.532 | 0.589 | 0.397 | 0.552 | 0.657 | 43 | 0.542 |
| layout | RF_secilen | 0.461 | 0.579 | 0.612 | 0.410 | 0.530 | 0.617 | 30 | 0.554 |
| layout | RF_tum | 0.461 | 0.572 | 0.613 | 0.410 | 0.530 | 0.640 | 43 | 0.551 |
| letter | baseline_medyan | 0.762 | 0.000 |  | 0.692 | 0.000 |  | 0 | 0.000 |
| letter | OL_secilen_C0.1 | 0.561 | 0.560 | 0.605 | 0.513 | 0.572 | 0.623 | 28 | 0.566 |
| letter | OL_secilen_C0.3 | 0.558 | 0.578 | 0.609 | 0.513 | 0.561 | 0.606 | 28 | 0.570 |
| letter | OL_tum_C0.03 | 0.596 | 0.521 | 0.579 | 0.526 | 0.548 | 0.656 | 43 | 0.534 |
| letter | RF_secilen | 0.607 | 0.473 | 0.594 | 0.436 | 0.658 | 0.666 | 28 | 0.566 |
| letter | RF_tum | 0.610 | 0.480 | 0.593 | 0.474 | 0.633 | 0.669 | 43 | 0.556 |
| alter | baseline_medyan | 0.813 | 0.000 |  | 0.859 | 0.000 |  | 0 | 0.000 |
| alter | OL_secilen_C0.1 | 0.729 | 0.344 | 0.449 | 0.718 | 0.425 | 0.501 | 26 | 0.385 |
| alter | OL_secilen_C0.3 | 0.743 | 0.353 | 0.455 | 0.744 | 0.366 | 0.488 | 26 | 0.360 |
| alter | OL_tum_C0.03 | 0.732 | 0.344 | 0.436 | 0.718 | 0.378 | 0.471 | 43 | 0.361 |
| alter | RF_secilen | 0.710 | 0.390 | 0.441 | 0.756 | 0.318 | 0.426 | 26 | 0.354 |
| alter | RF_tum | 0.710 | 0.401 | 0.459 | 0.731 | 0.403 | 0.441 | 43 | 0.402 |

Seçilen: sayfa düzeni = RF (seçilmiş özellikler), harf biçimi = ordinal lojistik (C = 0,3), düzeltmeler = RF (tüm özellikler).

### Model B: görüntü tabanlı (ResNet18 ImageNet, sabit gömme; CNN eğitilmedi)

Tam çözünürlükte (yeniden boyutlandırma yok) tablet ya da kırpılmış görüntü → son katman ortalama + maksimum havuzlama (1024 boyut) → standartlaştırma + PCA (16/32/64) + ordinal lojistik. Veri artırma yok. En iyi üç yapılandırma:

| hedef | config | cv_mae | cv_qwk | val_mae | val_qwk | secim_puani |
|---|---|---|---|---|---|---|
| alter | B_crop_pca32_C0.1 | 0.772 | 0.228 | 0.821 | 0.268 | 0.248 |
| alter | B_tablet_pca32_C0.1 | 0.767 | 0.244 | 0.821 | 0.190 | 0.217 |
| alter | B_tablet_pca64_C0.1 | 0.770 | 0.266 | 0.808 | 0.148 | 0.207 |
| layout | B_tablet_pca16_C0.1 | 0.520 | 0.482 | 0.436 | 0.496 | 0.489 |
| layout | B_crop_pca32_C0.1 | 0.531 | 0.482 | 0.474 | 0.468 | 0.475 |
| layout | B_tablet_pca64_C0.1 | 0.528 | 0.476 | 0.474 | 0.415 | 0.445 |
| letter | B_tablet_pca64_C0.1 | 0.596 | 0.473 | 0.577 | 0.525 | 0.499 |
| letter | B_tablet_pca16_C0.1 | 0.645 | 0.390 | 0.551 | 0.522 | 0.456 |
| letter | B_tablet_pca32_C0.1 | 0.640 | 0.418 | 0.564 | 0.480 | 0.449 |

Seçilen: sayfa düzeni = tablet PCA16, harf biçimi = tablet PCA64, düzeltmeler = kırpılmış PCA32. Model B tüm hedeflerde Model A'nın gerisinde (seçilen yapılandırmaların CV QWK'si 0,23–0,48 vs 0,35–0,58); yalnız yaklaşık 370 eğitim kaydı ve alan (karalama/kalınlık) bilgisi için hazır özellikler zayıf.

### Test sonuçları (bir kez; train+val'de eğitildi; okul-küme bootstrap %95 GA)

| model | hedef | config | n | mae | qwk | qwk_ci_lo | qwk_ci_hi | spearman | baseline_mae |
|---|---|---|---|---|---|---|---|---|---|
| A (geometrik özellik) | alter | RF_tum | 78 | 0.692 | 0.398 | 0.132 | 0.507 | 0.503 | 0.885 |
| A (geometrik özellik) | layout | RF_secilen | 78 | 0.564 | 0.410 | 0.264 | 0.488 | 0.647 | 0.551 |
| A (geometrik özellik) | letter | OL_secilen_C0.3 | 78 | 0.667 | 0.376 | 0.201 | 0.571 | 0.577 | 0.795 |
| B (CNN gömme) | alter | B_crop_pca32_C0.1 | 78 | 0.795 | 0.093 | 0.026 | 0.191 | 0.427 |  |
| B (CNN gömme) | layout | B_tablet_pca16_C0.1 | 78 | 0.551 | 0.328 | 0.143 | 0.441 | 0.502 |  |
| B (CNN gömme) | letter | B_tablet_pca64_C0.1 | 78 | 0.769 | 0.189 | 0.041 | 0.503 | 0.465 |  |

- Model A üç maddede de baseline'ın (QWK 0) üzerinde: QWK 0,38–0,41, Spearman 0,50–0,65. **MAE:** harf biçimi ve düzeltmelerde baseline'dan iyi (0,67 vs 0,80; 0,69 vs 0,89), **sayfa düzeninde baseline ile aynı** (0,56 vs 0,55): sınıf dağılımı çarpık (çoğu puan 2) olduğundan "her zaman 2" tahmini düşük MAE verir; modelin katkısı sıralamadadır (Spearman 0,65), mutlak hata azaltmada değil.
- Test QWK'si geliştirme CV'sinden (0,55 / 0,57 / 0,35–0,40) düşük: küçük test (78 kayıt, 40 çocuk, 7 okul) ve geniş GA (alt sınırlar 0,13–0,26).
- Model B daha düşük ve daha belirsiz (QWK 0,09–0,33).

Karışıklık matrisleri (Model A, test; satır = gerçek, sütun = tahmin; uç sınıflar hiç tahmin edilmiyor, orta sınıflara büzülme var):

|  | tahmin 1 | tahmin 2 | tahmin 3 | tahmin 4 | tahmin 5 |
|---|---|---|---|---|---|
| gerçek 1 | 0 | 18 | 1 | 0 | 0 |
| gerçek 2 | 0 | 23 | 15 | 0 | 0 |
| gerçek 3 | 0 | 7 | 11 | 0 | 0 |
| gerçek 4 | 0 | 0 | 2 | 1 | 0 |
| gerçek 5 | 0 | 0 | 0 | 0 | 0 |
|  | tahmin 1 | tahmin 2 | tahmin 3 | tahmin 4 | tahmin 5 |
|---|---|---|---|---|---|
| gerçek 1 | 0 | 3 | 5 | 0 | 0 |
| gerçek 2 | 0 | 12 | 17 | 0 | 0 |
| gerçek 3 | 0 | 2 | 17 | 5 | 2 |
| gerçek 4 | 0 | 0 | 6 | 7 | 0 |
| gerçek 5 | 0 | 1 | 1 | 0 | 0 |
|  | tahmin 1 | tahmin 2 | tahmin 3 | tahmin 4 | tahmin 5 |
|---|---|---|---|---|---|
| gerçek 1 | 0 | 5 | 2 | 0 | 0 |
| gerçek 2 | 0 | 13 | 28 | 0 | 0 |
| gerçek 3 | 0 | 2 | 13 | 4 | 0 |
| gerçek 4 | 0 | 2 | 3 | 3 | 0 |
| gerçek 5 | 0 | 0 | 1 | 2 | 0 |

### Model karşılaştırması
Model A (özellik tabanlı) > Model B (gömme): açıklanabilir, daha az veriyle daha iyi, her tahmin özelliklerle ilişkilendirilebilir. Model B, ince ayar ya da görev-uyumlu ön eğitimle iyileştirilebilir ama mevcut örnek sayısında (≈ 190 çocuk eğitimde) büyük ağ eğitimi önerilmez.

## 7. Alan farkı: render ayarlarına duyarlılık [ölçüldü, val]

Gerçek fotoğrafta kalem kalınlığı ve çözünürlük farklı olacağından, aynı val çocukları farklı render ayarlarında (çizgi kalınlığı 2/3/5 px, 3/4/6 px/tb) yeniden üretilip train'de eğitilmiş Model A ile değerlendirildi (val QWK):

| variant | alter | layout | letter |
|---|---|---|---|
| dusuk_coz(3ppu,2px) | 0.350 | 0.491 | 0.534 |
| ince(2px) | 0.299 | 0.542 | 0.530 |
| kalin(5px) | 0.117 | 0.482 | 0.127 |
| orijinal(3px,4ppu) | 0.403 | 0.530 | 0.561 |
| yuksek_coz(6ppu,4px) | 0.236 | 0.540 | 0.397 |

Özelliklerin yalnız 24'ü (43 içinden) render değişimleri arasında kararlı (orijinal ↔ varyant Spearman ≥ 0,9); en kararsızlar: `blob_frac`, `comp_h_iqr_ratio`, `gap_med_over_xh`, `slope_med_deg`, `gap_cv`, `wobble_over_xh`. **Sayfa düzeni** ayarlar arasında göreli kararlı (0,48–0,54), **harf biçimi ve düzeltmeler çok duyarlı** (5 px kalınlıkta 0,13 / 0,12).

**Render rastgeleleştirme (veri artırma yalnız eğitim kümesinde, hedef etiketi değiştirmeyen):** eğitim görüntüleri 6 farklı render ayarında (2–5 px, 3–5 px/tb) üretilip özellikleriyle birlikte eğitime katıldı; val'de aynı 5 ayarla değerlendirme (QWK):

| hedef | egitim | dusuk_coz(3ppu,2px) | ince(2px) | kalin(5px) | orijinal(3px,4ppu) | yuksek_coz(6ppu,4px) |
|---|---|---|---|---|---|---|
| alter | render rastgeleleştirme (6 varyant) | 0.302 | 0.288 | 0.249 | 0.326 | 0.151 |
| alter | tek render (3px) | 0.350 | 0.299 | 0.117 | 0.403 | 0.236 |
| layout | render rastgeleleştirme (6 varyant) | 0.598 | 0.532 | 0.569 | 0.536 | 0.540 |
| layout | tek render (3px) | 0.491 | 0.542 | 0.482 | 0.530 | 0.540 |
| letter | render rastgeleleştirme (6 varyant) | 0.551 | 0.561 | 0.506 | 0.586 | 0.550 |
| letter | tek render (3px) | 0.534 | 0.530 | 0.127 | 0.561 | 0.397 |

Ortalama QWK sayfa düzeninde ve harf biçiminde arttı, düzeltmelerde hafif düştü; düzeltmelerde orijinal ayarda da kötüleşme var (0,40 → 0,33). En kötü ayardaki QWK: harf biçimi 0,13 → 0,51, sayfa düzeni 0,48 → 0,53, düzeltmeler 0,12 → 0,15 (hâlâ duyarlı). **Bu iyileştirme yalnız val üzerinde ölçüldü; test kümesi tekrar kullanılmadı;** sonraki sürümde varsayılan eğitim biçimi olarak önerilir.

## 8. Disgrafi ve klinik grup analizi (keşifsel; **sınıflandırma ertelendi**)

Geliştirme kümesi (train+val; test kullanılmadı), 227 çocuk (129 `group = 1`, 98 `group = 0`):

- **`group` ile disgrafi bayrağı aynı mı? [ölçüldü]** Hayır, birebir değil: 223/227 aynı; 4 çocukta farklı (1 çocuk `group = 0` ama disgrafi tanısı kayıtlı; 3 çocuk `group = 1` ama özel bakım kaydı "tanı sürüyor"). `group` kod kitabında "special_care'den uyarlanmış ölçüt" olarak tanımlı; uyarlama kuralı belirtilmemiş. Tanı bayrakları (tüm kullanılabilir 275 çocukta): disleksi 31, disortografi 10, diskalkuli 6, dispraksi 2.
- **Karıştırıcılar [ölçüldü]:** tipik 98 çocuğun **tamamı** `city1`; HD çocuklarının yalnız 5'i `city1`'de; 50 HD çocuğu danışma merkezinde (tipiklerde 0). **Yalnız şehir bilgisi `group`'u AUC = 0,98 ile ayırıyor.**
- **Geometrik özellikler tek başına:** okul-gruplu CV AUC (dikte, lojistik) **0,58**; şehir yoluyla 0,98. Özellik düzeyinde en ayırıcılar (tek değişkenli AUC 0,69–0,80) sayfa kullanımı/boyut özellikleridir (kutu boyutları, taban dalgalanması), ki bunlar toplama yeri/kâğıt konumu farklarını da yansıtabilir.
- **İki grubun birlikte bulunduğu okullar:** geliştirme kümesinde yalnız 3 okul (37 çocuk: 32 tipik, 5 HD); okul-içi AUC'ler yüksek (0,88–0,94; çoğunlukla mürekkep/çizgi uzunluğu) ama 4–5 HD çocuğa dayanıyor: güvenilir değil.
- **Karar:** katılımcı ve okul bazlı güvenilir bir klinik değerlendirme mümkün değil (HD/tipik karışık okul sayısı 3–5, şehir yoluyla sızıntı). Bu nedenle **keşifsel sınıflandırma modeli kurulmadı**; veri kaynağı farkından yararlanan yüksek doğruluk raporlanmadı. Klinik tanı modeli geliştirildiği iddia edilmez. Yapılabilecek: aynı kurumdan her iki grubu da içeren yeni veri; ya da kurum/şehir bilgisini kontrol eden tasarım.

## 9. Temsili uzman raporu

`python -m src.handwriting.diagramo.report_dg` (yerel `reports/` klasörü; gerçek çocuk yazısı görselleri içerir, git dışı). Örnek seçimi yalnız model tahminlerine göre (en düşük, orta, en yüksek tahmin toplamı; gerçek etiketlere bakılmadı); test kümesinden 3 yazı. Raporun bölümleri:
**A. Geometrik ölçümler** (görüntüden; tb ya da oran; eğitim bölümündeki aynı görevin dağılımına göre yüzdelik; %5 uç işareti; ≥ 100 yazı kuralı), **B. Deneysel model tahmini** (üç HLS maddesi: sınıf, sürekli değer, %80 aralık [CV kalıntılarından], geliştirme CV performansı; "uzman değerlendirmesi değildir"), **model tahminine katkıda bulunan özellikler** (tek özellikli occlusion: özellik eğitim medyanına çekilince tahmin değişimi), **C. incelenebilecek bölgeler** (görsel: satır taban çizgileri [turuncu = dalgalanma ≥ %10], kalın/üst üste binmiş bölgeler, çok uzun bileşenler, satır dışı mürekkep), **D. güvenilirlik ve sınırlamalar**.

Örnek (kopya görevi, 3. sınıf sürümü; kısaltılmış):

| Geometrik ölçüm (A) | Değer | Referans yüzdeliği |
|---|---|---|
| Yazı boyutu (x-yüksekliği) | 8,25 tb | 94. |
| Yazı boyutu / satır aralığı | 0,81 | 90. |
| Taban çizgisi dalgalanması / x-yüksekliği | 0,13 | 72. |
| Bileşenler arası boşluk (ortanca) | 4,23 | 99. (uç bölge: kontrol edin) |
| Kalın mürekkep payı | 0,006 | 71. |

| Deneysel tahmin (B; HLS yönü: 1 = iyi … 5 = kötü) | Sınıf | Sürekli | %80 aralık |
|---|---|---|---|
| Sayfa düzeni | 4 | 3,72 | 2,8–4,6 |
| Harf biçimi | 5 | 4,72 | 3,7–5,0 |
| Düzeltmeler | 4 | 3,83 | 2,7–5,0 |

Tahmine katkı (en yüksek 3): sayfa düzeni: `xh_tb` (8,25 vs eğitim medyanı 5,25), `wobble_med_tb`, `n_comps`; harf biçimi: `n_comps` (26 vs 66: az bileşen = yüksek puan yönünde), `xh_over_pitch`, `line_len_med_tb`; düzeltmeler: `tall_comp_frac`, `thick_frac`, `slope_abs_med_deg`. Bölge görseli yerelde.
**Ayrım:** A ölçümdür; B yalnız DiaGraMo'da öğrenilmiş deneysel bir tahmindir ve rapor bunu uzman değerlendirmesi gibi sunmaz. Gerçek fotoğrafta bağımsız doğrulama yapılana kadar sonuçlar "DiaGraMo üzerinde geliştirilmiş deneysel tahmin" olarak etiketlenir.

## 10. Sınırlamalar ve sonraki adımlar

**Sınırlamalar:** (1) tek veri seti, tek ülke/dil, 8–12 yaş, tablet üstünde kâğıt; (2) küçük örnek (187 eğitim çocuğu) ve küçük test; (3) HLS derecelendiricisi/güvenirliği belirtilmemiş; (4) üretilen görüntü ≠ gerçek fotoğraf (kâğıt çizgisi, kalem, gürültü, perspektif, sabit kalınlık): özelliklerin yarısına yakını render ayarlarına duyarlı; (5) birim belirsiz (tb); (6) kâğıt konumu/boyutu bilinmiyor; (7) `group` karıştırıcılı; (8) özellikler çok ilişkili ve seçim lenient (q < 0,10); (9) Spearman p/q değerleri okul kümelenmesini tam yansıtmaz (GA okul-küme bootstrap).

**Öneriler:**
1. Render rastgeleleştirmeli eğitimi varsayılan yapmak; gerçekçi render (kâğıt çizgisi, mürekkep, gürültü) eklemek.
2. Gerçek el yazısı fotoğraflarında (az sayıda uzman puanlı örnekle) bağımsız doğrulama: tahminlerin aktarılabilirliğini ölçmek (bu çalışmada yapılmadı).
3. HLS derecelendiricileri ve tanı kaynağı için yazarlarla iletişim; mümkünse madde başına derecelendirici sayısı ve uyumu.
4. Model A'yı kalınlıktan bağımsız özelliklerle sınırlamak ve duyarlı özellikleri (`n_comps`, `blob_frac`, boşluk özellikleri) kalınlık normalizasyonuyla yeniden tanımlamak.
5. Klinik grup analizi için kurum/şehir kontrollü yeni veri olmadan ilerlememek.

## 11. Tekrarlanabilirlik

Deney komutları `src/handwriting/diagramo/experiments.py` içinde (`python -X utf8 -m src.handwriting.diagramo.experiments <analysis|development_a|development_b|ablation|render|clinical|final_test>`). Bu belgedeki tablolar ilk olarak aynı mantığı kullanan geçici betiklerle üretildi; komutlar bu mantığın toplu hâlidir ve **yeniden çalıştırılarak doğrulanmadı** (`final_test` kilit nedeniyle zaten çalışmaz). Model B test değerlendirmesi de artık kilidi denetler (`cnn.final_test_emb`).
