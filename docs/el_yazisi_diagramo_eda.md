# DiaGraMo: EDA, etiket analizi, koordinat → PNG prototipi ve model fizibilitesi

Tarih: 2026-11-26. Veri: *Multimodal Czech online handwriting and cognitive data from children with and without handwriting disabilities*
(Zvončáková, Mekyska, Klocek, Mucha, Galáž; v2, Temmuz 2026; DOI 10.5281/zenodo.18299326; **CC BY 4.0**). Yalnız DiaGraMo üzerinde çalışıldı; FD-LEX, Malaysian ve çizim modülü değişmedi.
Veri yerel `data/handwriting/diagramo/` altında, git dışı. Etiketler: **[doğrulandı]** dosyalardan ölçüldü, **[README]** veri setinin kendi belgesinde yazıyor, **[belirtilmemiş]** belgelerde yok.

## Özet

- **Online (tablet) veri:** 288 çocuk, 4000 koordinat kaydı (SVC), 14 görev/çocuk (11–14). Statik fotoğraf değil; kalem koordinatları (x, y mm), zaman, kalem durumu, basınç, eğim.
- **Bütün yazı örnekleri:** 4 görev — *dictation-3/4* (dikte) ve *copy-3/4* (kopya) — kısa Çekçe cümleler (3. ve 4. sınıf sürümleri), çizgili kâğıda. **Harf, kelime ya da paragraf düzeyinde ayrı görev yok**; diğer görevler spiral/döngü/testere elemanları ve Rey figürü çizimidir. 270 kullanılabilir çocuktan toplam **530 yazma kaydı** (dikte 260, kopya 270 çocuk).
- **Etiketler:** tanı kaydı (disgrafi, disleksi, disortografi, dispraksi, diskalkuli), `group` (el yazısı güçlüğü 157 / tipik 118 benzersiz çocuk), **HLS** (el yazısı ürününün 5 maddelik derecelendirmesi: okunabilirlik, çaba, **sayfa düzeni, harf biçimi**, düzeltmeler), HPSQ-C öz bildirimi, grafomotor eleman değerlendirmeleri, Rey figürü, WJ-IV, BACH, DIB. Statik görüntüyle en ilişkili olanlar HLS maddeleri.
- **Ciddi karıştırıcı:** `group` ile **şehir/okul/zaman** neredeyse örtüşüyor: 118 tipik çocuğun **hepsi** tek şehirden (city1, ID ön eki BR), el yazısı güçlüğü olan 157 çocuğun yalnız 9'u o şehirden; 60 HD çocuğu "PPP" (pedagojik-psikolojik danışma) merkezinde toplanmış, tipik çocukların hiçbiri orada değil.
  Bu yüzden **disgrafi/HD sınıflandırması şimdilik savunulamaz** (model yalnız konum/zamanı öğrenebilir).
- **Prototip:** koordinatlardan fiziksel ölçekli PNG üretimi çalışıyor (16 örnek görüntü, 15 test). Önemli bulgu: **tablet y ekseni yukarı doğru** (60/60 kayıtta yazı y azalarak ilerliyor); düzeltilmeden görüntüler ters çıkıyor.
- **Model fizibilitesi (özet):** supervised öğrenme için en uygun hedefler **HLS maddeleri (özellikle sayfa düzeni, harf biçimi, düzeltmeler)** ve eleman görevleri; ilk adım model değil, **kendi geometrik özelliklerimizi HLS ile karşılaştırarak doğrulamak**. Gerçek fotoğraf ile koordinattan üretilen görüntü arasında büyük alan farkı var (kâğıt çizgisi, kalem, gürültü, sabit çizgi kalınlığı).

## 1. Kullanım koşulları [README]

| Konu | İçerik |
|---|---|
| Lisans | CC BY 4.0: paylaşım ve uyarlama serbest, **atıf zorunlu** |
| Atıf | Zenodo DOI 10.5281/zenodo.18299326, v2 (Temmuz 2026); yazarlar yukarıda |
| Etik | PSU-752/Brno/2020 (Çek Bilimler Akademisi Psikoloji Enstitüsü etik kurulu) |
| Gizlilik | v2'de doğum tarihi ve onay tarihi kaldırılmış; test tarihi 3 aylık pencere + yıl; katılımcı, şehir ve okul kodları anonim |
| Fikri mülkiyet | WJ-IV, BACH, DIB, RCFT madde metinleri ve puanlama protokolleri **yayımlanmamış** (telif); yalnız türetilmiş puanlar var |
| Toplama | Aralık 2021 – Haziran 2023, Çekya; cihaz Wacom Cintiq 16, ortalama ≈ 167 Hz (README) |
| Eksik değer kodu | `null` (CSV'lerde boş) |

Lisans, verinin işlenmesine ve paylaşılmasına izin veriyor; yine de çocuk verisi olduğu için ham veri, türetilmiş görüntüler ve katılımcı kodları **GitHub'a yüklenmez** (kullanıcı kararı); yalnız yerelde tutulur.
Sınırlama: README bazı belge tutarsızlıkları içeriyor (aşağıda §3 ve §6).

## 2. Dizin düzenlemesi [doğrulandı]

```
data/handwriting/diagramo/
  raw/         arşivin iç yapısı korunarak: data/{raw_data,processed_data,clean_data}, info/, scripts/, DiaGraMo_project.Rproj
  processed/images/   üretilen PNG'ler (16 örnek + _contact_sheet.png)
  metadata/    codebook_flat.csv, label_table.csv (türetilmiş)
  manifests/   svc_inventory.csv, json_vs_svc.csv, samples.csv (türetilmiş)
```
Bir iç içe `DiaGraMo-project/DiaGraMo-project` kaldırıldı (aynı sürücüde yeniden adlandırma; veri kopyalanmadı). **Kayıp yok:** taşıma öncesi ve sonrası 8311 dosyanın göreli yolları ve bayt boyutları listesi birebir aynı (12 887 564 392 bayt).
`data/` `.gitignore` altında (`git check-ignore` ile doğrulandı).

| Klasör | Dosya | Boyut |
|---|---|---|
| `data/raw_data/handwriting_data/data_SVC` | 4000 `.svc` (288 klasör) | ≈ 3 GB |
| `data/processed_data/handwriting_data/data_JSON` | 4000 `.json` (SVC'nin dönüştürülmüşü) | 2,9 GB |
| `data/clean_data` | 294 `*_merged.json` (çocuk başına görev JSON'ları + bilişsel veri) | 5,6 GB |
| `data/{raw,processed}_data/cognitive_test_data` | `.csv` (`;` ayraç, ondalık virgül) ve `.rds` | 0,8 MB |
| `info/` | Codebook.xlsx (768 değişken), README.txt, metadata.json, stimuli.pdf, dataReport_TACR.html, distorted_data.xlsx | 11 MB |
| `scripts/` | R (temizleme, birleştirme, psikometri), Python (SVC → JSON) | 0,2 MB |

## 3. Ham ve temizlenmiş veri farkları [doğrulandı]

| Karşılaştırma | Sonuç |
|---|---|
| **SVC → processed JSON** | 4000/4000 dosyada `samples_count` SVC satır sayısına eşit; ama **7 dosyada JSON dizileri SVC'den kısa** (1–15 örnek); 3'ünde yalnız son örnek(ler) eksik, 4 eleman kaydında ortak uzunlukta bile değerler farklı (dönüştürücü baştaki/sondaki havada hareketi kırpma kontrolleri yapıyor; kırpma olabilir, nedeni incelenmedi); kalan 3993 dosya birebir aynı. Ham kaynak olarak SVC kullanılmalı |
| **processed JSON → clean_data** | Örneklenen 150 dosyada (x, y, zaman, kalem, azimut, eğim, basınç) fark yok; `clean_data` aynı koordinatları + bilişsel veriyi birleştiriyor |
| **Bilişsel CSV ham → temizlenmiş** | 289 satır, **762 ortak sütunun hiçbirinde değer farkı yok**; temizlenmiş sürüm sütun adlarını snake_case yapıyor ve **6 sütun ekliyor**: 5 omit bayrağı + `participant_count`. **Hiçbir satır silinmemiş** |
| **Omit bayrakları** (`flag_to_omit_total`) | 13 satır işaretli: `group` ∉ {0,1} (8), Çekçe dışı dil (2), tanı alakasız (8: disleksi/disortografi tek başına vb.), tanı kaydı eksik (3). Temizleme betiği tanı olarak yalnız *tipik gelişim*, *disgrafi* ve *tanı sürüyor* kategorilerini alakalı sayıyor. Kullanılabilir: **276 satır = 275 benzersiz çocuk** |
| `clean_data` kapsamı | 294 katılımcı dosyası: 288 bilişsel kayıt **+ 6 yalnız-SVC katılımcı**; omit bayraklı 13 çocuk **çıkarılmamış** |

Kodlama sorunları: kod kitabı ile veri arasında **72 sütun adı uyuşmuyor** (veride yazım hataları: `dib_transription_*`, `hls_*_a_ledgibility`); ham CSV'de camelCase (`id_schoolPPP`), temizlenmişte snake_case.

## 4. Katılımcılar [doğrulandı]

| | Tüm kayıtlar | Kullanılabilir (omit = 0) |
|---|---|---|
| Satır / benzersiz çocuk | 289 / 288 (1 tekrarlayan ID, iki satır yalnız HLS dikte maddelerinde farklı: biri eksik) | 276 / 275 |
| El yazısı güçlüğü (`group = 1`) / tipik (0) | 159 / 122 (8 eksik; satır sayısı) | satır: 158 / 118; **benzersiz çocuk: 157 / 118** (README özeti 161 HD diyor: dosyadan teyit edilemedi) |
| Sınıf 3 / 4 | 114 / 175 | 109 / 167 (3. sınıf: yaş 8,2–10,6; 4. sınıf: 9,2–11,9) |
| Cinsiyet (kız) | 73/289 | %26 hem HD'de hem tipikte |
| Yaş (yıl) | 8,2–11,9 (ort. 9,8) | HD 9,81, tipik 9,76 |
| Okul / şehir | 36 / 15 | 35 / 15 (okul başına medyan 7 çocuk; ≥ 10 çocuğu olan 10 okul) |
| Toplama yeri (`site_type_ppp`) | okul 220 / PPP 65 | okul 215 / **PPP 60 (hepsi HD)** |

Kimlik uyuşmazlığı: **6 çocuğun SVC dosyası var, bilişsel kaydı yok** (kodlar belgeye yazılmadı; 13–14 görev) ve **6 bilişsel kaydın SVC'si yok** (4'ü `BR09...`, 2'si `BR8...` biçiminde kod). Eşleştirme tahmin edilmedi (yazım hatası mı, gerçek eksik mi **belirtilmemiş**).
Kullanılabilir 275 çocuktan **273'ünün SVC kaydı** var; **270'inin en az bir yazma kaydı** var.

**Şehir/okul/zaman ile grup örtüşmesi [doğrulandı]:**
- Tipik 118 çocuğun **tamamı** `city1` (ID ön eki `BR`, 11 okul); HD çocukları 15 şehirden (`city1`: 9, `city4`/ön ek HK: 53, diğerleri 2–13).
- 35 okuldan yalnız **5'inde iki grup birlikte** (58 çocuk: 50 tipik, 8 HD); 6 okul yalnız tipik (68), 24 okul yalnız HD (148).
- Toplama dönemi: HD'nin 121/157'si *2022 Ekim–Aralık*; tipiklerin dağılımı 2021 Ekim – 2023 Haziran arası.
- Şehir içi kontrol: `city1`'de 118 tipik / 9 HD.

## 5. Görevler ve koordinat verisi

### 5.1 Görev türleri ve örnek sayıları [doğrulandı]

Görev adları dosya adından (`ID_TSKnn(TA)-ad_1.svc`); 14 görev/çocuk (TSK 3-4 ile 15-16 sınıfa göre: dikte/kopya 3. ya da 4. sınıf sürümü). `kullanılabilir`: omit = 0 çocukların kayıtları.

| TSK | görev | tür | dosya | katılımcı | kullanılabilir katılımcı | HD / tipik | nokta (medyan) | süre s (medyan) | vuruş (medyan) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | RCFT-recognition | rcft | 285 | 285 | 270 | 153 / 117 | 25564 | 221 | 57 |
| 2 | RCFT-recall | rcft | 285 | 285 | 271 | 154 / 117 | 15080 | 125 | 41 |
| 3 | dictation-3 | writing | 113 | 113 | 110 | 56 / 54 | 80135 | 553 | 151 |
| 4 | dictation-4 | writing | 159 | 159 | 150 | 91 / 59 | 83626 | 567 | 208 |
| 5 | big-spiral-fast | element | 287 | 287 | 272 | 155 / 117 | 1282 | 7 | 1 |
| 6 | small-spiral-fast | element | 288 | 288 | 273 | 156 / 117 | 1158 | 6 | 1 |
| 7 | saw-fast | element | 288 | 288 | 273 | 156 / 117 | 912 | 5 | 1 |
| 8 | upper-loops-fast | element | 287 | 287 | 272 | 155 / 117 | 1105 | 6 | 1 |
| 9 | lower-loops-fast | element | 287 | 287 | 272 | 155 / 117 | 1877 | 10 | 1 |
| 10 | rainbow-fast | element | 286 | 286 | 271 | 154 / 117 | 1220 | 7 | 1 |
| 11 | combined-loops-fast | element | 288 | 288 | 273 | 156 / 117 | 2852 | 16 | 2 |
| 12 | small-spiral-precise | element | 288 | 288 | 273 | 156 / 117 | 2628 | 15 | 1 |
| 13 | lower-loops-precise | element | 288 | 288 | 273 | 156 / 117 | 2722 | 15 | 1 |
| 14 | combined-loops-precise | element | 288 | 288 | 273 | 156 / 117 | 3505 | 20 | 2 |
| 15 | copy-3 | writing | 117 | 117 | 114 | 58 / 56 | 47762 | 337 | 98 |
| 16 | copy-4 | writing | 166 | 166 | 156 | 95 / 61 | 61676 | 427 | 146 |

- **Bütün yazı örnekleri (cümle yazma): TSK3/4 dikte ve TSK15/16 kopya.** Uyarıcı (`info/stimuli.pdf`): 3–5 kısa Çekçe cümle, "podpis" (imza) satırı altında çizgili kâğıda; kopyada metin basılı sunuluyor. Metin sınıfa göre sabit (3. ve 4. sınıf sürümü): aynı metni yazan çocuklar arasında doğrudan kıyas mümkün.
- **Tek harf / kelime / paragraf görevi yok.** Eleman görevleri (TSK5–14): spiral, testere, döngüler, gökkuşağı (bir kalem vuruşu); RCFT (TSK1–2): Rey karmaşık figürü kopya/hatırlama çizimi (**çizim görevi**).
- **Sınıf ↔ görev sürümü:** 3. sınıfta 107 çocuk 3 sürümünü, 1 çocuk 4 sürümünü yazmış; 4. sınıfta 155 / 7 (ters) / 4 yazma kaydı yok: sınıf etiketi ile yazma metni sürümü 8 çocukta uyuşmuyor.

### 5.2 SVC koordinat yapısı ve birimler [doğrulandı + dolaylı çıkarım]

- Biçim: ilk satır örnek sayısı, sonra 7 sütun: **x, y, zaman, kalem durumu, azimut, eğim (altitude), basınç** (README ve `convert_SVC_to_JSON.py`). Başlık sayısı satır sayısına 4000/4000 eşit.
- **Zaman:** saniye; 200 Hz nominal (medyan Δt = 0,005 s); yazma kaydı medyanı 69 bin nokta ≈ 8 dk (pen havadayken de kayıt sürüyor).
- **x, y birimi: milimetre (README'de açıkça yazmıyor; dolaylı doğrulama):** koordinat üst sınırı x ≈ 348,16, y ≈ 203,2 (tablet etkin alanı belgelenmemiş; yalnız gözlenen üst sınır), kalem çizim hızı medyan ≈ 16 mm/s (IQR 14–20), ardışık nokta mesafesi medyan 0,14–0,17 mm, tahmin edilen satır aralığı ≈ 11 mm (40 kayıtta otokorelasyonla; FD-LEX'in 10,8 mm kâğıt çizgisine yakın).
- **y ekseni yukarı doğru artıyor:** 60 rastgele yazma kaydının 60'ında ilk %10 noktanın ortalama y'si son %10'dan büyük (medyan 49 mm; yazı yukarıdan aşağı ilerler), x için 55/60 (sola→sağa). Sol-alt orijin.
- **Kalem durumu:** 1 = kalem yüzeyde, 0 = havada (`pen=1` iken basınç > 0 hariç: 0 satır `pen=1 ∧ basınç=0`, 0 satır `pen=0 ∧ basınç>0`). Yüzeydeki koşularda zaman boşluğu yok; hareketsiz havada kayıt sürüyor (havadaki en büyük Δt: 2185 s, 4000 dosyanın birinde). 
- **Basınç:** 0–8192 (tablet seviyesi, fiziksel birim belirtilmemiş); **azimut** 0–359; **eğim** 20–90 (derece varsayımı; birim belirtilmemiş). Statik fotoğraftan elde edilemeyen: hız, basınç, eğim, hareket sırası, havadaki hareket.
- **Yazma görevi vuruş sayıları** (pen 0→1): dikte-3 medyan 151, dikte-4 208, kopya-3 98, kopya-4 146.
- **Kâğıt/sayfa boyutu ve çizgiler kayıtta yok.** Yazı tablet koordinatlarında; kâğıt boyutu **belirtilmemiş** (stimuli.pdf A4 yatay, 842x595 pt; çizgi aralığı veriden ≈ 11 mm).

### 5.3 Eksik, bozuk ve tekrarlanan kayıtlar [doğrulandı]

| Kontrol | Sonuç |
|---|---|
| Boş/okunamayan SVC | 0; NaN içeren dosya 0 |
| Zaman geriye giden dosya | 0 |
| Yinelenen dosya (MD5) | 0 |
| Tekrarlayan zaman damgası (Δt = 0) | 1287 dosyada toplam 23 455 satır (milisaniye çözünürlüğü; ayrıntı yok) |
| JSON ↔ SVC uzunluk farkı | 7 dosya (§3); 4'ünde değer farkı da var |
| `distorted_data.xlsx` (95 dosya, 66 çocuk, etiketli) | `extra_content` 42, `rotated` 18 (RCFT), `not_unlike` 11, `spiral_connection` 8, `repeated_tracing` 7, `corrupted` 3, `crossed_out` 2, `mixed_font` 2, `not_complete` 1, `incorrect_direction` 1. **Yazma görevlerinde 43 dosya** (çoğu `extra_content`: dikte 19, kopya 19) |
| Tekrarlayan katılımcı kaydı | 1 çocuk (2 satır, HLS dikte maddeleri farklı) |
| Kimlik uyuşmazlığı | 6 SVC-only, 6 bilişsel-only |
| Eksik etiket (HLS: yalnız kullanılabilir 275 çocukta; 289 satırda dikte 30, kopya 21) | `group` 8 (omit bayraklı), HLS dikte 16, HLS kopya 8, HPSQ-C 6, eleman değerlendirmesi 5–7, RCFT 7–8 |

`distorted_data.xlsx` etiketlerinin tanımı belirtilmemiş; `extra_content`'in yazma görevinde ne olduğu (ek yazı, imza, çizim) bakılarak doğrulanmadı.

## 6. Etiket analizi

Anlamlar **`Codebook.xlsx`**'ten; kod kitabında yazmayan her şey "belirtilmemiş". İstatistikler 275 kullanılabilir çocuk üzerinde. AUC: değişkenin HD grubunda daha yüksek olma olasılığı (0,5 = ayırmıyor); `group` zaten `special_care_type`'tan türetildiği için disgrafi bayrağı ile 0,99.

| değişken | aile | araç | ölçek (kod kitabı) | görev | n | eksik | ort (SD) | AUC (HD vs tipik) |
|---|---|---|---|---|---|---|---|---|
| `group` | tanı/grup | special_care'den türetilmiş ölçüt | 1 = el yazısı güçlüğü; 0 = tipik el yazısı gelişimi | tümü | 275 | 0 | 0.57 (0.50) |  |
| `special_care_type_dysgraphia` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.56 (0.50) | 0.99 |
| `special_care_type_dyslexia` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.11 (0.32) | 0.60 |
| `special_care_type_dysortographia` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.04 (0.19) | 0.53 |
| `special_care_type_dyspraxia` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.01 (0.09) | 0.51 |
| `special_care_type_dyscalculia` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.02 (0.15) | 0.52 |
| `special_care_type_diagnosis_ongoing` | tanı | SLD tanısı kaydı | 1/0 | tümü | 275 | 0 | 0.02 (0.13) | 0.50 |
| `special_care_type_typical_development` | tanı | SLD tanısı kaydı | 1 = hiçbir SLD yazılmamış | tümü | 275 | 0 | 0.42 (0.49) | 0.01 |
| `hpsqc_sum` | öz bildirim | HPSQ-C (10 madde) | 0–40 | genel (görevden bağımsız) | 269 | 6 | 13.99 (5.44) | 0.63 |
| `hpsqc_legibility_sum` | öz bildirim | HPSQ-C okunabilirlik faktörü (madde 1+2+10) | 0–12 | genel | 273 | 2 | 3.48 (2.25) | 0.66 |
| `hpsqc_performance_time_sum` | öz bildirim | HPSQ-C performans/süre faktörü (3+4+9) | 0–12 | genel | 273 | 2 | 5.61 (2.17) | 0.59 |
| `hpsqc_wellbeing_sum` | öz bildirim | HPSQ-C duygusal/fiziksel iyilik faktörü (5+6+7+8) | 0–16 | genel | 271 | 4 | 4.88 (3.04) | 0.56 |
| `hls_dictat_a_ledgibility` | yazı ürünü derecelendirmesi | HLS madde a: okunabilirlik (veride yazım hatalı sütun adı) | 1–5 (1 = tüm kelimeler okunur) | dictation | 259 | 16 | 2.73 (1.04) | 0.64 |
| `hls_dictat_b_effort` | yazı ürünü derecelendirmesi | HLS madde b: okuma çabası | 1–5 | dictation | 259 | 16 | 2.92 (1.10) | 0.64 |
| `hls_dictat_c_page_layout` | yazı ürünü derecelendirmesi | HLS madde c: sayfa düzeni | 1–5 (1 = çok iyi düzen) | dictation | 259 | 16 | 2.36 (0.85) | 0.57 |
| `hls_dictat_d_letter_formation` | yazı ürünü derecelendirmesi | HLS madde d: harf biçimi | 1–5 (1 = iyi biçimli) | dictation | 259 | 16 | 2.98 (1.01) | 0.68 |
| `hls_dictat_e_alterations` | yazı ürünü derecelendirmesi | HLS madde e: düzeltmeler/ek öğeler | 1–5 | dictation | 259 | 16 | 2.96 (1.00) | 0.55 |
| `hls_dictat_sum` | yazı ürünü derecelendirmesi | HLS toplam | 1–25 | dictation | 259 | 16 | 13.95 (4.27) | 0.64 |
| `hls_transcript_a_ledgibility` | yazı ürünü derecelendirmesi | HLS madde a: okunabilirlik | 1–5 | copy | 267 | 8 | 2.72 (1.13) | 0.73 |
| `hls_transcript_c_page_layout` | yazı ürünü derecelendirmesi | HLS madde c: sayfa düzeni | 1–5 | copy | 267 | 8 | 2.58 (0.95) | 0.68 |
| `hls_transcript_d_letter_formation` | yazı ürünü derecelendirmesi | HLS madde d: harf biçimi | 1–5 | copy | 267 | 8 | 3.13 (1.01) | 0.70 |
| `hls_transcript_sum` | yazı ürünü derecelendirmesi | HLS toplam | 1–25 | copy | 267 | 8 | 14.06 (4.49) | 0.75 |
| `bach_dictation_sum` | yazım hatası (ortografi) | BACH dictation, hata sayısı toplamı (4 değerlendirici) | 0–22 | dictation | 275 | 0 | 17.83 (14.28) | 0.83 |
| `dib_transription_sum` | yazım hatası (ortografi) | DIB transcription, hata toplamı (veride sütun adı yazım hatalı: transription) | kodlama yok | copy | 275 | 0 | 7.63 (6.05) | 0.73 |
| `element_speed_bs_sum` | grafomotor eleman değerlendirmesi | büyük spiral, hızlı (7 ölçüt, 0/1) | 0–7 | big-spiral-fast | 269 | 6 | 4.20 (1.35) | 0.44 |
| `element_speed_ss_sum` | grafomotor eleman değerlendirmesi | küçük spiral, hızlı | 0–7 | small-spiral-fast | 270 | 5 | 4.10 (1.34) | 0.42 |
| `element_speed_zz_sum` | grafomotor eleman değerlendirmesi | testere (zig-zag), hızlı | 0–7 | saw-fast | 270 | 5 | 4.75 (1.43) | 0.28 |
| `element_speed_ul_sum` | grafomotor eleman değerlendirmesi | üst döngüler, hızlı | 0–7 | upper-loops-fast | 269 | 6 | 4.16 (1.61) | 0.36 |
| `element_speed_ll_sum` | grafomotor eleman değerlendirmesi | alt döngüler, hızlı | 0–7 | lower-loops-fast | 269 | 6 | 3.10 (1.91) | 0.34 |
| `element_speed_r_sum` | grafomotor eleman değerlendirmesi | gökkuşağı, hızlı | 0–7 | rainbow-fast | 268 | 7 | 3.99 (1.47) | 0.36 |
| `element_speed_cl_sum` | grafomotor eleman değerlendirmesi | birleşik döngüler, hızlı | 0–7 | combined-loops-fast | 270 | 5 | 3.64 (1.74) | 0.35 |
| `element_precision_ss_sum` | grafomotor eleman değerlendirmesi | küçük spiral, hassas | 0–7 | small-spiral-precise | 270 | 5 | 4.03 (1.36) | 0.33 |
| `element_precision_ll_sum` | grafomotor eleman değerlendirmesi | alt döngüler, hassas | 0–7 | lower-loops-precise | 270 | 5 | 3.64 (1.77) | 0.38 |
| `element_precision_cl_sum` | grafomotor eleman değerlendirmesi | birleşik döngüler, hassas | 0–7 | combined-loops-precise | 270 | 5 | 3.51 (1.69) | 0.39 |
| `rcft_task001_sum_hs` | görsel-mekânsal | Rey karmaşık figür, kopya (36 puan) | 0–36 | RCFT-recognition (TSK1: kopya olup olmadığı dosya adından belirsiz) | 267 | 8 | 22.53 (7.30) | 0.29 |
| `rcft_task002_sum_hs` | görsel-mekânsal / bellek | Rey karmaşık figür, anlık hatırlama | 0–36 | RCFT-recall (TSK2) | 268 | 7 | 10.92 (6.17) | 0.37 |
| `bach_vda_sum_hs` | görsel-mekânsal | BACH görsel ayırt etme A | 0–60 | yok (kâğıt/test) | 270 | 5 | 24.13 (4.91) | 0.32 |
| `bach_vdb_sum_hs` | görsel-mekânsal | BACH görsel ayırt etme B | 0–60 | yok | 270 | 5 | 18.05 (5.05) | 0.27 |
| `wj_voc_sum_hs` | bilişsel | WJ-IV sözcük bilgisi | 0–59 | yok | 275 | 0 | 24.00 (5.72) | 0.44 |
| `wj_ns_sum_hs` | bilişsel | WJ-IV sayı serisi | 0–42 | yok | 275 | 0 | 22.06 (4.83) | 0.20 |
| `wj_va_sum_hs` | bilişsel | WJ-IV sözel dikkat | 0–37 | yok | 275 | 0 | 14.32 (3.45) | 0.25 |
| `bach_pa_d_sum_hs` | fonolojik | BACH fonolojik analiz | 0–16 | yok | 270 | 5 | 11.40 (3.23) | 0.53 |
| `bach_ps_b_sum_hs` | fonolojik | BACH fonolojik sentez | 0–16 | yok | 270 | 5 | 8.76 (3.68) | 0.40 |
| `bach_pm_a_sum_hs` | fonolojik | BACH fonem değiştirme | 0–14 | yok | 275 | 0 | 7.91 (4.12) | 0.30 |
| `mark_czech_1_numeric` | okul notu | Çekçe karne notu (yıl sonu) | 1–5 | yok | 258 | 17 | 1.69 (0.76) | 0.85 |


### 6.1 Etiket türleri arasındaki farklar (kod kitabı ve README'ye dayalı)
| Tür | Değişkenler | Ne olduğu | Ne olmadığı / belirsiz |
|---|---|---|---|
| **Klinik tanı kaydı** | `special_care_type*`, `current_care_type` | "SLD tanısı varsa türü" (kod kitabı); yalnız disgrafi/tipik/ongoing alakalı sayılmış | Tanıyı kimin, hangi yöntemle, ne zaman koyduğu **belirtilmemiş**; araştırma ekibinin değerlendirmesi olup olmadığı belirsiz |
| **Grup etiketi** | `group` | "special_care'den uyarlanmış el yazısı güçlüğü ölçütü" | Bağımsız bir test sonucu değil; tanı kaydından türetilmiş; şehir/toplama yeriyle örtüşüyor |
| **Tarama/öz bildirim** | `hpsqc_*` | Çocuklar için el yazısı yeterlik tarama anketi (10 madde, 0–4; okunabilirlik, süre, iyilik faktörleri); README özeti "self-reported handwriting proficiency" | Yanıtlayanın (çocuk/ebeveyn/öğretmen) madde düzeyinde belirtilmediği; klinik tanı değil |
| **Uzman/derecelendirici değerlendirme** | `hls_*`, `element_*`, `bach_dictation_*`, `dib_*`, `rcft_*` | Yazı/çizim ürününün puanlanması (HLS 1–5; eleman 0/1 ölçüt; hata sayıları) | HLS ve eleman değerlendiricilerinin kimliği/sayısı/güvenirliği **belirtilmemiş**; yalnız BACH/DIB için değerlendirici sütunları var |
| **Standart test puanı** | `wj_*`, `bach_p*`, `bach_vd*` | Bilişsel, fonolojik, görsel ayırt etme testleri | El yazısı ürününden bağımsız beceriler (madde içerikleri telifli, yayımlanmamış) |

Ürün odaklı etiketler (HLS: sayfa düzeni, harf biçimi, düzeltmeler; eleman ölçütleri; RCFT) statik görüntü analiziyle ilişkilendirilebilir; hız/basınç/hareket planlaması gerektiren kavramlar (HPSQ-C "performans süresi", dispraksi tanısı) görüntüden ölçülemez.
"Motor koordinasyon" için **ayrı bir test yok**; en yakınları eleman görevleri puanları ve dispraksi/ortopedi/nöroloji kayıtları (dispraksi 2 çocuk, `current_care_type`'ta nöroloji/ortopedi toplam 4).
"Sayfa düzeni ve harf biçimi": HLS c ve d maddeleri (dikte ve kopya için ayrı).

## 7. Koordinat → PNG prototipi

Kod: `src/handwriting/diagramo/` (`io.py` okuma, `render.py` dönüşüm, `samples.py` örnek seçimi/eşleştirme, `eda.py` envanter, `labels.py` etiket tablosu); testler `tests/test_diagramo.py` (15 test; 3 mutasyon denemesiyle: pen durumunu yok sayma, y çevirmesini kaldırma, çizgi kalınlığını ölçeğe bağlama testler tarafından yakalandı).

| İlke | Uygulama |
|---|---|
| Yüzeye temas | Yalnız `pen == 1` noktaları çizilir; havadaki noktalar çizilmez |
| Bağımsız çizgiler | Yeni vuruş: pen 0→1, zaman boşluğu > 0,05 s ya da ardışık nokta mesafesi > 10 mm; vuruşlar birbirine bağlanmaz (testle doğrulandı); tek noktalı vuruş nokta olarak çizilir |
| Eksenler/birimler | x, y mm; y yukarı → görüntüde çevrilir (`y_up=True`); EDA kanıtları §5.2 |
| Ölçek | **Fiziksel mod:** mm başına piksel sabit (yazma için 5 px/mm ≈ 127 dpi), örnek kendi sınırlarına göre kırpılır (kenarlık 8 mm), en-boy ve yazı boyutu (mm) korunur. **Sığdırma modu** (`fit_px`): tek ölçekle uzun kenar sabit, en-boy korunur. Her örnek bağımsız; veri seti istatistiği kullanılmaz |
| Sayfa boyutu | Kayıtta yok; `canvas="tablet"` ile tablet etkin alanı (348,16 x 203,2 mm) çizilebilir |
| Görünüm | Beyaz arka plan, siyah, **sabit** çizgi kalınlığı (3 px), 2x alt örnekleme ile yumuşatma |
| Bütün görev | Tüm kayıt tek görüntü; ek metin/imza ayrıştırılmaz |
| Eşleştirme | `manifests/samples.csv`: görüntü, katılımcı, görev, SVC yolu, ölçek, boyut, vuruş sayısı, etiketler (group, tanı bayrakları, HLS toplamları, sayfa düzeni, harf biçimi, HPSQ-C, yaş, sınıf, cinsiyet, okul, toplama yeri) |

**Örnek görüntüler (16, yerel):** `data/handwriting/diagramo/processed/images/` altında `<katılımcı>_<görev>.png` + `_contact_sheet.png`; katılımcı eşleştirmesi yerel `manifests/samples.csv`'de (belgede katılımcı kodu verilmez). Seçim: 4 yazma görevi (dikte-3/4, kopya-3/4) x 2 grup (8), dikte-4 ve kopya-4'te HLS toplamının en düşük ve en yüksek olduğu çocuklar (4), eleman görevleri (büyük spiral, testere, birleşik döngüler, hassas alt döngüler; 4); katılımcı tekrarı yok.

**Doğrulama:** (1) birim testleri (fiziksel ölçek ± 0,6 mm, kalem kalkınca boşluk, y yönü, sabit kalınlık, tablet tuvali, en-boy); (2) **görsel kontrol**: yazılar okunur (Çekçe cümleler), düzgün yönde; HLS'in en yüksek (kötü) uçları belirgin karalama/üzeri çizme içeriyor, en düşük uçlar düzgün; (3) fiziksel makullük (hız, satır aralığı §5.2).
**Sınırlamalar:** kâğıt çizgisi yok; çizgi kalınlığı sabit (gerçek mürekkep basınca bağlı kalınlık gösterir); renk/arka plan/gürültü yok; `extra_content` kayıtları (yazma görevlerinde 38) ek vuruşlar içerir ve ayıklanmadı; dikte süresi boyunca havada hareket çizilmez; JSON yerine ham SVC kullanılır.

## 8. Model eğitimi fizibilitesi

### 8.1 Soruların yanıtı

| Soru | Yanıt |
|---|---|
| **Hangi etiketler supervised öğrenme için kullanılabilir?** | **Uygun:** HLS maddeleri (dikte n = 259, kopya n = 267; ordinal 1–5; özellikle c sayfa düzeni, d harf biçimi, e düzeltmeler, ayrıca toplam), eleman görevi ölçüt puanları (n ≈ 270/eleman; 0–7), RCFT kopya puanı (n = 267; çizim). **Koşullu/riskli:** `group` ve tanı bayrakları (şehir/okul/zaman karıştırıcısı; dispraksi 2, disortografi 10, diskalkuli 6 çocuk: çok az). **Uygun değil:** WJ-IV, BACH fonolojik/görsel ayırt etme, okul notları, BACH/DIB yazım hataları (içerik/dil; geometri değil), HPSQ-C (öz bildirim, ürün değil) |
| **Hangi yazı görevleri yeterli?** | Dikte ve kopya birlikte **270 çocuk / 530 kayıt** (153 HD / 117 tipik) (aynı çocuğun iki kaydı bağımlı). Sınıf sürümü başına 110–156 çocuk: sıfırdan derin ağ için çok az; hazır görüntü özellikleri/küçük başlık ya da el yapımı özelliklerle uygulanabilir. Eleman görevleri örnek sayısı bakımından benzer (≈ 270) ama metin değil |
| **Statik görüntüden hangi özellikleri öğrenebiliriz?** | Boyut, hizalama, satır organizasyonu ve sayfa kullanımı, harf biçimi, düzeltme/üzeri çizme yoğunluğu, vuruş yoğunluğu. **Öğrenilemez:** hız, basınç, eğim, vuruş sırası, kalem kaldırma, süre |
| **Hangi etiketler statik analizle ilişkilendirilebilir?** | HLS c/d/e maddeleri doğrudan ürüne ait; ön kontrol: ham mürekkep uzunluğu (koordinatlardan, statik bir nicelik) HLS toplamıyla Spearman **0,34 (dikte-3) – 0,52 (dikte-4), 0,42 (kopya-3) – 0,66 (kopya-4)**; sayfa düzeni için 0,39–0,55 (yalnız dikte için hesaplandı; ön gözlem: kendi başına anlamlı bir sinyal olduğunu gösterir, ama karalama/düzeltme ve yazı boyutunu birlikte yakalar). `group` ile HLS toplamı AUC 0,64–0,75, yani HLS'in disgrafi grubunu ayırma gücü orta |
| **Koordinattan üretilen görüntü ↔ gerçek fotoğraf farkı model eğitimini nasıl etkiler?** | Büyük alan farkı: (1) kâğıt çizgisi/lekeler/gölge/perspektif/çözünürlük yok; (2) sabit çizgi kalınlığı (gerçekte kalem ve basınca bağlı); (3) tek renk, kusursuz bölütleme; (4) Çekçe cümleler, 8–12 yaş, tablet üstündeki kâğıt (FD-LEX: Almanca, 9–17 yaş, tarama). Doğrudan eğitilen model gerçek fotoğrafta güvenilmez; riski azaltmak için: gerçekçi render (çizgili kâğıt, mürekkep kalınlığı/bulanıklık, gürültü, perspektif) ve **alan rastgeleleştirme**, dilden/bağlamdan bağımsız **geometrik özellikler**, ve gerçek fotoğraflarda (en azından etiketsiz, FD-LEX ile) ayrı doğrulama |
| **Model, nihai uzman raporuna somut ne katar?** | (a) **Özellik geçerliliği:** kendi geometrik ölçümlerimizin (boyut, hiza, sayfa kullanımı) uzmanların sayfa düzeni/harf biçimi puanlarıyla ilişkisini göstermek (eğitim gerektirmez); (b) rapora **destekleyici gösterge** (ör. "bu örnek, uzman derecelendirmesinde sayfa düzeni açısından yüksek puan alan yazılara benzer"), belirsizlik ve sınırlama notuyla; (c) kalite bayrakları (karalama/düzeltme yoğunluğu). **Tanı veya okunabilirlik sonucu verilmez** |

### 8.2 Uygulanabilir model alternatifleri

| # | Girdi | Hedef | Çocuk (n) | Algoritma seçenekleri | Metrik | Sınırlamalar | Değerlendirme |
|---|---|---|---|---|---|---|---|
| A | **Geometrik özellik doğrulaması** (model yok): koordinat-PNG'den kendi ölçümlerimiz | HLS c/d/e maddeleri | dikte 259, kopya 267 | Spearman, kısmi korelasyon (yaş/sınıf/metin sürümü sabit), karma model | Spearman ρ, GA | Rendering ile fotoğraf farkı; derecelendirici belirsizliği | **Önerilen ilk adım** |
| B | Görüntü (render) ya da özellik vektörü | HLS maddeleri (sıralı 1–5) veya toplam | 259–267 | Ridge/sıralı lojistik; gradyan artırma; hazır CNN/ViT özellikleri + doğrusal başlık | Spearman, QWK, MAE; tabanlar: ink uzunluğu, boyut | Az örnek; tek değerlendirici belirsiz; ordinal gürültü; render → fotoğraf alan farkı | Aday (A sonuçlarına bağlı); okul-bazlı gruplu CV |
| C | Render görüntü | `group` (HD vs tipik) | 270 (153 / 117) | Lojistik, gradyan artırma, CNN | AUROC, dengeli doğruluk, kalibrasyon | **Şehir/okul/zaman karıştırıcısı**: tipiklerin tamamı `city1`; şehir içi yalnız 118 tipik / 9 HD; karışık 5 okulda 50 / 8 | **Şimdilik yapılmaz**; yapılacaksa meta veri (şehir, tarih) tabanı ile kıyas şart |
| D | Eleman görüntüsü (spiral, döngü, testere) | Eleman ölçütleri (0/1) ve 0–7 toplam | ≈ 270 / eleman | Sınıflayıcı/sıralı regresyon, hazır görüntü özellikleri | AUROC/QWK, Spearman | Metin değil; nihai uygulama metin fotoğrafı alacak | İkincil/yan görev (ileride spiral yükleme istenirse) |
| E | RCFT kopya çizimi | RCFT kopya puanı (0–36) | 267 | Regresyon | Spearman, MAE | Çizim görevi, telifli figür; el yazısı değil | Kapsam dışı (görsel-mekânsal çalışma ayrı) |
| F | Özellikler | Tanı alt türleri (disleksi, disortografi, dispraksi, diskalkuli) | 31 / 10 / 2 / 6 | – | – | Örnek yok, el yazısı ürünü ilişkisi belirsiz | Uygun değil |
| G | Etiketsiz görüntü/özellik | – (kümeleme, temsil öğrenme, alan farkı ölçümü) | 270 + FD-LEX (etiketsiz) | Otokodlayıcı, kümeleme | Alan uyumsuzluğu ölçüleri | Etiket yok; yorum yok | Alan farkı analizi için yardımcı |

Bölme (tüm alternatifler): **okul-gruplu** (35 okul; aynı çocuğun dikte+kopyası aynı katmanda); karıştırıcıya karşı şehir ve toplama dönemi kovaryatları raporlanır; gerçek fotoğraf doğrulaması ayrı.

### 8.3 Hedefi seçerken (karar sizde)
- HLS maddeleri (A/B) **mevcut etiketlerin niteliğine en uygun** hedeflerdir: ürüne dayalı, ordinal, grup karıştırıcısına göre daha az doğrudan bağımlı (yine de doğrulanmalı: derecelendirici ve şehir etkileri belirtilmemiş).
- Disgrafi/HD sınıflandırması (C) bu veri setiyle karıştırıcılar giderilemediği için kesinleştirilmemeli.
- Okunabilirlik ana hedef olarak alınmadı; HLS "okunabilirlik" ve "çaba" maddeleri yalnız yardımcı kalır.
- Hız, basınç, hareket sırası girdi olarak kullanılmaz (statik fotoğrafta yok).

## 9. Açık sorular ve sonraki adımlar
1. HLS ve eleman değerlendiricileri (kim, kaç, güvenirlik), tanıların kaynağı ve yöntemi: makale/yazarlar (K. Zvončáková).
2. `extra_content` (yazma görevlerinde 38 kayıt) ve `distorted_data` etiketlerinin tanımı; görsel kontrol.
3. 6 + 6 kimlik uyuşmazlığının nedeni.
4. Adım A: koordinat-PNG üzerinde mevcut el yazısı hattı (`src/handwriting`) ile özellik çıkarma + HLS karşılaştırması; kâğıt çizgisi ve fotoğraf benzeri bozulmalar ekleyen gerçekçi render.
5. Bütün yazma kayıtlarının (530) dönüştürülmesi (henüz yapılmadı; ≈ dakikalar).
