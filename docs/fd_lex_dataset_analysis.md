> **PASİF (2026-11-27):** el yazısı modülü artık DiaGraMo ile sürüyor; FD-LEX Scriptoria ve Malaysian çalışmaları pasif/arşiv durumunda (dosya ve kod silinmedi, kullanılmıyor). Güncel belge: `docs/el_yazisi_diagramo_deney.md`. Karar: `docs/kararlar.md`.

# FD-LEX Scriptoria veri seti analizi (Aşama 1 denetim + Aşama 2 ön fizibilite)

Tarih: 2026-11-25. Notebook: `notebooks/fd_lex_eda.ipynb` (çıktılar içinde). Sayfa tablosu: `data/handwriting/fd_lex/manifests/pages.csv`
(5656 satır, git'e girmez). Malaysian çalışması ve çizim modülü değişmedi (`docs/handwriting_dataset_analysis.md`, `notebooks/handwriting_eda.ipynb`).

Etiketler: **[doğrulandı]** dosyalardan ölçüldü. **[yayında]** web kaynaklarında (FD-LEX sayfaları, Collection Policy) yazıyor, dosyadan doğrulanamadı.
**[bilinmiyor]** ne dosyada ne bulduğum kaynaklarda var. **[hipotez]** gözleme dayanıyor ama kanıtlanmadı.

Kısıtlara uyum: model eğitilmedi; sayfa görüntüsü diske yazılmadı (yalnız 288 örnek sayfa bellekte 100 dpi işlendi, geçici küçük resimler bellekte);
ham veri değişmedi; `data/` git tarafından yok sayılıyor (`.gitignore` satır 223, `git check-ignore` ile doğrulandı). Kullanım izni alınmış **varsayılmadı** (bölüm 5).
Ortam notu: PyMuPDF ve openpyxl `.venv`'e kuruldu; `requirements.txt` değiştirilmedi (karar bekliyor).
Gizlilik notu: her kapak sayfasında PDF'i indiren kullanıcının adı yazıyor; manifest ve notebook bu satırı **saklamıyor** (kontrol edildi).

## Özet

- 8 PDF, 5664 sayfa: 8 kapak + **5656 yazı sayfası**; kapakta toplam kayıt (Hits) **5628** = 938 öğrenci x 6 yazı. 28 fazladan sayfa çok sayfalı/çift sayfalardan.
- **Öğrenci kodu metin katmanında var, OCR gerekmedi:** 5656 sayfanın 5656'sı Excel'deki 938 koddan biriyle eşleşti (%100; 1 sayfada bozuk kod "neu:" satırından düzeltildi), her Excel öğrencisinin sayfası bulundu.
- **Metadata zengin:** sınıf (5/9), grup (kontrol/müdahale), okul türü, yaş (ay), cinsiyet, dil geçmişi, Almanca notu, 6 yazı için kelime sayısı ve "Rating". Malaysian'da bunların hiçbiri yoktu.
- **Öğrenci bazlı bölme mümkün** (938 benzersiz kod; her öğrencinin sayfaları ardışık blokta). Okul/sınıf düzeyinde sızıntı için kodun ilk 4 karakteri küme olarak kullanılabilir (**[hipotez]**: sınıf/okul).
- **Sayfa → (görev, zaman) eşlemesi** PDF'te yazmıyor; sıra Ber1, Arg1, Ber2, Arg2, Ber3, Arg3 olarak **iki bağımsız yolla doğrulandı** (bölüm 4), ama 27 öğrencide (6 sayfadan farklı) belirsiz.
- Görüntüler gerçek **A4 tarama**: 150/200/300 dpi, çoğu renkli; hepsi aynı çizgili formda; **çizgi aralığı 10,8 mm (±0,1)** tüm sayfalarda → fiziksel ölçek ve ortak normalleştirici var. Malaysian'da ölçek yoktu.
- Ölçümler (n=288 örnek sayfa, doğruluk referansı yok): harf boyutu, satır hizası, eğim, sayfa kullanımı hesaplanabiliyor; kelime aralığı kaba kalıyor. Karıştırıcılar çok (üzeri çizilmiş kelimeler, anonimleştirme "XXX" yazısı, kod kutusu, not yazıları, kalem türü, tarama çözünürlüğü/rengi).
- **Rating'in anlamı belgelenmemiş**; el yazısı kalitesi etiketi olarak kullanılamaz.
- **Kullanım izni ve lisans bilinmiyor.** Kayıt gerektiriyor **[yayında]**; bu çözülmeden veriyi Drive/Colab'a yüklememek öneriliyor.

## 1. PDF dosyaları ve kapaklar [doğrulandı]

| PDF | Sayfa | MB | Kapak "Datei" |
|---|---|---|---|
| Originaltext_01 | 714 | 234 | 1/8 |
| _02 | 708 | 216 | 2/8 |
| _03 | 713 | 217 | 3/8 |
| _04 | 707 | 236 | 4/8 |
| _05 | 707 | 272 | 5/8 |
| _06 | 704 | 372 | 6/8 |
| _07 | 708 | 434 | 7/8 |
| _08 | 703 | 419 | 8/8 |

- Her PDF'in ilk sayfası kapak ("DECKBLATT, Scriptoria, Datei n / 8, Hits: 5628", atıf: Becker-Mrotzek/Grabowski 2018, DOI 10.18716/FD-LEX/861). Sekiz kapağın metni (dosya numarası ve kullanıcı satırı hariç) aynı.
- **Kapakta filtre ya da seçim ölçütü yok:** yalnızca korpus adı, dosya sırası, toplam kayıt sayısı ve atıf. "Filtre" bilgisi Excel dosyasının adında ("Selektion_Kopfdaten") ima ediliyor ama içeriği yalnızca öğrenci tablosu.
- Üretici: iText 4.2.0; PDF'lerin oluşturma tarihi 2026-11-25 (indirme/dışa aktarma zamanı, yazıların tarihi değil).
- Toplam 5664 sayfa, kapak hariç 5656. 5628 yazıya karşı 28 fazladan sayfa (bölüm 3).
- Korpusun yayındaki tanımı: 5628 metin, 938 öğrenci, 5. ve 9. sınıf, Köln ve Hannover, 09.2013–06.2015, üç ölçüm zamanında ikişer metin (argüman ve rapor), el yazısı orijinallerin taramaları ve normalize transkriptler **[yayında]**. Transkript bu PDF'lerde yok (yalnız taramalar).

## 2. Excel metadata (`Datentabelle.xlsx`) [doğrulandı]

Tek sayfa `Selektion_Kopfdaten`, 938 satır x 23 sütun, `Code` benzersiz (937 kod 8, 1 kod 9 karakter).

| Sütun | İçerik | Eksik |
|---|---|---|
| Code | öğrenci kodu | 0 |
| Klassenstufe | KLASSE_5 (495), KLASSE_9 (443) | 0 |
| Gruppe | KONTROLLGRUPPE 472, INTERVENTIONSGRUPPE 466 | 0 |
| Schulform | GYMNASIUM 531, IGS 407 | 0 |
| Alter in Monaten | sınıf 5: ort. 129 (109–155); sınıf 9: ort. 178 (161–202) | 1 |
| Geschlecht | WEIBLICH 485, MAENNLICH 453 | 0 |
| Sprachbiographie | NUR_DEUTSCH 535, DEUTSCH_PLUS_ZWEITSPRACHE 202, DEUTSCH_ALS_ZWEITSPRACHE 201 | 0 |
| Deutschnote | 1–5 | 15 |
| AlphabetTask (4–37), SLS (0–70), Wortschatz (0–30) | **anlamı belgelenmemiş [bilinmiyor]**. Adlara göre test puanı olabilir; "AlphabetTask" el yazısı akıcılığıyla ilgili olabilir (**[hipotez]**), kod kitabı gerekli | 3 / 0 / 2 |
| Textlänge_{Ber,Arg}_MZP{1,2,3} | altı sütun; yayında "yazılan kelime sayısı" **[yayında]**; ortalama 46–89 | 0 |
| Rating_{Ber,Arg}_MZP{1,2,3} | altı sütun, 0–6, 0,5 adım | 0 |

Sınıf x okul türü x grup (öğrenci): sınıf 5 Gymnasium 136 müdahale / 148 kontrol, IGS 105 / 106; sınıf 9 Gymnasium 119 / 128, IGS 106 / 90.

### Rating ve değerlendirme sütunlarının anlamı
- Değerler 0–6 arası, 0,5 adımlı; ortalama 3,5–4,1 (MZP'ye göre artıyor).
- Rating ile aynı yazının kelime sayısı arasında orta düzey ilişki (Spearman 0,34–0,58); aynı öğrencinin farklı yazılarının ratingleri arasında 0,28–0,42.
- Ratingin neyi derecelendirdiği (içerik, dil, bütünlük, el yazısı?) ne Excel'de, ne PDF'lerde, ne de bulabildiğim yayınlarda yazıyor **[bilinmiyor]**. Kelime sayısıyla ilişkisi onun yazının içeriği/dil kalitesiyle ilgili olabileceğini düşündürüyor (**[hipotez]**), el yazısı okunaklılığı etiketi olarak varsayılmadı ve kullanılmamalı.
- Diğer kısaltmalar (SLS, AlphabetTask) için de aynı: kod kitabı ya da yayın gerekir.

## 3. Sayfalar, öğrenci kodları, eşleşme [doğrulandı]

- **Kod çıkarma:** sayfa metin katmanı yalnızca iki satır: öğrenci kodu ve telif satırı. Kod, "©" satırının hemen üstündeki satır. OCR gerekmedi.
- Bazı sayfalarda ek metin: **236 sayfada (220 öğrenci) "XXX"** (anonimleştirme işareti, imza yerine sayfaya basılmış siyah yazı; bölüm 6); 10 sayfada başka ek satırlar (1 sayfada bozuk OCR benzeri metin katmanı). 1 sayfada kod 7 karakter (bir karakter eksik) ve altında "neu:" ile düzeltilmiş kod var; düzeltmeyle çözüldü.
- **Eşleşme:** 5656/5656 sayfa (%100) bir Excel koduna eşleşti; 938/938 Excel öğrencisinin sayfası var (%100). Komşudan çıkarım gerekmedi.
- **Öğrenci başına sayfa:** 6 sayfa 911 öğrenci; 7 sayfa 21; 8 sayfa 3; 9 sayfa 1; 5 sayfa 2. Toplam 5656 = 938 x 6 + 28.
  Fazladan sayfa nedenleri: bir yazının iki sayfaya taşması **[hipotez]**, 1 öğrencide aynı sayfa iki kez (aşağıda) ve PDF sınırında bölünen bloklar. 5 sayfalı 2 öğrencide bir yazı eksik ya da tek sayfada **[bilinmiyor]**.
- **Öğrenci blokları ardışık:** hiçbir kod birden çok ayrı blokta geçmiyor.
- **PDF'ler arası:** 5 öğrenci iki PDF'e bölünmüş (öğrenci B: PDF01 sonu + PDF02 başı; öğrenci C: 02/03; öğrenci D: 05/06; öğrenci E: 04/05; öğrenci F: 07/08); hepsi PDF sınırında, yani sayfa örtüşmesi değil kesim. Öğrenci bazında bölme yapılırken PDF'e göre değil koda göre gruplanmalı.
- PDF sırası Excel satır sırasını izlemiyor (Spearman 0,54, 9 sıra bozulması): sıra bağımlı varsayımlar yapılmamalı.

### Tekrar ve örtüşme
- **Birebir kopya:** 1 çift: PDF06 sayfa 177 ve 181 (öğrenci A), aynı görüntü akışı (SHA-1 ve küçük resim korelasyonu 1,00). Aynı öğrencide. **Düzeltme (2026-11-25, plan denetiminde):** bu öğrenci 6 sayfalı gruptadır (6 sayfa, biri kopya), yani 28 fazladan sayfanın parçası değil; tekilleştirilince 5 sayfa kalır ve görev/zaman eşlemesi belirsiz olur (belirsiz öğrenci sayısı 27 değil 28). `pages.csv`'deki varsayım sütunu bu öğrenci için yanlış doldurulmuştu.
- **Yaklaşık kopya (küçük resim korelasyonu, aynı boyutlu sayfalar arasında):** başka 0,98 üstü çift yok; 0,95 üstü 686 çift. En benzer çiftler gözle incelendi: farklı öğrencilerin soluk/az yazılı sayfaları, aynı çizgili form yüzünden benzer; kopya değil. Küçük resim yöntemi 5356 JPEG sayfada yapıldı; 300 sayfa (FlateDecode, 60'ı ikili) birebir hash dışında karşılaştırılmadı.
- **PDF'ler arası veri örtüşmesi:** öğrenci düzeyinde yok (aynı öğrenci yalnızca yukarıdaki 5 sınır kesimi dışında tek PDF'te). Aynı sayfa başka PDF'te tekrar etmiyor (hash).

### Öğrenci bazlı bölme
- **Mümkün [doğrulandı]:** kod benzersiz, tam eşleşme, her öğrencinin sayfaları tek blokta. Bölme öğrenci koduna göre yapılmalı (6 sayfa/öğrenci bağımlı).
- **Daha sıkı sızıntı kontrolü:** kodun ilk 4 karakteri (49 küme, medyan 20 öğrenci) sınıf düzeyi ve müdahale grubuyla temiz örüntü veriyor (örn. "51–56" yalnızca sınıf 5, "90–97" yalnızca sınıf 9; 2. karakter K/H okul türüyle tutarlı). Bunun okul/sınıf olduğu **[hipotez]**; kod kitabı yok. Küme bazında bölme sınıf içi sızıntıyı azaltır ama sınıf düzeyine göre stratifikasyonu zorlaştırır (küme sınıfa özgü).

## 4. Yazma görevi ve ölçüm zamanı

- Yapı **[doğrulandı: Excel + yayın]:** 2 görev (Ber = olay/kaza raporu "Unfallbericht", Arg = "Meine Meinung zur Schuldfrage", sonra okul spor aletleri hakkında Frau Große'ye mektup) x 3 ölçüm zamanı (MZP1–3). Her yazı için kelime sayısı var. Gerçek tarihler ve MZP arası süre **[bilinmiyor]** (çalışma 09.2013–06.2015 **[yayında]**).
- **Sayfa sırası hipotezi:** öğrencinin 6 sayfası sırayla Ber1, Arg1, Ber2, Arg2, Ber3, Arg3. Sınama:
  1. **Görsel:** 6 rastgele öğrenci x 6 sayfa başlığı: 1. ve 2. sayfalarda basılı "Unfallbericht" / "Meine Meinung zur Schuldfrage", 3–6. sayfalarda aynı türde yazılar, 2./4./6. sayfalar mektup formunda ("Sehr geehrte/Liebe Frau Große"). Bir öğrencide sayfada elle yazılmış "WZ: 40" / "WZ: 22" notları Excel'deki Ber1=40, Arg1=22 ile eşleşiyor.
  2. **Sayısal:** 288 örnek sayfada mürekkep miktarı ile Excel kelime sayısı arasındaki Spearman: her sayfa konumunun en yüksek korelasyonu beklenen sütunla (6/6). Köşegen ortalaması 0,69, köşegen dışı 0,41.
  Sonuç: sıra büyük olasılıkla doğru; yine de bu **sayfa başına garanti değil**. Tam 6 sayfalı olmayan 27 öğrencide eşleme belirsiz; manifestte `gorev_zaman_varsayim` yalnız tam 6 sayfalı öğrencilere dolduruldu (**varsayım sütunudur**).
- Ratingler ve kelime sayıları görev/zamana göre farklı dağılıyor (Ber MZP1 ort. 67 kelime, Arg MZP1 46, Ber MZP3 89): referanslar **görev x zaman** bazında kurulmalı. Arg2/Arg3 ve diğerleri farklı metin türleri (mektup), düzen farklı olabilir.

## 5. Kullanım izni, lisans ve etik [doğrulandı / yayında / bilinmiyor]

- Kapakta "Zitationsvorgabe" (atıf) var; **lisans metni yok** [doğrulandı].
- FD-LEX erişimi **kayıt gerektiriyor** ve Collection Policy'de ayrı kullanım koşulu yok, portala yönlendiriyor **[yayında]**. Veri setinin lisansı/kullanım koşulları bulduğum kaynaklarda **[bilinmiyor]**. Her kapakta indiren kişinin kişisel hesabı kayıtlı: veri kişisel hesapla alındı, bu iznin proje, yayın ve paylaşıma yetip yetmediği belli değil.
- **Çözülmesi gerekenler (sorulacak yer: FD-LEX / Mercator-Institut iletişim adresi, **[yayında]**):**
  1. Verinin bitirme projesinde (akademik, ticari olmayan) kullanımı için izin ve koşullar.
  2. **Paylaşım/yükleme:** projenin iş akışı veriyi Google Drive'a ve Colab'a koyuyor (`CLAUDE.md`). Üçüncü taraf bulut hizmetine yükleme izne tabi olabilir; izin netleşene kadar FD-LEX verisini Drive'a/Colab'a yüklememeyi öneririm (karar sizde).
  3. **Çocuk el yazısı ve kodlar:** reşit olmayan öğrencilerin el yazıları; sayfalarda öğrencinin elle yazdığı kod ve pseudonim kodu var, imzalar "XXX" ile maskelenmiş. Rapor ve sunumlarda örnek sayfa göstermek için ayrıca izin gerekebilir (Almanya'da çocuk verisi; GDPR kapsamı, hukuki değerlendirme yapılmadı).
  4. Türetilmiş çıktıların (ölçüm tabloları, referans dağılımları) paylaşılması.
- Kodda ve belgede kullanıcı hesabı adı saklanmadı; PDF'ler git dışında.

## 6. PDF içindeki görüntüler [doğrulandı]

- Her yazı sayfası A4 (≈595x842 pt) ve içinde **tek bir gömülü tarama görüntüsü** (3 sayfada 2–4 görüntü, parça parça).
- Renk: DeviceRGB 3879, ICCBased 1375, DeviceGray 342, **Indexed 1 bit (ikili) 60**; hepsi 8 bit, ikili olanlar hariç.
- Sıkıştırma: 5356 sayfa JPEG (DCT), 299 FlateDecode (gri ve ikili sayfaların bir kısmı), 1 sayfa karma.
- **Etkin çözünürlük** (görüntünün uzun kenarı / A4 uzun kenarı): ~300 dpi 2950 sayfa (3508x2480 ve 2480x3507), ~200 dpi 1897 (1653x2338), ~150 dpi 807 (1754x1240), <120 dpi 2 sayfa; 48 sayfa 3307x4677.
- Dosya boyutu (görüntü akışı) PDF'e göre medyan 233–509 KB: PDF'ler arasında tarama/sıkıştırma kalitesi farklı.
- **Sayfa dönüşü:** 1807 sayfa 270°, 147 sayfa 180°, 6 sayfa 90° /Rotate bayrağıyla saklı; `get_pixmap` dönüşü uygulayınca sayfalar dik çıkıyor (her dönüşten 2 örnek gözle kontrol edildi). Gömülü görüntünün kendisi dönük olabilir; doğrudan görüntü çıkarılırsa dönüş uygulanmalı.
- **Tarama biçimi sınıf ve PDF ile karışık:** PDF01–04 yalnız sınıf 5 (01 ve 02 yalnız kontrol, 04 yalnız müdahale, 03 çoğunlukla müdahale), PDF05 karışık (153 sınıf 5 + 553 sınıf 9), PDF06–08 yalnız sınıf 9 (06 kontrol, 08 müdahale). ~300 dpi sayfaların oranı sınıf 5'te yaklaşık %30, sınıf 9'da yaklaşık %78; gri/ikili sayfalar (402) çoğunlukla sınıf 9 (gri) ve sınıf 5 (ikili). Yani çözünürlük ve renk, sınıf ve grupla birlikte değişiyor. Sınıf bazlı referanslar tarama farkını da taşır.

## 7. Aşama 2: ön fizibilite

Örneklem: her PDF'ten 6 öğrenci, yalnızca tam 6 sayfalı olanlar (48 öğrenci, 288 sayfa; sınıf 5: 26, sınıf 9: 22 öğrenci), seed 42. 100 dpi, bellekte. Yöntem: kâğıt çizgileri yatay açma ile bulunup çıkarıldı, kalan mürekkep üzerinde ölçüm. **Doğruluk için referans etiket yok;** "uygulanabilir" = hesaplanıyor ve gözle makul, "doğru" demek değil. Küçük örneklem: sayısal değerler yön göstermek içindir.

Ortak bulgular:
- Çizgili form her sayfada aynı: 288/288 sayfada 21–25 çizgi (medyan 23), **aralık medyan 10,8 mm (10,2–10,9)**. Çizgi bulma sorunsuz (renk uzayına göre başarısızlık yok). Bu fiziksel ölçek ve satır konumu için güçlü bir dayanak.
- Tarama eğikliği küçük: |açı| medyan 0,15°, en fazla 0,55° (yine de düzeltildi).
- Mürekkep renkli sayfalarda neredeyse hep mavi tonlu (renkli mürekkebin %96–100'ü mavi tonda); örnek sayfaların %83'ünde (240/288) mürekkebin yarısından fazlası renkli ayırt edilebiliyor (RGB sayfalarda %97, ICC sayfalarda %82 medyan renkli oran); gri/ikili sayfalarda renkten ayırma yok (ölçüm tamamen gri düzeyine dayanıyor).

| Ölçüm | Sonuç (n=288 sayfa) | Karar |
|---|---|---|
| **Harf boyutu ve tutarlılığı** | Bağlı bileşen yüksekliği medyan 2,79 mm (IQR ≈ 2,5–3,3), sayfa içi dağılım genişliği (IQR/medyan) medyan 0,56. Öğrenci içi tutarlılık: ICC(1) 0,55 (harf boyutu), 0,47 (dağılım genişliği); yani öğrenci farkı baskın. | **Uygulanabilir (mm ölçeğiyle).** Ama bileşen ≠ harf: bitişik yazıda birden çok harf bir bileşen, çizgiyle kesişen harfler bölünüyor. Doğru ölçü (x-yüksekliği) satır/taban çizgisi bölütlemesi ve elle doğrulama ister. |
| **Kelime aralıkları** | Sütun boşluklarının harf yüksekliğine oranı medyan 0,30 (dağılım geniş: 0,08–2,92); eşiğe göre "geniş boşluk" sayfa başına medyan 69. Öğrenci içi tutarlılık ICC 0,12 (düşük). | **Kısmen / zayıf.** Harf içi boşluk ile kelime boşluğu ayrımı yok; bitişik yazı, üzeri çizilmişler, "XXX" bunu bozuyor. Gerçek kelime bölütlemesi gerekir. |
| **Satır hizası, çizgiye uyum** | Satır merkezinin çizgiye göre konumu medyan −0,24 satır aralığı (yazı çizgiden biraz yukarıda), satırlar arası SD medyan 0,03 (çok düzgün); kullanılan satır oranı sınıf 5: 0,35, sınıf 9: 0,52. ICC(1) 0,11 (SD), 0,26 (kullanılan satır). | **Uygulanabilir (geometrik olarak).** Düzensizlik ölçüsü ayırt edici mi bilinmiyor; "kullanılan satır oranı" yazı uzunluğuna bağlı, görev ve uzunlukla normalleştirilmeli. |
| **Yazı eğimi** | Satır içi eğim: medyan 0,05°, satırlar arası SD medyan 0,26°; sayfa eğikliği çıkarıldıktan sonra. ICC(1) 0,15 (medyan eğim), 0,09 (SD). | **Uygulanabilir, ama gürültülü.** Öğrenciye özgü kararlılık düşük: ölçüm gürültüsü mü gerçek değişim mi ayrılamadı. "Harf eğimi" (italik açısı) ölçülmedi. |
| **Sayfa organizasyonu** | Sol kenar boşluğu medyan 18,5 mm (8–42), kullanılan satır oranı, ilk/son çizgi konumu. | **Uygulanabilir**, ama kod kutusu, imza "XXX", başlık/not yazıları ve yazı uzunluğu karıştırıyor; ROI ve görev bazlı normalleştirme gerekir. |
| **Aynı öğrencinin farklı ölçüm zamanları** | Kod ile üç zamanın sayfaları eşleşiyor. Harf boyutu (Ber+Arg ortalaması) MZP1→MZP3 farkı ortalama −0,05 mm, SD 0,74 mm (n=48): sistematik kayma yok, bireysel değişim büyük. | **Uygulanabilir** (yapı olarak). Değişimin gürültüyü aşıp aşmadığı için tekrar ölçüm hatası bilinmeli; müdahale grubunun etkisi el yazısı üzerinde bilinmiyor. |

Sınıf karşılaştırması iddia edilmedi (tarama farkı ve örneklem küçük); tabloda yalnız ölçümün yapılabilirliği var.

### Karıştırıcı faktörler (görsel kontrol: 12 rastgele sayfa + 36 başlık kırpıntısı; sayısal oran iddiası yok)
- **Üzeri çizilmiş/karalanmış kelimeler:** örnek sayfaların çoğunda var (mavi kalın karalamalar); bileşen sayısı ve mürekkep miktarını şişirir. Otomatik ayıklama denenmedi.
- **Anonimleştirme "XXX"** (236 sayfa, 220 öğrenci): imza yerine basılı siyah yazı; mürekkep olarak sayılır. Metin katmanından (n_xxx ve sözcük kutuları) konumu bulunabilir.
- **Kod kutusu ve elle yazılmış kod/başlık:** görülen örnek sayfaların hepsinde "Deine Nummer/Code" kutusu ve içine yazılmış kod, ilk satıra taşabiliyor; sayfa başında basılı başlık (rapor/görüş) ve kenarda notlar ("WZ: 40", "3 62", "t2", "Ber"). Bunların bir kısmı araştırmacı notu olabilir (**[hipotez]**).
- **Kalem:** çoğu mavi tükenmez; siyah/kurşun kalem ve yeşil kalem de var; soluk kurşun kalem yazı (bazı sayfalarda neredeyse okunmuyor) eşiklemeyi bozar.
- **Çizgiler:** aynı çizgili form, harflerle kesişiyor (ölçümü bozar ama çıkarılabiliyor; kesişimde harf parçaları kaybolur).
- **Tarama kalitesi:** 150–300 dpi karışık, JPEG sıkıştırma farkı, arka plan parlaklığı değişimi ve bir örnekte kenar gölgesi, ikili (1 bit) sayfalar (60) ve gri sayfalar (342).
- **Öğretmen notu / düzeltme:** örnek sayfalarda belirgin kırmızı kalem düzeltmesi görmedim (12 sayfa); küçük örneklemden genelleme yapılamaz. Çizim (resim) olarak tanımlanabilecek içerik görmedim; sistematik kontrol yapılmadı.
- **Metin türü:** rapor ve mektup düzeni farklı; mektupta başlık/imza satırı var. Görev x zaman bazında ayrı değerlendirme gerekir.
- **Çok sayfalı yazılar:** 30 fazladan sayfa; hangi yazının devamı olduğu otomatik anlaşılmıyor.

### Referans dağılımları (yaş, sınıf, görev bazında) için uygunluk
- **Sınıf x görev x zaman:** her hücrede öğrenci sayısı kadar yazı: sınıf 5'te 495, sınıf 9'da 443 (tam 6 sayfalı olmayanlar hariç az azalır).
- **Ek kırılımlar (öğrenci):** sınıf x okul türü x cinsiyet: en küçük hücre 89 (sınıf 9, IGS, kız); grup eklenirse en küçük hücre 38. Yani çoğu kırılımda 100'ün üzerinde, ama grup ve cinsiyet birlikte eklenirse küçülüyor (Çizim modülündeki `MIN_GROUP = 100` ölçütüne göre sınıf x okul türü x cinsiyet çoğunlukla sınırda).
- **Yaş:** sınıf 5'te 120–140 ay (%91), sınıf 9'da 170–190 ay (%85); dar yaş bantları (10 ay) sınıf içinde 23–290 öğrenci. Yaşa göre referans, sınıf referansından anlamlı ölçüde ayrı değil (yaş aralığı sınıf içinde dar).
- **Müdahale grubu:** müdahalenin yazı içeriğini hedeflediği biliniyor **[yayında]**; el yazısını etkileyip etkilemediği **[bilinmiyor]**. Referansı MZP1 ya da kontrol grubuyla sınırlamak daha güvenli ama MZP1'in müdahaleden önce olduğu Excel'de yazmıyor (**[hipotez]**).
- **Bu bir popülasyon ya da klinik norm değildir:** Köln ve Hannover'de, 2013–2015'te, bir müdahale çalışmasına katılan Gymnasium ve IGS öğrencileri **[yayında]**; Hauptschule vb. okul türleri yok, öğrencilerin üçte biri Almanca dışı dil geçmişine sahip (402/938), klinik grup yok. Yalnızca "bu çalışma örnekleminde akranlara göre" denebilir. Kullanıcı fotoğrafları (telefon, farklı kâğıt) bu taramalardan farklı koşulda: ölçek ve kâğıt farkı ayrıca ele alınmalı.

## 8. Malaysian veri seti ile karşılaştırma

| Konu | Malaysian (249 görüntü) | FD-LEX Scriptoria (5656 sayfa) |
|---|---|---|
| Birim | bir ya da birkaç satırlık kırpılmış görüntü | tam A4 sayfa, 1 görüntü/sayfa |
| Öğrenci kimliği | yok (yayında 83 katılımcı) | **var, %100 eşleşti (938)** |
| Yaş / sınıf / cinsiyet | yok | **var** |
| Görev / zaman | yok (Malayca cümle kopyalama) | **var** (2 görev x 3 zaman; sayfa sırası doğrulandı) |
| Etiket | iki sınıf (potansiyel disgrafi), uzman, ölçüt belirsiz | **disgrafi etiketi yok**; Rating anlamı belirsiz |
| Görüntü durumu | ikili, ters, sıkı kırpılmış, ölçek yok | renkli/gri A4 tarama, 150–300 dpi, **ölçek var** (çizgi 10,8 mm) |
| Çizgili kâğıt | var, aralık değişken, ölçeksiz | aynı form, sabit aralık |
| Sızıntı denetimi | yapılamıyor | öğrenci ve (hipotez) sınıf bazında yapılabilir |
| Karıştırıcılar | ölçek, ikilileştirme, kırpma | üzeri çizilmiş kelime, "XXX", kod kutusu, not, kalem, tarama |
| Lisans/izin | CC BY (UiTM deposu) **[yayında]** | **bilinmiyor**, kayıt gerekli |
| Dil | Malayca | Almanca; yazan çocuklar ilk-orta okul çağında (9–17 yaş: 109–202 ay) |

Önemli fark: FD-LEX **disgrafi etiketi taşımıyor**; hedefiniz etiket tahmini değil, betimleyici ölçüm ve referans karşılaştırması olduğu için bu bir engel değil. Ancak Malaysian'ın tek avantajı olan "klinik ilişkili etiket" kaybolur; FD-LEX'te klinik ilişkili bir iç doğrulama yok.

## 9. Veri sınırlamaları (özet)
1. Kullanım izni ve lisans bilinmiyor; bulut yüklemesi riskli.
2. Disgrafi/okunaklılık etiketi yok; Rating ve diğer test sütunlarının anlamı belgelenmemiş.
3. Sayfa → görev/zaman eşlemesi çıkarımla (doğrulandı ama 27 öğrenci belirsiz).
4. Tarama çözünürlüğü ve rengi sınıf/PDF ile karışık.
5. Üzeri çizilmiş kelimeler, anonimleştirme yazısı, kod kutusu, notlar ölçümleri bozuyor.
6. Örnek yalnızca iki okul türü, iki şehir, bir müdahale çalışması; norm değil.
7. Aşama 2 ölçümleri 48 öğrencilik örnekle, doğrulama referansı olmadan; harf boyutu ve kelime aralığı henüz güvenilir değil.
8. Çizgili formda yazılan tek tip (A4, 10,8 mm); kullanıcı fotoğrafları farklı olacak.

## 10. Olası optimizasyonlar
- Tüm sayfaları 100 dpi'de bir kez ölçüp özellik tablosunu önbelleğe almak (örnek 288 sayfa birkaç dakikada; 5656 sayfa için PDF başına paralel işlem). Gömülü JPEG'i `draft` modunda küçük çözmek, `get_pixmap`'ten hızlı.
- Metin katmanından "XXX" ve kod konumlarını (kelime kutuları) alıp ROI'den çıkarmak; kod kutusunu sabit koordinattan maskelemek.
- Kalem rengi/sayfa tipine (renkli, gri, ikili) göre ayrı eşikleme; arka plan normalizasyonu.
- Satır bölütleme (çizgi tabanlı) + gerçek x-yüksekliği; kelime bölütlemesi için boşluk eşiğini harf yüksekliği ve satır aralığına göre öğrenmek (elle doğrulama ile).
- Üzeri çizilmiş kelimeleri yoğun mavi blok olarak ayıklamak (renk + yoğunluk), etkisini ölçmek.
- Normları görev x zaman x sınıf bazında tutmak; 7+ sayfalı öğrencileri ayrı işaretlemek.

## 11. Sonraki aşama önerileri (karar sizde)
1. **İzin:** FD-LEX/Mercator-Institut'a kullanım, bulut yükleme ve örnek sayfa gösterimi için yazılı soru; yanıt gelene kadar veriyi yerelde tutmak.
2. **Kod kitabı:** Rating, AlphabetTask, SLS, Wortschatz tanımları için dokümantasyon istemek (veri sahiplerinden).
3. **Doğrulama çalışması:** ~100 sayfada elle işaretleme (x-yüksekliği, kelime sınırları, üzeri çizilmişler) ile ölçümlerin hatasını sayısallaştırmak; bu yapılmadan harf boyutu/kelime aralığı raporda sunulmamalı.
4. **Tam ölçüm geçişi** (model yok): bütün sayfalarda özellik tablosu + kalite bayrakları (çözünürlük, renk, "XXX", üzeri çizilmiş yoğunluğu).
5. **Referans kurulumu:** sınıf x görev x zaman (x okul türü gerektiğinde) bazında yüzdelik; "bu çalışma örnekleminde akranlara göre" dili; öğrenci/küme bazında bölme (referansta bölme gerekmiyor ama doğrulama için gerekli).
6. **Karar kaydı:** FD-LEX'in ana aday olarak değerlendirilmesi `docs/kararlar.md`, `docs/plan.md` ve `docs/durum.md`'ye bu rapor onaylanınca işlenir (şimdilik dokunulmadı).
7. Çizim modülündeki iş akışı (plan → denetleyici → onay → uygulama → doğrulayıcı) bu aşama için de uygulanabilir; plan modunda ayrı plan önerilir.

## Kaynaklar [yayında]
- FD-LEX tanıtım sayfası ve Collection Policy (Mercator-Institut, Köln): https://mercator-institut.uni-koeln.de/en/research-development/research-based-services/forschungsdatenbank-lernertexte-fd-lex-in-german ve https://mercator-institut.uni-koeln.de/sites/mercator/user_upload/Collection_Policy_FD-LEX_2024_04.pdf
- Forschungsdaten Bildung kaydı (DOI 10.18716/FD-LEX/861): https://www.fachportal-paedagogik.de/forschungsdaten/studiendetails.php?id=528
- Not: bu kaynakları yalnızca web arama özetlerinden okudum, sayfaları ayrıca açıp doğrulamadım. Lisans ve rating tanımı hiçbirinde bulunamadı.
