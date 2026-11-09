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
| Çizgi ve yapı | Kenar yoğunluğu | Canny kenar piksellerinin oranı | Kenar ve doku miktarı (çizgi inceliğiyle birlikte; metin raporda yok) |
| | Toplam çizgi uzunluğu (metin raporda "Çizgi miktarı") | Maskeyi iskeletleştir, piksel say | Ne kadar çizgi çizildiği (boyanmış alanlar kısa sayılır) |
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
- **Kenar yoğunluğu** (`kenar_yogunlugu_cizim`; 2026-11-10'a kadar metin raporda "Detay", artık yalnız JSON'da): gri tonlu sayfada
  Canny kenar dedektörü (sigma 1); maskenin 2 piksel çevresi dışındaki kenarlar (kağıt dokusu, tarama izleri)
  sayılmaz; kenar piksellerinin **çizim piksellerine** oranı. Çizimin büyüklüğünden bağımsız: ince çizgilerden
  oluşan çizim yüksek, geniş düz boyama düşük. Çizim yoksa tanımsız.
- **Kenar yoğunluğu (sayfa)** (`kenar_yogunlugu`): aynı kenar piksellerinin sayfaya oranı (tablodaki tanım).
  JSON'da ve normlarda duruyor, metin raporda yok.
- **Toplam çizgi uzunluğu** (`cizgi_uzunlugu`; JSON adı "Toplam çizgi uzunluğu", metin raporda **"Çizgi miktarı"**,
  2026-11-10'dan itibaren): maskenin iskeleti (skimage `skeletonize`), piksel sayısı. Çizgilerin orta hattının
  toplam uzunluğudur; **boyanmış alanlar iskelette kısa sayılır, boyama miktarını ölçmez**: yoğun boyalı ama az çizgili
  bir çizim düşük çıkar. Çizgi kalınlığından bağımsız (Spearman −0,20). Mutlak piksel sayısıdır: normlar yalnız
  512 x 362 (10860 görüntünün 10848'i; 12'si 512 x 364–367) görüntüler için geçerli, başka çözünürlükte uzunluk
  yeniden ölçeklenmeli ya da norm yeniden çıkarılmalı.
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
  doluluk oranı, farklı renk sayısı, renklilik (çizim pikselleri), koyu ton oranı, çizgi miktarı (toplam çizgi
  uzunluğu, piksel; 2026-11-10'a kadar beşinci satır "Detay (kenar yoğunluğu)" idi). Metin rapor, çizgi miktarı için
  her raporda "boyanmış alanlar çizgi sayılmaz" notunu, küçük çizimde ayrıca "doluluk ve çizgi miktarı aynı olguyu
  yansıtır" notunu düşer.
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

   | | doluluk | renk sayısı | renklilik | koyu ton | çizgi miktarı | boyama |
   |---|---|---|---|---|---|---|
   | doluluk | 1 | 0,15 | 0,28 | −0,07 | 0,59 | 0,47 |
   | renk sayısı | 0,15 | 1 | 0,24 | −0,02 | 0,25 | −0,05 |
   | renklilik | 0,28 | 0,24 | 1 | −0,16 | −0,21 | 0,50 |
   | koyu ton | −0,07 | −0,02 | −0,16 | 1 | 0,05 | −0,14 |
   | çizgi miktarı | 0,59 | 0,25 | −0,21 | 0,05 | 1 | −0,23 |
   | boyama | 0,47 | −0,05 | 0,50 | −0,14 | −0,23 | 1 |

   (2026-11-10'a kadar beşinci ölçüm "detay" idi; dolulukla −0,42, renklilikle −0,56, boyamayla −0,67.
   Çizgi miktarının en yüksek ilişkisi dolulukla 0,59; aynı doluluk bandında, 0,08–0,12 (n=650), 5.–95. dilim
   967–4435: dolulukta olmayan bilgi taşır.)

10. **Detay (çizim pikseli başına kenar) çizgi kalınlığını da ölçer.** Kenar sayısı çizimin konturuyla, payda
    alanıyla büyür: ince çizgilerden oluşan çizim yüksek, geniş boyama düşük değer alır. Boyama oranıyla −0,67,
    ortalama çizgi kalınlığıyla −0,75 ilişkili (train). Değer "çok ayrıntı" kadar "ince çizgi / az boyama" da
    demektir. Bu yüzden 2026-11-10'dan itibaren metin raporda yok (yerine çizgi miktarı); JSON'da ve normlarda kalır.

11. **Çizgi miktarı (toplam çizgi uzunluğu) boyanmış alanı çizgi saymaz** (2026-11-10).
    - İskelet geniş boyalı bölgede kısa kalır: yoğun boyalı ama az çizgili çizim düşük çıkar; metin rapordaki not bunu
      söyler. Boyama miktarı için JSON'daki boyama oranına bakılır.
    - JPEG halesi, seyrek tarama ve maske sınırlamaları (2, 3) iki yönde uzunluk ekleyebilir; normlar aynı maskeyle
      çıktığı için aynı yönde etkilenir, kabul edildi.
    - Doluluk ile 0,59 ilişkili (en yükseği); küçük çizimde (doluluk < 0,03) hem doluluk hem çizgi miktarı ⚠ alır
      (çizgi miktarı mutlak bir ölçüm, küçük çizim kümesinde değil; train'de küçüklerde %79,6, büyüklerde %8,2). İkisi
      tek olgudur (çizim küçük); metin rapor bunu notla söyler. Kural değişmedi, küme tablosu yeniden hesaplanmadı.
    - Tam sayfa boyalı çizimlerde (doluluk > 0,9; train'de 294 çizim, %3,7) iskelet çok kısa kalır ve çizgi miktarı ⚠
      alır, gerçekte karakalem çizgisi olsa bile; düşük değer "az çaba" olarak okunmamalı, doluluk ve renklilikle birlikte
      bakılmalı.
    - Mutlak piksel sayısı: yalnız 512 x ~362 görüntüler için geçerli norm; başka çözünürlükte yeniden ölçekle ya da norm
      yeniden çıkar.

## Model tabanlı ölçümler (görev uyumu, mutlu–üzgün ayrışma)

Plan: `docs/plan_gorev_uyumu.md`. Kod: `src/task_fit.py` (`python -m src.task_fit`). Önce val analizi sonuçları, sonra
tanım ve sınırlamalar.

- **Model:** donmuş referans model `convnext_tiny_320px_lr0.0001_ls0.1_s42` (320px, değerlendirmedeki dönüşüm).
  `p` = modelin "üzgün" olasılığı.
- **Görev uyumu:** mutlu görevinde `1 − p`, üzgün görevinde `p`. Raporda yüzdelik olarak; ⚠ verilmez.
- **Ayrışma:** `d = p(üzgün çizim) − p(mutlu çizim)` (olasılık farkı). Ölçüte göre (iki skoru da aynı uçta, < 0,1 ya
  da > 0,9, olan çiftler %25'ten fazlaysa logit) olasılık kaldı: val'de bu çiftler %5,9. `d > 0` olan çiftler %86,4.
- **Norm kaynağı:** KIDO val (1386 çizim, 693 öğrenci). Val model ve ayar seçiminde kullanıldı; iyimserlik payı
  testte ölçüldü (aşağıda, "Bu ölçümün doğruluğu").
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
- **Sunum kararı (2026-10-21):** görev uyumu tam yüzdelik olarak verilir, kaba bant yok; her raporda yığılma notu
  durur: "Üst dilimlerde skorlar birbirine çok yakın (50.–95. dilim arası 0,03–0,06 olasılık farkı); küçük yüzdelik
  farkları anlamlı okunmamalı." Yüzdelik monoton dönüşümlerden etkilenmez; olasılık / logit seçimi görev uyumu
  yüzdeliğini değiştirmez.
- **Ayrışma `d` dağılımı (val, olasılık farkı):** `d` görev uyumundan farklı olarak geniş yayılıyor, aynı yığılma
  sorunu yok. İlkokul (n=346) 5 / 25 / 50 / 75 / 95. dilim: −0,291 / 0,110 / 0,703 / 0,875 / 0,914; ortaokul (n=347):
  −0,188 / 0,218 / 0,745 / 0,876 / 0,916. `d < 0` olan çiftler ilkokulda %15,6, ortaokulda %11,5. Üst uçta (75. dilimden
  sonra) `d` label smoothing yüzünden ≈ 0,92'de tavan yapar; orada da küçük fark yorumlanmaz, aynı not geçerli.

### Norm dosyası
`{output}/normlar/model_normlari.csv` (`python -m src.task_fit --write-norms`, 2026-10-21): val'den 2079 satır;
`tur=cizim` 1386 satır (skor = görev uyumu; ilkokul mutlu / üzgün 346 / 346, ortaokul 347 / 347), `tur=cift` 693 satır
(skor = `d`, ayrışma skoru `ayrisma_skoru` sütununda: `d_olasilik`; ilkokul 346, ortaokul 347). Sütunlar: tur, dosya, ogrenci, sinif,
egitim, gorev, skor, olasilik_uzgun, ayrisma_skoru, model, surum. Cinsiyet sütunu yok. `MODEL_NORM_VERSION` (şimdi 1)
ve model adı yüklemede kontrol edilir; uyuşmazsa hata verir.

### Raporda (2026-10-21)
`python -m src.report <görüntü>` JSON'a `model_olcumleri` ekler (model, norm sürümü, görev uyumu değeri / yüzdeliği,
karşılaştırma grubu ve n, notlar, sınırlamalar) ve metin raporda ölçüm satırlarının altında "Görev uyumu" satırını,
hemen altında karşılaştırma grubunu ve sınırlamaları gösterir. İki yol (mutlu, üzgün) verilirse ayrıca
`<öğrenci>_cift.json/.txt`: `d`, yönü (`uygun` / `ters`), yüzdeliği. Model (`.pt`) ya da norm dosyası yoksa bölüm
"çalışmadı" olur, ölçüm raporu etkilenmez. KIDO train'indeki çizimde "skor iyimser" notu, val'dekinde "karşılaştırma
grubunun içinde" notu çıkar.

### Tanım ve kullanım (rapora girmeden önce)
- **Ne ölçer:** modelin bu çizimi KIDO'da hangi göreve çizilmiş çizimlere benzettiği. Çocuğun duygu durumunu, görevi
  yapıp yapamadığını ya da bir klinik durumu göstermez.
- **Görev uyumu (tek çizim):** görev dosya adından ya da `--task`'tan; yüzdelik, eğitim seviyesi x görev val normunda
  (orta sıra yüzdelik, `norms.percentile` ile aynı). Karşılaştırma grubu ve n JSON'da ve metinde yazılır
  ("ilkokul (1–4. sınıf) mutlu normu, n=346"); ölçüm bölümünün sınıf normuyla karıştırılmaz.
- **Ayrışma (iki çizim):** aynı çocuğun mutlu ve üzgün çizimi birlikte verilirse `d` ve yüzdeliği; `d < 0` metinde
  "model iki çizimi görevlerinin tersi yönünde sıralıyor" olarak yazılır. Tek çizimde ayrışma hesaplanmaz.
- **⚠ verilmez**, uyarı özetine ve görüşme önerisi kurallarına girmez (`docs/kararlar.md`, 2026-10-21).

### Sınırlamalar (her raporda aynı, koşulsuz)
1. Skor çocuğun ruh hali değil; modelin görev benzerliğidir.
2. Norm kaynağı val: model ve ayar seçimi val ile yapıldığı için yüzdelikler hafif iyimser olabilir. Payı test
   çizimlerinin val normlarındaki dağılımıyla ölçüldü: belirgin bir sapma saptanmadı, küçük bir yukarı yönlü sapma dışlanamaz (aşağıda).
3. Model ilkokul erkek çocukların mutlu çizimlerini daha sık "üzgün" görevine benzetir; bu gruptaki çocuklarda düşük
   görev uyumu ve düşük ayrışma daha sık beklenir. Not herkese aynı gösterilir, cinsiyete göre koşullu değildir.
   Sayı: 320px referans modelde test %28,3 (GA 22,0–34,7; 448px modelde %33,7 görülmüştü).
4. Seyrek ya da az renkli çizimlerde görev uyumu düşebilir; doluluk ve renk sayısıyla birlikte okunmalı.
5. Üst dilimlerde skorlar birbirine çok yakın (yukarıdaki yığılma notu).
6. Norm grubu seçimi sınırda kaldı: ortaokul üzgün hücresinde sınıf eğilimi düzeltmesiz anlamlıydı (p 0,030); eğitim
   seviyesi normunda ortaokul 7. sınıf çizimleri daha düşük, 8. sınıf daha yüksek yüzdelik alabilir.
7. Normlar KIDO'dan (Şanlıurfa, 1–8. sınıf); başka bir örneklemde dağılım farklı olabilir.
8. Test doğruluğu aşağıda ("Bu ölçümün doğruluğu"). Çizim KIDO train'indeyse skor iyimserdir (model o çizimi eğitimde gördü); rapor bunu not eder (adım 5).

### Bu ölçümün doğruluğu (test, 2026-11-10; plan `docs/plan_test_metrikleri.md`, adım 6)
Test tahminleri referans modelle bir kez üretildi (`tahminler/convnext_tiny_320px_lr0.0001_ls0.1_s42_test.csv`,
sha256 `ac410b6f…98c1`); 816 öğrenci, 1632 çizim. Tablolar `{output}/test_metrikleri/` (`python -m src.final_metrics`).
Öğrenci bazlı bootstrap %95 GA (2000, seed 42). **Dürüstlük notu:** test seti daha önce 448px modelle görülmüştü
(alt grup hipotezi oradan); bu 320px modelde ilk ve tek ölçümdür, bağımsız keşif değil yeniden doğrulamadır.
Birincil metrikler genel AUC, `d > 0` oranı ve norm aktarımıdır; alt grup sonuçları betimleyici ve düzeltmesizdir.

- **Ayırt edicilik (birincil).** AUC val 0,880 (GA 0,862–0,898), test 0,889 (0,872–0,904); val–test farkı −0,009
  (test biraz yüksek; belirgin iyimserlik payı saptanmadı, küçük bir yukarı yönlü sapma dışlanamaz). macro F1 (0,5 eşiği) val 0,810, test 0,806 (0,787–0,825). Çiftlerde
  `d > 0` oranı val %86,4, test %89,3 (87,1–91,4).
- **Norm aktarımı (birincil).** Test çizimlerinin val normundaki yüzdeliği ≤ 5 olanlar %4,8 (3,7–5,9), ≥ 95 olanlar
  %6,3 (5,2–7,5) (görev uyumu, genel; beklenen %5). Hücre hükümleri (önceden yazılmış kural: GA'nın tamamı %10'un
  üstündeyse "zayıf"): 8 hücrenin 16 ucundan 15'i "makul"; ortaokul mutlu üst uç %10,5 (7,6–13,8) "belirsiz". Hiçbir uç
  "zayıf" değil. Val normu sabit alındı; val'in kendi örnekleme belirsizliği GA'da yok. 50. yüzdelik altı oranı
  %43,9–55,1 (hükme girmez). Ayrışma: ≤ 5 %4,0, ≥ 95 %5,1.
- **Alt gruplar (betimleyici).** AUC kadın 0,907, erkek 0,857; ilkokul kadın 0,913, ilkokul erkek 0,826; ortaokul
  kadın 0,903, ortaokul erkek 0,898. macro F1: ilkokul kadın 0,846, ilkokul erkek 0,741. Kadın–erkek AUC farkı 0,050
  (GA 0,018–0,081), ilkokul kadın–erkek 0,087 (0,041–0,131); ortaokulda fark 0,006 (−0,039–0,052). Sınıf düzeyi
  AUC 0,84–0,92 (sınıf 8 en geniş GA: 0,756–0,909, n=59). Sınıflar arası fark yazılmadı.
- **Hata yönü.** Mutlu çizimin "üzgün" tahmin edilmesi: genel %18,8; ilkokul erkek %28,3 (22,0–34,7), ilkokul kadın
  %12,2 (8,3–16,8), ortaokul erkek %19,0 (12,3–25,9). Üzgün→mutlu yönü gruplar arasında %18–24 civarında, belirgin
  fark yok. Sınırlama notundaki sayı bununla güncellendi (%33,7 → %28,3, 448px → 320px).
- **En alt %5 sıklığı** (görev uyumu yüzdeliği ≤ 5, sadece belgeleme): genel %4,8; ilkokul erkek %6,4; ortaokul erkek
  %3,3; sınıf 7 ve 8 %6,5–6,8. Gruplar arası fark küçük; ⚠ kararını değiştirmez.
- **Sınırlamalar:** alt grup ve sınıf tabloları düzeltmesiz (yaklaşık 20 grup); küçük gruplarda GA geniş.
  Test val'den farklı örneklem olduğu için norm aktarımının makul çıkması başka örnekleme genelleme anlamına gelmez
  (hepsi KIDO).
