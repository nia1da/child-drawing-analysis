# Doğrulama: 5a3cc35, küçük çizimlerde oransal ölçümlere ⚠ verilmemesi (2026-10-21)

Denetleyen: dogrulayici subagent'ı. Sonuç: **ŞÜPHELİ**. Kod mantığı doğru, testler geçiyor, test seti ve bölme
etkilenmemiş; ama dokümandaki gerekçe sayıları raporun kullandığı ⚠ kuralıyla tutmuyor, iki üye (koyu ton, renk
entropisi) bu kurala göre neredeyse hiç savrulmuyor ve metin raporda hangi satırın etkilendiği görünmüyor.

## Çalıştırılanlar
- unittest: 44 test geçti.
- `python -m src.training --model convnext_tiny --size 320 --quick`: cuda'da 1 epoch, "kayıt yazılmadı".
- `deneyler.csv`: md5 koşudan önce ve sonra aynı; son değişikliği 19 Ekim.
- Bölme: commit `src/splits.py`, `src/data.py` ve metadata'ya dokunmuyor. Metadata train 7842, val 1386, test 1632;
  norm dosyasındaki 7842 satırın hepsi train'de, sürüm 3.
- Test seti: commit test setini açmıyor. Ancak `mask_check.pick` aday havuzunu bütün metadata'dan çekiyor
  (`src/measurements/mask_check.py:40`, `:81`) ve sınıflandırmak için adayların görsellerini okuyor (`kind_of`).
  Etiket ya da değerlendirme kullanılmıyor; seçilen 24 çizimin hiçbiri test değil (21 train, 3 val). Önceden de vardı.
- Spearman / vekil kontrolü: ölçüm tanımı değişmediği için uygulanmadı.

## Bulgular (önem sırasıyla)

### 1. [Şüpheli, önemli] Dokümandaki oranlar ⚠ kuralıyla yeniden üretilemiyor
Yer: `docs/olcumler.md:99–104`, `src/report.py:27–29`. Train normlarında her çizim kendi sınıf x görev grubunda,
rapordaki kuralla (`tail_shares`, eşit ya da daha uç olanlar %5'ten az) değerlendirildi. %5–95 dışı oranı (%):

| ölçüm | doluluk <0,01 (n=9) | 0,01–0,02 (n=30) | 0,02–0,03 (n=54) | 0,03–0,05 | >0,1 |
|---|---|---|---|---|---|
| boyama_orani | 44 | 47 | 46 | 31 | 7,8 |
| cizgi_kalinligi | 67 | 53 | 52 | 29 | 8,0 |
| kenar_yogunlugu_cizim | 56 | 47 | 43 | 29 | 8,0 |
| ortalama_doygunluk | 44 | 40 | 32 | 23 | 8,7 |
| renklilik_cizim | 56 | 37 | 33 | 23 | 8,7 |
| sicak_ton_payi | 67 | 23 | 18 | 11 | 5,6 |
| koyu_ton_orani | 0 | 17 | 13 | 11 | 4,5 |
| renk_entropisi | 11 | 10 | 5,6 | 6,2 | 7,0 |

Doküman 0,02–0,03 için "%19–54", 0,01 altı için "%44–78" diyor; koyu ton ve entropi için doğru değil, entropide
küçük çizimlerde artış yok. Orta sıra yüzdelikle (p<5 ya da p>95) dokümana yakın sayılar çıkıyor (%26–52, %44–67):
sayılar büyük ihtimalle raporun kullanmadığı yöntemle hesaplanmış. Öneri: oranları `tail_shares` kuralıyla yeniden
yaz; `renk_entropisi` ve `koyu_ton_orani`'nın kümede kalmasını yeniden düşün.

### 2. [Şüpheli, klinisyen tarafı] Metin raporda etkilenen satırlar işaretlenmiyor
Yer: `src/report.py:118`, `:126`. Kontrol sayfasındaki 24 çizimin 4'ü 0,03'ün altında (110-3H-1081-F-S 0,004;
103-4A-520-M-S 0,013, val; 207-6B-551-M-S 0,017; 101-2E-190-M-H 0,026). Dördünde de "Detay … 98–99. yüzdelik
diliminin üstünde", "Renklilik … 1. yüzdelik diliminin altında" ⚠'siz görünüyor; tek uyarı genel kalite notu ve hangi
satırları kastettiğini söylemiyor. JSON'da `etkilenen` var, metinde yok. Öneri: satır düzeyinde işaret ya da notta
ölçüm adları.

### 3. [Şüpheli, kapsam] `renk_sayisi` küçük çizimde de büyüklüğe bağlı ama dışarıda
Yer: `src/measurements/metrics.py:29`, `:113`. Bir ton bölmesi için en az 50 piksel (`HUE_MIN_PIXELS`) gerekiyor;
93 küçük çizimin 17'sinde en az bir renk bu taban yüzünden sayılmamış (küçük çizimlerde doygun piksel medyanı 943).
%5–95 dışı oranı 0,02–0,03'te %20, 0,01 altında %44, doluluk >0,1'de %4,3. Dışarıda bırakmak savunulabilir ama
belgelenmeli. Diğer dışarıda bırakılanlar mantıklı (mutlak ölçüler; sayfa tabanlı ölçümler küçük çizimde doğru
betimleme; ağırlık merkezi dağınık ama konumu doğru gösteriyor). Kümedeki 8 ölçümün hepsi gerçekten çizim
piksellerine ya da alt kümesine bölünüyor.

### 4. [Küçük] JSON şeması tutarsız
Yer: `src/report.py:72–77`. `soluk_renk` girdisinde `etkilenen` yok, `kucuk_cizim`'de var. `kucuk_cizim.deger` 4
haneye yuvarlanıyor: 0,02996 "deger 0,03, esik 0,03, bayrak true" görünür.

### 5. [Küçük] Testler
Yer: `tests/test_measurements.py:318–342`. Mutasyon: küme boşaltılınca yeni test düşüyor, davranış gerçekten
sınanıyor. Eksik: eşik sınırı (doluluk == 0,03'te bayrak olmamalı), küçük grup + küçük çizim birlikte, `etkilenen`
içeriği; kümeye girmeyen ölçümlerin ⚠'si sadece metin satırlarından dolaylı sınanıyor.

### 6. [Doğru] report.py mantığı
`tiny` `small`'dan bağımsız; ikisi birlikteyse bütün ⚠ kalkar, iki not da görünür. None değerli ölçümlerde yüzdelik
ve ⚠ None (küçük çizimlerde `sicak_ton_payi` 93'ün 27'sinde None). Boş çizim bayrak alıyor. Doluluğun ⚠'si korunuyor.

### 7. [Doğrulandı] Dokümandaki diğer sayılar
Train'de doluluk <0,03: 93 çizim (%1,19). Kırpılmış sayfa 178 416 piksel (biri 180 432); 0,03 x sayfa = 5352.
Doluluk >0,1'de %4–9 doğrulandı (%4,5–8,7).

### 8. MEASUREMENT_VERSION artırılmamalı
Ölçüm ve maske tanımı değişmedi, norm CSV'si aynı. Yan not: JSON `surum` ölçüm sürümü; aynı sürüm 3 raporlarının
bir kısmında `kucuk_cizim` var, bir kısmında yok. Rapor şeması ayrıca sürümlenebilir; zorunlu değil.
