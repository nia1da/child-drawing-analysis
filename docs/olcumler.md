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

## Uygulanan ölçümler (ilk dilim, ölçüm sürümü 1)

Kod: `src/measurements/` (`mask.py`, `metrics.py`, `norms.py`), rapor `src/report.py`.
Görüntüler 512×362; bütün ölçümler kenarlardan 4 piksel kırpılmış sayfa (504×354) üzerinde.

- **Çizim maskesi:** bir piksel çizime aittir, eğer V < 230 (kurşun kalem, siyah, koyu boya) ya da S > 30 (renkli)
  ise. Histerezis: V < 240 ya da S > 20 olan soluk pikseller, bu kesin eşikleri geçen bir parçaya bağlıysa katılır.
  8 pikselden küçük parçalar ve piksellerinin %90'ı kenara 10 pikselden yakın parçalar (tarama izleri) atılır.
  Eşiklerin ölçüldüğü veriler `mask.py` başında. Maske 24 çizimlik kontrol sayfasıyla onaylandı (2026-10-19;
  `python -m src.measurements.mask_check`, Drive `maske_kontrol/`).
- **Doluluk oranı:** maskedeki piksellerin sayfaya oranı.
- **Farklı renk sayısı:** maskedeki doygun pikseller (S > 60, V > 60) 12 ton bölmesine (30°, kırmızı 0° çevresinde
  ortalı) ayrılır; doygun piksellerin en az %3'ünü ve en az 50 pikseli içeren bölmeler sayılır. Siyah, gri ve beyaz
  sayılmaz; kahverengi turuncu/kırmızı bölmesine düşer. Karakalem çizim 0 verir.
- **Koyu ton oranı:** maskedeki piksellerden V < 80 olanların oranı. Siyah kalem/boya sayılır, kurşun kalem grisi
  (V ≈ 130–200) genelde sayılmaz. Çizim yoksa tanımsız.

## Normlar ve rapor

- Normlar sadece **train** bölümünden (7842 çizim): `python -m src.measurements.norms` → Drive
  `normlar/olcum_normlari.csv` (her train çizimi için bir satır ve ölçüm sürümü). Val ve test norma girmez.
  Grup büyüklükleri: sınıf × görev başına 258 (1. sınıf) – 696 (3. sınıf).
- Sınıf düzeyi dosya adından: `101-3B-560-F-H.jpg` → 3 (harf şube); görev son harften (H/S).
- **Yüzdelik:** orta sıra (eşit değerlerin yarısı altta sayılır).
- **⚠ (aralık dışı):** akranların %5'inden azı bu kadar düşük (ya da yüksek) bir değere sahipse. Orta sıra
  yüzdelik kullanılmaz: koyu ton oranı 0 olan çizimler grupların %5–12'si olduğu halde yüzdelikleri 2,5–6'ya düşer;
  sıradan bir değer işaretlenmesin diye kuyruk payı (≤ x ve ≥ x olanların oranı) kullanılır.
- Ölçüm ya da maske tanımı değişirse `metrics.MEASUREMENT_VERSION` artırılır; eski normlar yüklenirken hata verir.
- Rapor: `python -m src.report <görüntü yolu> [--grade N --task mutlu|uzgun]` → JSON + metin
  (Drive `raporlar/`). JSON modülden bağımsız: `modul`, `karsilastirma_grubu`, `olcumler`, `kalite`, `not`.
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
