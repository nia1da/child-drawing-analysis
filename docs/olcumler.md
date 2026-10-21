# Çizim ölçümleri

Çizim modülünün ölçümleri. Makine öğrenmesi yok, sadece görüntü işleme. Her ölçüm KIDO train bölümündeki
çizimlerden sınıf düzeyi (1–8) × görev (mutlu/üzgün) bazında normlara bağlanır ve raporda
"akranlarının X. yüzdelik diliminde" diye sunulur. Rapor betimleyicidir, tanı dili içermez.

| Grup | Parametre | Nasıl hesaplanır | Ne söyleyebilir |
|---|---|---|---|
| Kompozisyon | Doluluk oranı | Çizim piksellerinin tüm sayfaya oranı | Sayfayı ne kadar kullandığı |
| | Ağırlık merkezi (x, y) | Çizim piksellerinin ortalama konumu | Çizimin sayfada yoğunlaştığı yer |
| | Kapsayan kutu oranı | Çizimi çevreleyen en küçük dikdörtgenin sayfaya oranı | Köşede mi, sayfaya yayılmış mı |
| | Çeyrek dağılımı | Sayfayı 2×2 veya 3×3 böl, her bölgedeki doluluk | Mekânsal düzen |
| Renk | Farklı renk sayısı | Doygun piksellerde ton histogramı, eşiği geçen bölme sayısı | Renk çeşitliliği |
| | Renk entropisi | Ton histogramının entropisi | Renk dengesi |
| | Ortalama doygunluk | Çizim piksellerinin ortalama S değeri | Canlı mı, soluk/karakalem mi |
| | Koyu ton oranı | Çizim içinde V değeri düşük piksellerin oranı | Siyah ve koyu renk kullanımı |
| | Sıcak/soğuk oranı | Kırmızı-sarı tonların mavi-yeşil tonlara oranı | Paletin yönü |
| | Renklilik skoru | Hasler–Süsstrunk ölçütü | Genel renk canlılığı |
| | Boyama oranı | Renkle doldurulmuş alanların kontur alanlarına oranı | İçler boyanmış mı |
| Çizgi ve yapı | Kenar yoğunluğu | Canny kenar piksellerinin oranı | Detay ve karmaşıklık |
| | Toplam çizgi uzunluğu | Maskeyi iskeletleştir, piksel say | Ne kadar çizildiği |
| | Ortalama çizgi kalınlığı | Distance transform ile iskelet boyunca kalınlık | Kalem baskısı/araç tipi |
| | Bağlı bileşen sayısı | Maskedeki ayrı parçalar (çok küçükler hariç) | Ayrı öğe sayısı |

## Uygulanan ölçümler (ölçüm sürümü 3)

Tablodaki bütün ölçümler uygulandı (sürüm 1: ilk dilim, doluluk, renk sayısı, koyu ton; sürüm 2: geri kalanlar;
sürüm 3: renklilik ve kenar yoğunluğunun çizim piksellerine göre halleri).
Kod: `src/measurements/` (`mask.py`, `metrics.py`, `norms.py`), rapor `src/report.py`.
Görüntüler 512×362; bütün ölçümler kenarlardan 4 piksel kırpılmış sayfa (504×354) üzerinde.
Çizim yokken (boş maske) konum, doygunluk, koyu ton, boyama ve kalınlık tanımsızdır (`null`).

- **Çizim maskesi:** bir piksel çizime aittir, eğer V < 230 (kurşun kalem, siyah, koyu boya) ya da S > 30 (renkli)
  ise. Histerezis: V < 240 ya da S > 20 olan soluk pikseller, bu kesin eşikleri geçen bir parçaya bağlıysa katılır.
  8 pikselden küçük parçalar ve piksellerinin %90'ı kenara 10 pikselden yakın parçalar (tarama izleri) atılır.
  Eşiklerin ölçüldüğü veriler `mask.py` başında. Maske 24 çizimlik kontrol sayfasıyla onaylandı (2026-10-19;
  Drive `maske_kontrol/`; aday havuzu o zaman bütün bölümlerdi, seçilen 24 çizimin 21'i train, 3'ü val). Yeni
  çalıştırmalar (`python -m src.measurements.mask_check`) sadece train'den seçer ve `maske_kontrol_<YYYYMMDD-HHMM>/`'e yazar.

Kompozisyon:
- **Doluluk oranı** (`doluluk_orani`): maskedeki piksellerin sayfaya oranı.
- **Ağırlık merkezi** (`agirlik_merkezi_x`, `agirlik_merkezi_y`): maske piksellerinin ortalama konumu, sayfaya göre
  0–1 (x soldan sağa, y yukarıdan aşağı; 0,5 orta).
- **Kapsayan kutu oranı** (`kapsayan_kutu_orani`): maskeyi çevreleyen en küçük eksen hizalı dikdörtgenin sayfaya
  oranı. Tek bir uzak çizgi kutuyu büyütür; KIDO'da ortanca 0,98 (çoğu çizim sayfaya yayılmış).
- **Bölge doluluğu** (`doluluk_ust_sol` … `doluluk_alt_sag`): sayfa 3×3 bölgeye bölünür, her bölgenin doluluğu
  (9 değer, satır satır üst soldan).

Renk:
- **Farklı renk sayısı** (`renk_sayisi`): maskedeki doygun pikseller (S > 60, V > 60) 12 ton bölmesine (30°, kırmızı
  0° çevresinde ortalı) ayrılır; doygun piksellerin en az %3'ünü ve en az 50 pikseli içeren bölmeler sayılır. Siyah,
  gri ve beyaz sayılmaz; kahverengi turuncu/kırmızı bölmesine düşer. Karakalem çizim 0 verir.
- **Renk entropisi** (`renk_entropisi`): renk sayısına giren bölmelerin piksel dağılımının entropisi (bit). Tek renk
  ya da renksiz 0; k renk eşit kullanılmışsa log2(k), biri baskınsa daha düşük.
- **Ortalama doygunluk** (`ortalama_doygunluk`): maske piksellerinin ortalama S'si, 0–1. Karakalem ≈ 0.
- **Koyu ton oranı** (`koyu_ton_orani`): maskedeki piksellerden V < 80 olanların oranı. Siyah kalem/boya sayılır,
  kurşun kalem grisi (V ≈ 130–200) genelde sayılmaz.
- **Sıcak ton payı** (`sicak_ton_payi`): tablodaki "sıcak/soğuk oranı" pay olarak: sıcak / (sıcak + soğuk) doygun
  piksel, 0–1 (soğuk ton hiç yokken oran sonsuz olurdu). Sıcak: kırmızı, turuncu, sarı (345°–75°); soğuk: yeşil,
  camgöbeği, mavi (105°–255°); sarı-yeşil, mor ve pembe-eflatun ikisine de girmez. İkisi toplam 50 pikselden azsa
  tanımsız (karakalem; train'de %1,4).
- **Renklilik** (`renklilik_cizim`, metin raporda "Renklilik"): Hasler ve Süsstrunk (2003) ölçütü,
  rg = R − G, yb = (R + G)/2 − B; σ_rgyb + 0,3 μ_rgyb, **sadece maskedeki (çizim) piksellere uygulanır**.
  Neden: ölçüt fotoğraflar için tanımlanmış ve bütün görüntüde hesaplanır. Çocuk çiziminde görüntünün çoğu boş
  beyaz kağıttır; kağıt pikselleri ortalamayı ve yayılımı belirler, böylece değer "renk ne kadar canlı" sorusundan
  çok "sayfanın ne kadarı renkli" sorusunu yanıtlar. Sayfa tabanlı hali train'de dolulukla Spearman 0,76 ilişkili
  (sürüm 2), doluluğun tekrarı gibi okunuyordu. Maskeye uygulanınca kağıt hesaba girmez: aynı kırmızı küçük ya da
  büyük alanda aynı değeri verir; siyah/gri kalem ≈ 0. Çizim yoksa tanımsız.
- **Renklilik (sayfa)** (`renklilik`): aynı ölçüt bütün sayfa üzerinde (yayımlanan tanım). JSON'da ve normlarda
  kıyas için duruyor, metin raporda yok. Beyaz ya da gri sayfa 0.
- **Boyama oranı** (`boyama_orani`): maskeden 7 pikselden ince çizgiler morfolojik açmayla atılır, kalan kalın
  bölgeler "boyanmış alan" sayılır; oran = boyanmış alan / konturların kapladığı alan (maske + kapalı kontur
  içleri). Sadece kontur ≈ 0, içi boyanmış şekiller ≈ 1. Alan ağırlıklı: büyük bir boyalı zemin bandı oranı yükseltir.

Çizgi ve yapı:
- **Kenar yoğunluğu** (`kenar_yogunlugu_cizim`, metin raporda "Detay (kenar yoğunluğu)"): gri tonlu sayfada
  Canny kenar dedektörü (sigma 1); maskenin 2 piksel çevresi dışındaki kenarlar (kağıt dokusu, tarama izleri)
  sayılmaz; kenar piksellerinin **çizim piksellerine** oranı. Çizimin büyüklüğünden bağımsız: ince çizgilerden
  oluşan çizim yüksek, geniş düz boyama düşük. Çizim yoksa tanımsız.
- **Kenar yoğunluğu (sayfa)** (`kenar_yogunlugu`): aynı kenar piksellerinin sayfaya oranı (tablodaki tanım).
  JSON'da ve normlarda duruyor, metin raporda yok.
- **Toplam çizgi uzunluğu** (`cizgi_uzunlugu`): maskenin iskeleti (skimage `skeletonize`), piksel sayısı.
- **Ortalama çizgi kalınlığı** (`cizgi_kalinligi`): iskelet boyunca 2d − 1 (d: maskede kenara uzaklık, distance
  transform), piksel. Boyanmış alanlarda iskelet alanın ortasından geçer; değer alanın genişliğini ölçer.
- **Bağlı bileşen sayısı** (`bilesen_sayisi`): maskedeki 8-komşulukla bağlı parçalar, 30 pikselden küçükler hariç.

## Normlar ve rapor

- Normlar sadece **train** bölümünden (7842 çizim): `python -m src.measurements.norms` → Drive
  `normlar/olcum_normlari.csv` (her train çizimi için bir satır ve ölçüm sürümü). Val ve test norma girmez.
  Grup büyüklükleri (her sınıfta mutlu ve üzgün eşit, her öğrencinin iki çizimi):

  | Sınıf | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
  |---|---|---|---|---|---|---|---|---|
  | Mutlu / üzgün (her biri) | 258 | 324 | 696 | 683 | 658 | 544 | 456 | 302 |

- **Küçük grup:** karşılaştırma grubu 100 çizimden azsa (`report.MIN_GROUP`) ⚠ verilmez (%5'lik kuyruk 5'ten az
  çizime dayanırdı); yüzdelikler gösterilir, raporda "karşılaştırma grubu küçük (n=…)" notu düşer. KIDO normlarında
  böyle grup yok; kural başka normlar (örn. ileride başka veri) için.
- **Küçük çizim:** doluluk 0,03'ün altındaysa (`report.MIN_FILL`, ≈ 5350 piksel; train'in en düşük %1,2'si, 93 çizim)
  küçük çizim kümesindeki ölçümlere (`report.SMALL_DRAWING_MEASURES`) ⚠ verilmez; yüzdelikleri gösterilir. Metin
  raporda bu satırlar "*" ile işaretlenir, not: "* çizim çok küçük, bu ölçümler güvenilir değil". JSON'da `kalite`
  içinde `kucuk_cizim` (`deger` yuvarlanmamış doluluk, `etkilenen` kümedeki ölçümler). Küçük çizimde doluluk
  gösterimde aşağı yuvarlanır (0,02996 → 0,029), eşiğe çıkmış görünmesin. Eşik bir uzlaşım, belirgin kırılma yok.
- **Küçük çizim kümesi kuralı:** adaylar çizim piksellerine (ya da alt kümesine) göre oransal ölçümler ve renk sayısı
  (`metrics.SMALL_DRAWING_CANDIDATES`; renk sayısında bölme başına 50 piksel tabanı küçük çizimde renk düşürür).
  Bir aday, doluluk < 0,03 olan train çizimlerindeki %5–95 dışı oranı, doluluk > 0,1 olanlardakinin en az 2 katıysa
  kümeye girer. Oran ⚠ kuralıyla (kuyruk payı, aşağıda) ve her çizim kendi sınıf x görev grubunda hesaplanır.
  Doluluk, kapsayan kutu, bölge dolulukları, sayfa tabanlı ölçümler, çizgi uzunluğu, bileşen sayısı ve ağırlık
  merkezi aday değil: küçük çizimde uç çıkmaları çizimin küçüklüğünü doğru betimler, ⚠'leri kalır. Küme bir kez
  hesaplanıp sabitlendi (2026-10-21, sürüm 3 normları); yeniden hesaplamak ve sabitle karşılaştırmak için
  `python -m src.report --small-drawing-table`. Normlar değişince yeniden bakılır. Sonuç (%, train; küçük n=93,
  sıcak ton payında 66; büyük n=6932, sıcak ton payında 6890):

  | Ölçüm | Doluluk < 0,03 | Doluluk > 0,1 | Karar |
  |---|---|---|---|
  | Farklı renk sayısı | 24,7 | 4,4 | kümede |
  | Renk entropisi | 7,5 | 7,1 | dışarıda |
  | Ortalama doygunluk | 35,5 | 8,7 | kümede |
  | Koyu ton oranı | 12,9 | 4,5 | kümede (2,9 kat) |
  | Sıcak ton payı | 24,2 | 5,7 | kümede |
  | Renklilik (çizim pikselleri) | 36,6 | 8,8 | kümede |
  | Boyama oranı | 46,2 | 7,9 | kümede |
  | Kenar yoğunluğu (çizim pikseli başına) | 45,2 | 8,1 | kümede |
  | Ortalama çizgi kalınlığı | 53,8 | 8,1 | kümede |
  | Doluluk oranı | 100 | 5,8 | aday değil |
  | Ağırlık merkezi (x) | 32,3 | 8,3 | aday değil |
  | Ağırlık merkezi (y) | 29,0 | 8,3 | aday değil |
  | Kapsayan kutu oranı | 62,4 | 2,2 | aday değil |
  | Bölge doluluğu (üst sol / üst orta / üst sağ) | 1,1 / 5,4 / 0 | 5,7 / 5,9 / 5,5 | aday değil |
  | Bölge doluluğu (orta sol / merkez / orta sağ) | 3,2 / 2,2 / 0 | 6,4 / 6,3 / 5,5 | aday değil |
  | Bölge doluluğu (alt sol / alt orta / alt sağ) | 15,1 / 37,6 / 1,1 | 7,2 / 8,1 / 5,9 | aday değil |
  | Renklilik (sayfa) | 71,0 | 7,5 | aday değil |
  | Kenar yoğunluğu (sayfa) | 89,2 | 7,1 | aday değil |
  | Toplam çizgi uzunluğu | 79,6 | 8,2 | aday değil |
  | Bağlı bileşen sayısı | 4,3 | 5,5 | aday değil |
- Sınıf düzeyi dosya adından: `101-3B-560-F-H.jpg` → 3 (harf şube); görev son harften (H/S).
- **Yüzdelik:** orta sıra (eşit değerlerin yarısı altta sayılır).
- **⚠ (aralık dışı):** akranların %5'inden azı bu kadar düşük (ya da yüksek) bir değere sahipse. Orta sıra
  yüzdelik kullanılmaz: koyu ton oranı 0 olan çizimler grupların %5–12'si olduğu halde yüzdelikleri 2,5–6'ya düşer;
  sıradan bir değer işaretlenmesin diye kuyruk payı (≤ x ve ≥ x olanların oranı) kullanılır.
- Ölçüm ya da maske tanımı değişirse `metrics.MEASUREMENT_VERSION` artırılır; eski normlar yüklenirken hata verir.
- Rapor: `python -m src.report <görüntü yolu> [--grade N --task mutlu|uzgun]` → JSON + metin
  (Drive `raporlar/`). JSON modülden bağımsız: `modul`, `karsilastirma_grubu`, `olcumler`, `kalite`, `not`.
  `kalite` girdilerinin hepsinde aynı alanlar: `kimlik`, `deger`, `esik`, `bayrak`, `mesaj`, `etkilenen` (boş olabilir).
  JSON bütün ölçümleri (tablo sırasıyla, `grup` alanıyla) içerir; metin rapor sadece beşini, bu sırayla gösterir:
  doluluk oranı, farklı renk sayısı, renklilik (çizim pikselleri), koyu ton oranı, detay (kenar yoğunluğu, çizim
  pikseli başına).
  Rapor train'deki bir çizim içinse "çizim karşılaştırma grubunun içinde" notu düşer.

## Maske sınırlamaları

Normlar aynı maskeyle hesaplandığı için bütün çizimleri aynı yönde etkileyen hatalar yüzdelikleri bozmaz;
bazı çizimleri etkileyip bazılarını etkilemeyen hatalar bozar. Bunlar raporda görünür olmalı.

1. **Çok soluk renkler maskeye girmez** (bazı çizimleri etkiler). Kağıda çok yakın soluk renkler (S ≈ 15–20, V ≈ 250;
   örn. 110-3H-1081'deki camgöbeği yağmur çizgileri) tarama gürültüsünden ayrılamaz: boş kağıtta S'nin 95.
   yüzdeliği 23'e kadar çıkar. Eşikler düşürülmedi. Bunun yerine **soluk renk bayrağı**: maskenin 3 piksel çevresi
   ve 10 piksellik kenar şeridi dışında S ≥ 14 olan, en az 20 piksellik kümelerin sayfaya oranı. Boş kağıtta 0
   (2000 çizimde ortanca 0). Eşik 0.0015, 110-3H-1081'e (0.0019) bakılarak seçildi; train çizimlerinin %8,4'ü
   bayraklanır. Eşiğin hemen üstündeki 6 örnekten 4'ü gerçek soluk renk (soluk bulut konturu, gözyaşı, tarama),
   2'si kağıt lekesi. Bayrak varsa rapor "soluk renk kullanımı: ölçümler eksik olabilir" der.
2. **Seyrek tarama ve dolgular parçalı çıkar** (aynı yönde). Açık renkli seyrek taramada (gökyüzü gibi) piksellerin
   çoğu gerçekten beyaz kağıttır; maske piksel düzeyinde kalem izini ölçer, "boyanmış alanı" değil.
3. **Çizgiler maskede biraz kalın** (aynı yönde). JPEG sıkıştırma çizgi kenarlarında hale bırakır; doluluk bütün
   çizimlerde biraz yüksek ölçülür.
4. **Köşedeki tarama artıkları kalabilir** (nadir). 10 piksellik kenar şeridinden büyük köşe parçaları (örn.
   280-7N-1733'teki sarı üçgen) atılmaz. Bütün KIDO'da (10860 çizim) iki komşu kenara değip köşe kutusunda
   (genişlik ve yüksekliğin %15'i) kalan parça 1268 çizimde (%11,7) var, ama 12'lik rastgele örnekte hepsi gerçek
   çizim öğesiydi (köşeye çizilmiş bulut, güneş, yağmur). Gerçek artık nadir; düzeltilmedi.
5. **Kenara çok yakın çizilmiş çerçeve atılabilir** (nadir). Piksellerinin %90'ı kenara 10 pikselden yakın parçalar
   tarama izi sayılır. Bütün KIDO'da bu filtrenin attığı ≥ 200 piksellik, en az iki kenara uzanan parça 533 çizimde
   (%4,9) var; 12'lik rastgele örnekte hepsi tarama kenar çizgisi ya da gölge bandıydı, çizilmiş çerçeve görülmedi.
   Düzeltilmedi.
6. Bir köşeye ya da iki kenara değen büyük (sayfanın ≥ %1'i) parça 7708 çizimde (%71) var; bunlar çoğunlukla
   sayfayı boydan boya geçen gökyüzü ve zemin boyamaları, artık değil.

Sürüm 2 ölçümlerinin sınırlamaları:

7. **Boyama: kalın çizgi boyama sayılır** (aynı yönde). 7 pikselden kalın keçeli kalem / pastel çizgiler (JPEG
   halesiyle birlikte) boyanmış alan sayılır; seyrek tarama (sınırlama 2) boyanmamış sayılır.
8. **Kenar yoğunluğu doku da ölçer.** Pastel ve kuru boya dolgularının pürüzlü dokusu çok kenar üretir; değer çizilen
   ayrıntı ile boyama dokusunu birlikte ölçer.
9. **Sayfa tabanlı renklilik ve kenar yoğunluğu dolulukla güçlü ilişkili** (train, Spearman): kenar yoğunluğu
   0,87, renklilik 0,76; çok çizilen sayfada büyürler. Bu yüzden sürüm 3'te metin raporda çizim piksellerine göre
   halleri kullanılır; sayfa tabanlı halleri JSON'da ve normlarda kalır. Metin rapordaki beş ölçüm ve boyama oranı
   arasındaki Spearman korelasyonları (train, 7842 çizim, sürüm 3):

   | | doluluk | renk sayısı | renklilik | koyu ton | detay | boyama |
   |---|---|---|---|---|---|---|
   | doluluk | 1 | 0,15 | 0,28 | −0,07 | −0,42 | 0,47 |
   | renk sayısı | 0,15 | 1 | 0,24 | −0,02 | 0,03 | −0,05 |
   | renklilik | 0,28 | 0,24 | 1 | −0,16 | −0,56 | 0,50 |
   | koyu ton | −0,07 | −0,02 | −0,16 | 1 | 0,06 | −0,14 |
   | detay | −0,42 | 0,03 | −0,56 | 0,06 | 1 | −0,67 |
   | boyama | 0,47 | −0,05 | 0,50 | −0,14 | −0,67 | 1 |

10. **Detay (çizim pikseli başına kenar) çizgi kalınlığını da ölçer.** Kenar sayısı çizimin konturuyla, payda
    alanıyla büyür: ince çizgilerden oluşan çizim yüksek, geniş boyama düşük değer alır. Boyama oranıyla −0,67,
    ortalama çizgi kalınlığıyla −0,75 ilişkili (train). Değer "çok ayrıntı" kadar "ince çizgi / az boyama" da
    demektir.

## Model tabanlı ölçümler (görev uyumu, mutlu–üzgün ayrışma)

Plan: `docs/plan_gorev_uyumu.md`. Kod: `src/task_fit.py` (`python -m src.task_fit`). Bu bölüm adım 3'te
tamamlanacak (tanım, sınırlamalar); şimdilik adım 2'nin sonuçları.

- **Model:** donmuş referans model `convnext_tiny_320px_lr0.0001_ls0.1_s42` (320px, değerlendirmedeki dönüşüm).
  `p` = modelin "üzgün" olasılığı.
- **Görev uyumu:** mutlu görevinde `1 − p`, üzgün görevinde `p`. Raporda yüzdelik olarak; ⚠ verilmez.
- **Ayrışma:** `d = p(üzgün çizim) − p(mutlu çizim)` (olasılık farkı). Ölçüte göre (iki skoru da aynı uçta, < 0,1 ya
  da > 0,9, olan çiftler %25'ten fazlaysa logit) olasılık kaldı: val'de bu çiftler %5,9. `d > 0` olan çiftler %86,4.
- **Norm kaynağı:** KIDO val (1386 çizim, 693 öğrenci). Val model ve ayar seçiminde kullanıldı; iyimserlik payı
  testte ölçülecek (plan adım 6).
- **Norm grubu: eğitim seviyesi x görev** (ilkokul 1–4: 346 çizim / öğrenci; ortaokul 5–8: 347). Ölçüt val
  tahminlerinden önce yazıldı (Kruskal–Wallis p < 0,05 / 6 ve bir sınıfın havuzdaki medyan yüzdeliğinin 50'den
  ≥ 10 puan sapması, ikisi aynı hücrede). Val sonucu (her sınıfın havuzdaki medyan yüzdeliği):

  | Hücre | KW p | En büyük sapma | Sınıf medyanları |
  |---|---|---|---|
  | Görev uyumu, ilkokul, mutlu | 0,52 | 4,0 | 1: 48,3 · 2: 49,9 · 3: 48,0 · 4: 54,0 |
  | Görev uyumu, ilkokul, üzgün | 0,073 | 9,4 | 1: 40,6 · 2: 45,5 · 3: 55,8 · 4: 53,0 |
  | Görev uyumu, ortaokul, mutlu | 0,71 | 9,2 | 5: 55,0 · 6: 46,8 · 7: 52,0 · 8: 40,8 |
  | Görev uyumu, ortaokul, üzgün | 0,030 | 11,8 | 5: 48,1 · 6: 52,0 · 7: 38,2 · 8: 58,1 |
  | Ayrışma, ilkokul | 0,22 | 13,2 | 1: 42,3 · 2: 36,8 · 3: 54,2 · 4: 53,3 |
  | Ayrışma, ortaokul | 0,21 | 6,9 | 5: 50,4 · 6: 51,4 · 7: 43,1 · 8: 53,2 |

  Hiçbir hücrede iki koşul birlikte sağlanmadı. İki hücrede sapma 10 puanı geçti ama anlamlı değil (ortaokul üzgün:
  7. sınıf 38,2; ilkokul ayrışma: 2. sınıf 36,8); sınıf grupları küçük (val'de sınıf başına 44–134 çizim). Karar
  Bonferroni düzeltmesine bağlı: ortaokul üzgün hücresinin düzeltmesiz p'si 0,030; düzeltme olmasaydı bu hücre iki
  koşulu da sağlar, karar sınıf x görev olurdu. Ayrışmada logit kullanılsaydı karar değişmezdi (p 0,23 / 0,25).
  Sınırlama olarak not edilir.
- **Skor yığılması:** görev uyumunun medyanı 0,91–0,94, %75'lik değeri 0,95, %95'lik değeri 0,96–0,97 (dört hücre
  de). Üst yarıdaki yüzdelik farkları (50. ile 95. dilim) hücreye göre 0,031–0,056'lık olasılık farkına dayanıyor; label smoothing
  0,1 skorları 0,95 civarında topluyor. Mutlu çizimlerin %53–55'inde, üzgün çizimlerin %55–62'sinde görev uyumu
  0,9'un üstünde.
