# Doğrulama: küçük çizim kümesi kuralı, "*" işareti, JSON alanları (commit'lenmemiş değişiklik, 2026-10-21)

Denetleyen: dogrulayici subagent'ı. Önceki denetim: `2026-10-21-kucuk-cizim-bayragi.md` (ŞÜPHELİ, 8 bulgu).
Sonuç: **GEÇTİ**. Önceki 1–5 numaralı bulguların hepsi karşılanmış; aşağıdaki notlar küçük, düzeltme şart değil.

## Çalıştırılanlar
- unittest: 48 test geçti.
- `python -m src.training --model convnext_tiny --size 320 --quick`: cuda, 1 epoch, "kayıt yazılmadı".
- `deneyler.csv`: md5 koşudan önce ve sonra aynı (05921f3c…), son değişiklik 19 Ekim.
- Bölme: `splits.py`, `data.py`, metadata değişmedi (metadata 19 Ekim; train 7842, val 1386, test 1632).
  Norm dosyası 7842 satır, hepsi train, sürüm 3. `MEASUREMENT_VERSION` = 3, değişmemiş.
- Test seti: açılmadı. `mask_check.pick` artık sadece train'den aday çekiyor (`src/measurements/mask_check.py:37`);
  yeni seçimin 24 çiziminin hepsi train.
- `python -m src.report --small-drawing-table` (Drive normları): `docs/olcumler.md` tablosundaki 26 satırın hepsi,
  n'ler (93 / 6932; sıcak ton payında 66 / 6890) ve kararlar birebir aynı; "SMALL_DRAWING_MEASURES kuralla aynı."
- Raporlar scratchpad'e (Drive'a değil): 104-2D-1268-M-S, 207-6B-551-M-S, 110-3H-1081-F-S (soluk + küçük),
  103-4A-520-M-S (val), 101-2E-190-M-H, 240-8C-629-M-S; ayrıca küçük grup (n=99) + küçük çizim.
- Spearman / vekil kontrolü: ölçüm tanımı değişmedi, uygulanmadı.

## Kontroller
- ⚠ kuralı: `small_drawing_table` (`src/report.py:67–84`) rapordaki `outside()`'ı her çizimin kendi sınıf x görev
  grubunda, NaN'lar düşülerek çağırıyor; rapor da `outside(group[key], x)` ve `tail_shares` NaN düşüyor. Aynı.
  Tek fark: tablo `MIN_GROUP`'u uygulamıyor; KIDO'da 100'den küçük grup yok, sonuç etkilenmez.
- Metin "*": kümedeki satırlarda "*", doluluk ⚠ kalıyor; soluk + küçükte iki not ("* …" ve "Kalite: soluk …");
  küçük grup + küçükte ⚠ yok, "grup küçük" notu ve "* …" notu birlikte; normal çizimde "*" yok.
- JSON: iki kalite girdisinde de aynı alanlar; `kucuk_cizim.deger` yuvarlanmamış; `olcumler` doluluğu aşağı
  yuvarlanmış (4 hane), metin 3 haneye aşağı yuvarlanmış.
- `round_down`: train'deki 93 küçük çizimin hepsinde hem JSON hem metin değeri Decimal ile hesaplanan doğru
  aşağı yuvarlamayla aynı; 0,0299 → 0,0299 / "0,029", 0,02996 → 0,0299 / "0,029", 0,029 → "0,029".
- Mutasyon: `round_down` yerine `round` → sınır testi düşüyor; küme boş → 2 test düşüyor; `SMALL_FACTOR` = 10 →
  tablo testi düşüyor.

## Notlar (önem sırasıyla)

### 1. [Küçük] `round_down` tam ondalık değerlerde bir basamak düşük
`src/report.py:62–64`. `math.floor(x * 10**d)` kayan nokta hatasıyla tam değerleri bir alta atıyor:
`round_down(0.0029, 4)` = 0,0028; 0–0,03 arasındaki k/10000 değerlerinden 21'inde. KIDO'da gerçekleşmiyor (sayfa
178 416 ya da 180 432 piksel; doluluk k/10000'e ancak k 625'in katıysa eşit olur, 0,03'ün altında yok), metin yolunda
(3 hane) hiç görülmedi. Başka sayfa boyutlarında JSON değeri en fazla 0,0001 düşük çıkabilir. Çözüm istenirse
`Decimal` ya da küçük bir epsilon.

### 2. [Küçük] Testler ⚠ kuralını yüzdelik kuralından ayırmıyor
`tests/test_measurements.py:402–414`. `outside` orta sıra yüzdelik kuralıyla değiştirildiğinde bütün testler
geçiyor; önceki denetimin 1. bulgusu tam olarak bu karışıklıktı. Tablo testine eşitlikli bir ölçüm (ör. çoğu 0
olan koyu ton) eklemek bunu yakalar. Gerçek tablo doğru kuralla hesaplanıyor; bu sadece gerileme koruması.

### 3. [Küçük] Kontrol sayfasının çizimleri değişti
`src/measurements/mask_check.py:37`. Havuz daraltıldığı için aynı seed başka 24 çizim seçiyor (önceki dört küçük
çizimden sadece 207-6B-551-M-S kaldı; şimdi küçükler 104-2D-1268-M-S ve 207-6B-551-M-S). Kullanıcının onayladığı
sayfa eski seçim; `build()` yeniden koşulursa Drive'daki `maske_kontrol/` farklı çizimlerle üzerine yazılır.
Yeni seçimde uç değer: 240-8C-629-M-S doluluk 1,000 (sayfanın tamamı boyalı), 214-6F-12-F-S 0,956; ⚠ doğru
veriliyor, bu değişiklikle ilgisiz.

### 4. [Küçük] Ulaşılamayan dal ve "sınırda" ifadesi
`src/report.py:167`: metinde kümeden hiç ölçüm yoksa not "Kalite: çizim çok küçük, bu ölçümler güvenilir değil."
oluyor; "bu ölçümler" görünür bir şeye işaret etmiyor. Şu anki `TEXT_MEASURES` ile bu dala girilmiyor.
`docs/olcumler.md:119`: koyu ton 2,9 kat, eşik 2; "sınırda" yerine "eşiğe en yakın" daha doğru olur.

### 5. [Doğru] Belgeler
`docs/olcumler.md:99–135`, `CLAUDE.md:100–105`, `src/report.py:1–40` docstring ve yorumları kodla tutarlı;
`PER_DRAWING_MEASURES` ve eski oranlar kalmamış. `SMALL_DRAWING_MEASURES` ⊂ `SMALL_DRAWING_CANDIDATES`.
