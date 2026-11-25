# Plan: El yazısı modülü, önişleme ve özellik çıkarma (FD-LEX Scriptoria)

**Güncel bilimsel hedef (2026-11-25):** grafomotor gelişimle ilişkili biçimsel/görsel-mekânsal özellikleri ölçmek, referanslarla karşılaştırmak, açıklanabilir uzman raporu üretmek (`docs/el_yazisi_bilimsel_temel.md`); statik görüntüden motor beceri ölçtüğümüz iddia edilmez. Yalnız FD-LEX (Malaysian arşiv). Fizibilite: `docs/el_yazisi_arastirma_fizibilite.md`; pilot: `docs/el_yazisi_pilot_protokolu.md`; rapor: `docs/el_yazisi_ornek_rapor.md`; transkriptler (gelecek): `docs/el_yazisi_gelecek_calisma.md`.

Durum: **plan v2 genel olarak kabul edildi (2026-11-25)**; öncelik çalışan prototip (`docs/el_yazisi_prototip.md`, sentetik görüntülerle). Gerçek veri izne bağlı; 100 sayfalık elle işaretleme ve kapsamlı istatistiksel doğrulama henüz başlamadı. Kabul ölçütleri **kesinleşmedi** (prototip belgesinde taslak tablo).

**Kabul edilen kararlar (2026-11-25):** FD-LEX ana, Malaysian yardımcı; çalışma çözünürlüğü **150 dpi**, sonra 200 ve 300 dpi ile duyarlılık testi; **70/15/15** öğrenci bazlı tabakalı bölme; **kayıpsız PNG** çıkarma (`extracted/`); `Rating` kullanılmaz; **izin geçidi** (A3'e izin yanıtı olmadan geçilmez); OneDrive klasör yedekleme ayarını kullanıcı elle kontrol edecek. Yeni: pilot (10–20 gerçek sayfa) izin sonrası; önce prototip sonuçları görselleştirilerek değerlendirilir.
Not: plandaki "Kayıpsız çıkarma: JPEG akışı olduğu gibi (JPG), Flate için PNG" ayrımı korunur; kullanıcı kararı "kayıpsız PNG" Flate sayfalar ve render gereken sayfalar için PNG, JPEG sayfalar için bayt-bayt aynı akış (yeniden sıkıştırmasız) olarak yorumlandı. Farklı istenirse (JPEG'i de PNG'ye çevirmek dosyayı büyütür, kayıpsız ama kaynak SHA eşitliği kaybolur) belirtilmeli.

**Prototip durumu (A0–A5'in sentetik kısmı):** `src/handwriting/` (yol koruması, ölçek/eğiklik, maskeler, satır segmentasyonu, özellikler, görselleştirme), `tools/check_no_student_data.py` + pre-commit kancası, 23+4 sentetik test. Plan adımlarından yapılmayanlar: A1 (gerçek çıkarma, manifest, tekilleştirme), A7 (bölme dondurma), A3 elle işaretleme, A5 profil tabanlı x-yüksekliği karşılaştırması, A6 istatistik. Henüz kod yazılmadı, model eğitilmedi.
Girdiler: `docs/fd_lex_dataset_analysis.md` (EDA, kabul edildi), `docs/handwriting_dataset_analysis.md` (Malaysian, yardımcı veri seti), `docs/kararlar.md`.
Çizim modülüne ve `src/` altındaki mevcut dosyalara dokunulmaz; el yazısı kodu yeni bir alt pakette (`src/handwriting/`) yaşar.

## 0. Amaç, kapsam, ilkeler

**Amaç:** yüklenen el yazısı sayfasından yorumlanabilir geometrik özellikler çıkarmak, bunları uygun referans gruplarıyla karşılaştırmak, betimleyici rapor üretmek.
Disgrafi teşhisi ve risk skoru yok. Çizim modülüyle aynı ilkeler: klasik görüntü işleme (öğrenme yok), kalite bayrakları, "bu çalışma örnekleminde akranlara göre" dili,
sistematik hatalar normlara da yansıyacağı için kabul, bazı sayfaları etkileyen hatalar bayrakla görünür.

**Kapsam dışı (kullanıcı kararı):** kelime aralığı, okunabilirlik skoru, `Rating` sütununun etiket olarak kullanımı, model eğitimi. `Rating`, `AlphabetTask`, `SLS`, `Wortschatz` **hiçbir amaçla kullanılmaz** (etiket, özellik seçimi, eşik, kalite analizi, doğrulama, tabakalama; manifeste ve özellik tablolarına alınmaz).
Bu karar anlamları kod kitabıyla belgelenene kadar sürer. `Textlänge` (yayında "yazılan kelime sayısı" **[yayında]**, dosyadan doğrulanmadı) yalnız sayfa kullanımını yazı uzunluğuna göre karşılaştırmak için **kovaryat**tir, etiket değildir.
**Cinsiyet:** özellik girdisi değildir ve referans dağılımlar cinsiyete göre ayrılmaz (çizim modülü ilkesi); yalnız bölme tabakalamasında ve dengesizlik raporunda kullanılır.

**Veri yönetimi kuralları (kalıcı):**
- FD-LEX verisi, türevleri (sayfa görüntüleri, kırpmalar, özellik tabloları) ve öğrenci kodları **yalnız yerel diskte** (`data/handwriting/fd_lex/`, git dışında) kalır. Kullanım izni netleşmeden Drive, Colab ya da GitHub'a yüklenmez.
- Kod, FD-LEX yolunu `PATHS`'in Drive'a giden dallarından ayrı tutar ve `colab` ortamında FD-LEX işlerini **reddeder** (`config.is_colab()` ise hata).
- Commit'e girmeden önce notebook çıktıları temizlenir: öğrenci taramaları (base64 görüntü), öğrenci kodları, dosya adlarındaki kodlar. **Mevcut iki notebook** (`fd_lex_eda.ipynb`, `handwriting_eda.ipynb`) 2026-11-25'te temizlendi (çıktılı FD-LEX kopyası yalnız yerelde, git dışı).
  Otomatik denetim (A0): **pre-commit kancası** (elle çalıştırmaya bağlı değil) staged içerikte öğrenci kodu desenini (gevşek: `\b[0-9][KkHh]\d{2}[A-Za-z]{2}\d{0,3}\b`; 7–9 karakterli ve bozuk kodları da yakalar), gömülü `image/png|jpeg`,
  "Benutzer" satırını ve `data/handwriting/` yolunu arar; bulursa commit'i durdurur. Kanca sentetik ihlallerle kendi testinden geçer.
- Belgelerde örnek öğrenci kodu verilmez ("öğrenci A"); özet istatistik verilebilir.
- **Bulut senkronu:** proje `C:\Users\user\Desktop\...` altında; Masaüstü OneDrive'a yönlendirilmiş görünmüyor (`GetFolderPath('Desktop')` = `C:\Users\user\Desktop`, OneDrive ayrı `C:\Users\user\OneDrive`), ama OneDrive "klasör yedekleme" ayarı **doğrulanmadı**: A0 kullanıcıdan bu ayarın kapalı olduğunu doğrulamasını ister. `paths.py` FD-LEX yolunun Google Drive / OneDrive / `bitirme` altında olmasını **reddeder** (birim testi) ve `data/ciktilar/` geri dönüşünü kullanmaz.
- `extracted/` yalnız yazı sayfalarını içerir (kapak sayfaları çıkarılmaz: kullanıcı adı satırı); diskte ek şifreleme yapılmaz, erişim yalnız yerel kullanıcı.
- Rapor ve normlar: "bu çalışma örnekleminde akranlara göre". Klinik/popülasyon normu değil (EDA bölüm 7).

## 1. Bilinen girdiler ve özel dikkat gerektiren üç konu

| Konu | Bilgi (EDA) | Planın yanıtı |
|---|---|---|
| **27 (tekilleştirme sonrası 28) öğrencide belirsiz görev/zaman** | 6 sayfa olmayan 27 öğrenci: 21 x 7, 3 x 8, 1 x 9, 2 x 5 sayfa (toplam 190 sayfa; 5656 = 938 x 6 + 28). **Tekrar eden sayfanın öğrencisi tam 6 sayfalı grupta** (6 sayfa, biri kopya; `pages.csv` ile doğrulandı): tekilleştirmeden sonra 5 sayfa kalır, o öğrenci de belirsiz olur → **28**. `pages.csv`'deki varsayım sütunu bu öğrenciye yanlışlıkla doldurulmuş; A1'de düzeltilir. | §A1.4: elle kontrol önce, otomatik eşleme yalnız öneri; çözülene kadar `gorev_zaman_guvence="belirsiz"` ve **görev/zaman bazlı referanslardan dışlanır** (görev bağımsız özelliklerde bayrakla kalabilir); dışlanan öğrencilerin profili raporlanır (seçilim yanlılığı). |
| **Tekrar eden sayfa** | PDF06 sayfa 177 ve 181 aynı görüntü akışı (aynı öğrenci). Başka birebir ya da > 0,98 benzer çift yok (yalnız JPEG sayfalarda; 300 Flate sayfada yalnız birebir hash). | §A1.3: aynı hash → ilk sayfa kalır, diğeri `yinelenen`; öğrenci eşitliği şartı **yok** (başka öğrencide ya da PDF'te çıkarsa ayrıca raporlanır); Flate sayfalara da yaklaşık kopya taraması eklenir. |
| **Çözünürlük ile sınıf ilişkisi** | ~300 dpi sayfalar sınıf 5'te %29, sınıf 9'da %78 (sınıf 5: 2 / 553 / 1556 / 880 sayfa <120 / ~150 / ~200 / ~300 dpi; sınıf 9: 0 / 254 / 341 / 2070; kaynak: `fd_lex_eda` bölüm 7 çıktısı). Gri/ikili sayfalar, PDF ve müdahale grubu da sınıfla karışık: **PDF x grup x dpi x sınıf birlikte karışık** (ör. PDF01–02 yalnız kontrol, PDF04 yalnız müdahale). | §A2 ve §A6: ortak çalışma çözünürlüğü; **aynı sayfalar üzerinde yapay bozma deneyleri = ölçümün çözünürlüğe duyarlılığının nedensel testi** (gerçek tarayıcı/kâğıt/sıkıştırma farkını ve sınıf farkını **ayırmaz**) + sınıf/PDF içi gözlemsel kontrol. **Tek karar kuralı (A6):** kontrol geçmezse sınıf bazlı yüzdelik o özellik için raporlanmaz ya da dpi tabakalı raporlanır; geçse bile "sınıf farkı" yorumunda tarama sınırlaması notu kalır. |

## 2. Dizin, kod yapısı, çıktılar (hepsi yerel, `data/handwriting/fd_lex/` altında)

```
data/handwriting/fd_lex/
  raw/                      (değişmez)
  metadata/                 (değişmez)
  manifests/pages.csv       (EDA'da üretildi; A1'de genişletilir)
  extracted/                A1: kayıpsız çıkarılmış gömülü görüntüler (yerel)
  work/                     A2: ortak çözünürlükte, dik, normalize sayfalar (yerel önbellek)
  features/                 A5: özellik tabloları, kalite bayrakları (yerel)
  annotations/              A3'te elle işaretlenen doğrulama sayfaları (yerel)
  splits.csv                A7: dondurulmuş bölme (yerel)
```
Kod (yeni, ayrı alt paket; çizim modülü değişmez): `src/handwriting/` içinde `paths.py` (yollar, Colab koruması), `manifest.py`, `extract.py`, `normalize.py`, `masks.py`, `segment.py`, `features.py`,
`quality.py`, `robustness.py`, `splits.py`; `tests/test_handwriting_*.py` **sentetik sayfalarla** (gerçek veri yok); `HW_MEASUREMENT_VERSION` sabiti (çizimdeki `MEASUREMENT_VERSION` gibi: tanım değişirse artar,
türev tablolar yeniden hesaplanır). Notebook yalnız `src/handwriting` fonksiyonlarını çağırır; notebook çıktıları commit öncesi temizlenir. Bağımlılıklar: `pymupdf`, `openpyxl` (`requirements.txt`'te, kullanıcı kararıyla; yerel, Colab'da FD-LEX zaten çalışmaz; Colab'da çizim akışı için kurulmaları zararsız ama gereksiz).
Not: `pymupdf` 2.1 ek paketler çekiyor (`onnxruntime`, `networkx`, `pymupdf-layout`, `pymupdf4llm`, `pyyaml`, `psutil`, `tabulate`); kullanılmıyor, ileride gereksiz bulunursa `pymupdf` yerine daha hafif bir sürüm denenebilir.

## 3. Aşamalar ve geçit ölçütleri

| Adım | İş | Geçit (bitti sayılma) |
|---|---|---|
| A0 | İzin geçidi, yerel-only koruma, commit denetimi | Koruma testi (Colab ortamında FD-LEX çağrısı hata verir); commit denetimi örnek ihlalleri yakalıyor |
| A1 | Çıkarma ve manifest (öğrenci kodu, kaynak bilgisi korunarak) | Manifest 5656 satır, çıkarılan dosya SHA'ları PDF akışlarıyla birebir; tekilleştirme ve sayfa eşleme raporu |
| A2 | Fiziksel ölçek ve çözünürlük normalizasyonu | Ölçek çapraz kontrolü (sayfa kutusu / çizgi aralığı) kabul sınırında; çalışma önbelleği |
| A3 | Kâğıt çizgisi, kod kutusu, XXX, başlık/not ayrıştırma | 60 sayfalık elle işaretli kümede maske ölçütleri (§A3 doğrulama) geçti |
| A4 | Yazı alanı ve satır segmentasyonu | Satır sayısı / taban çizgisi doğrulaması geçti |
| A5 | Özellik çıkarma (4 aile) | Her özellik işaretli sınama yarısında ölçütü geçti; geçmeyen, A5 başındaki **önceden yazılı kurala** göre sınıflanır |
| A6 | Dayanıklılık testleri (çözünürlük, kalem, tarama) | Ölçütler geçti; geçmeyen özelliğe bayrak ya da stratifikasyon kararı |

**Uygulama sırası: A0 → A1 → A7 → A2 → A3 → A4 → A5 → A6 → rapor** (A7 tabloda değil, A1'in hemen ardında dondurulur). A7'nin birimi öğrenci olduğu için görev/zaman belirsizliği (A1.4) bölmeyi **etkilemez**; bölme A1.4'ün bitmesini beklemez.
**İzin geçidi:** A0–A2 yalnız yerel ve geri alınabilir; **A3'e (elle işaretleme emeği) izin yanıtı gelmeden geçilmez**. Yanıt gelmezse A2 sonunda durulur ve kullanıcıya sorulur.
A3'ün elle işaretleme kümesi **yalnız train'den** seçilir. **Test bölümünün ölçüm değerlerine** A6 sonrası, norm aktarımı değerlendirmesine kadar bakılmaz; test için ayrı plan A6'dan önce yazılır (§A7.4). Her adım sonunda dogrulayici çalışır (`docs/dogrulama/<tarih>-<konu>.md`).

## A0. İzin geçidi ve koruma
- Kullanım izni **alınmadı varsayılmaz**; adımlar yerelde ilerler, izin yanıtı gelene kadar paylaşımla ilgili hiçbir şey yapılmaz. İzin metni gelirse `docs/kararlar.md`'ye özetlenir.
- Koruma: `paths.py` `CIZIM_ENV=colab` ya da `COLAB_RELEASE_TAG` varken hata verir; `deneyler.csv`/Drive yazan kodlardan ayrı. Sentetik veri testleri Colab'da koşabilir (gerçek veri okumaz).
- Commit denetimi: küçük betik (`tools/check_no_student_data.py`, yeni dosya) staged dosyalarda öğrenci kodu deseni, gömülü görüntü çıktısı, kullanıcı satırı arar. Notebook çıktıları temizleme komutu ve denetim, kapanış adımının parçasıdır.

## A1. PDF görüntülerinin çıkarılması, öğrenci kodları ve kaynak bilgisi

**Amaç:** her yazı sayfasının görüntüsünü, kimliği ve kaynağıyla birlikte, kayıpsız ve izlenebilir biçimde yerel diske çıkarmak.

**1. Kayıpsız çıkarma (`extracted/`).** Alternatifler:
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) **Gömülü akışı olduğu gibi yazmak** (`xref_stream_raw`; JPEG için bayt bayt aynı `.jpg`, Flate için PNG'e kayıpsız) — **önerilen** | Yeniden sıkıştırma yok; SHA'sı PDF'tekiyle eşit, kaynak kanıtlanabilir; hızlı | Sayfa dönüşü (`/Rotate`) ve çok görüntülü sayfalar ayrıca ele alınmalı |
| (b) `get_pixmap` ile sayfayı render edip yazmak | Dönüşü uygular, çok görüntülü sayfayı birleştirir | Yeniden örnekleme ve ek sıkıştırma; kaynak bayt eşitliği yok, dpi seçimine bağlı |
Karar: (a) birincil; 3 çok görüntülü sayfa için (b) ve manifestte `cikarma_yontemi` sütunu. Dönüş açısı dosyaya uygulanmaz, manifestte `donus_derece` olarak saklanır; yükleme sırasında uygulanır (EDA'da `get_pixmap` ile sayfaların dik çıktığı gözle doğrulandı; gömülü görüntü dönük olabilir, bu A1 doğrulamasında 90/180/270 örnekleriyle yeniden denetlenir).
**Dosya adı:** `{pdf}_{seite:04d}.jpg|png` (öğrenci kodu dosya adında değil, manifestte: kod tek yerde dursun).

**2. Manifest (`pages.csv` genişletilir).** Mevcut sütunlara eklenir: `xref`, `stream_sha1` (mevcut `img_sha1`), `cikarilan_dosya_sha256`, `donus_derece`, `cikarma_yontemi`, `cikarilan_boyut`, `dpi_eff`, `dpi_grubu`, `yinelenen` (bool), `gorev_zaman_guvence` (`dogrulandi`, `varsayim`, `belirsiz`), `bolum` (A7 sonrası). Öğrenci kodu, PDF adı ve sayfa numarası her satırda; kaynak sütunları (`pdf`, `seite`, `xref`) silinmez. Excel alanları (sınıf, grup, okul türü, yaş, cinsiyet, Textlänge) öğrenci koduyla birleştirilir; `Rating` vb. **manifeste alınmaz** (yanlışlıkla etiket olarak kullanılmasın; ayrı yerel dosyada tutulur).
**Doğrulama:** (i) çıkarılan dosyanın SHA'sı `xref_stream_raw` ile eşit (5356 JPEG sayfanın tamamı); **Flate (299) sayfalarda** PNG'nin piksel dizisi PyMuPDF'in decode ettiği pixmap ile birebir eşit; **çok görüntülü 3 sayfa** `get_pixmap` ile üretilir ve gözle kontrol edilir; (ii) manifest 5656 satır, her öğrenci kodu 938 Excel koduyla eşleşiyor (EDA'da %100); (iii) 90/180/270 dönüşlü örneklerde yükleme sonrası sayfa dik.

**3. Tekilleştirme.** Kural: aynı `stream_sha1` → ilk sayfa kalır, diğerleri `yinelenen=True` (silinmez, işaretli). **Öğrenci eşitliği şartı yok:** farklı öğrenci koduyla ya da farklı PDF'te aynı hash çıkarsa ayrıca raporlanır (kod hatası göstergesi). Yaklaşık kopya: küçük resim korelasyonu > 0,98 → aday, elle bakılır; **300 Flate sayfa için de** (decode edilmiş küçük resimle) taranır (EDA'da yalnız JPEG'lerde yapıldı). Bilinen vaka: PDF06 s177/s181 (öğrenci A); bu öğrenci 6 sayfalı gruptaydı, tekilleştirmeden sonra **5 sayfa** kalır ve belirsiz listesine girer (28). Kural her yeniden çalıştırmada yeniden değerlendirilir; PDF'ler arası örtüşme yeniden denetlenir.

**4. Görev/zaman eşlemesi (27 belirsiz öğrenci).**
- **Varsayılan (910 öğrenci: tam 6 sayfa ve tekrarsız):** sıra Ber1, Arg1, Ber2, Arg2, Ber3, Arg3 (EDA'da **288 sayfada / 48 öğrencide** görsel + sayısal doğrulandı; 910'a genelleme **kanıtlanmadı**). `gorev_zaman_guvence="varsayim"`. **Genişletilmiş doğrulama ve kabul ölçütü (sonuçtan önce):** (a) tüm 910 öğrencide mürekkep–`Textlänge` 6 x 6 Spearman matrisinde her sayfa konumunun en yüksek sütunu beklenen sütun **ve** köşegen ortalaması − köşegen dışı ortalaması ≥ 0,15; (b) rastgele 100 öğrencide 1.–2. sayfa basılı başlıklarının beklenenle uyumu ≥ %98. Biri geçmezse `varsayim` etiketi `belirsiz`e çevrilir ve nedeni araştırılır (özellikle PDF/sınıf alt kümelerinde).
- **Belirsiz öğrenciler (28 = 27 + tekilleştirmeyle düşen 1; ≈ 189 sayfa):** sıra tersine çevrildi, **elle kontrol önce**:
  1. **Elle kontrol (birincil):** sayfalar basılı başlık ("Unfallbericht", "Meine Meinung zur Schuldfrage") ve rapor/mektup biçimiyle incelenir (≈ 190 sayfa; 100 sayfalık işaretlemeden daha az emek); karar `annotations/page_task_manual.csv`'ye (yerel) gerekçe ve güven (yüksek/orta) ile yazılır.
  2. **Otomatik öneri (yalnız ikincil, karar vermez):** sayfa dizisini 6 yazıya bölen sıra korumalı olası bölmeler için mürekkep–`Textlänge` uyumu puanlanır. EDA'daki ayırt edicilik zayıf (köşegen 0,69 / köşegen dışı 0,41; 288 sayfa, 48 öğrenci), bu yüzden tek başına karar sayılmaz; yalnız elle kontrolü sıralar. Güvenilirliği **iki hata modeliyle** ölçülür (bilinen öğrencilerde (i) bir yazıyı iki sayfaya bölme, (ii) bir yazıyı eksiltme; mürekkep miktarı düzeyinde sentetik), sonuç güven aralığıyla raporlanır.
  3. **Çözülemeyenler:** `belirsiz`; görev ve zaman bazlı referanslara girmez; dışlanan öğrencilerin profili (sınıf, grup, okul türü, yazı uzunluğu) raporlanır, çünkü 7+ sayfalılar uzun yazanlar olabilir (seçilim yanlılığı).
- Çok sayfalı yazı (bir yazı iki sayfa): özellikler yazı düzeyinde sayfalar birleştirilerek değil, **sayfa düzeyinde** hesaplanır ve `devam_sayfasi` bayrağı taşır; yazı düzeyinde toplama ayrı karar (A5).

## A2. Fiziksel ölçek ve çözünürlük normalizasyonu

**Amaç:** mm cinsinden ölçüm ve çözünürlükten bağımsız karşılaştırma.

**Ölçek kaynağı alternatifleri:**
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) Sayfa kutusu (A4 ≈ 595x842 pt) ve görüntü boyutu → mm/px | Basit, hızlı | Tarayıcı "sayfaya sığdır" yaparsa gerçek ölçekten sapar; kenar boşluğu kırpılmışsa yanlış |
| (b) **Basılı çizgi aralığı** (EDA: 10,8 mm, 10,2–10,9) | Sayfanın kendisinden; tarama ölçeğini doğrudan ölçer; telefon fotoğrafına da genellenebilir | Çizgi bulma hatasına duyarlı; form sabit varsayımı (aynı basılı form; doğrulanmadı: yalnız 288 sayfa) |
| (c) İkisinin birleşimi: (a) birincil, (b) çapraz kontrol, > %2 sapmada (b) | Hata yakalar | Daha karmaşık |
Öneri: (c). **Doğrulama:** 288 örnek yerine **tüm sayfalarda** (a) ve (b) ölçeklerinin oranı; oranın dağılımı, sapan sayfaların PDF/dpi/sınıf ile ilişkisi (ölçek hatası sınıfa bağlıysa sistematik karıştırıcı). Kabul: sayfaların ≥ %98'inde |fark| ≤ %2; kalanlar `olcek_supheli` bayrağı. **Sapan sayfalar için önceden yazılı kural:** sapma PDF, dpi grubu ya da sınıfla ilişkiliyse (Cramér V ≥ 0,2) ölçek (b)'den (çizgi aralığı) alınır ve ilişki raporlanır; ilişkisizse bayrakla (a) kalır. "Tek basılı form, çizgi aralığı 10,8 mm" varsayımı bu adımda **tüm sayfalarda** (aralık ve çizgi konumu dağılımı) doğrulanır; tutmazsa A3.1(b) (şablon) kullanılmaz. **Eğiklik hata bütçesi:** düzeltme sonrası kalan |açı| ≤ 0,1° ≈ 150 mm'lik bir satırda ≤ 0,26 mm; taban çizgisi ölçütü (0,5 mm) bu bütçeyi aşmaz.

**Çalışma çözünürlüğü:** hepsi **150 dpi**'ye (en düşük yaygın; 807 sayfa zaten ~150) alan-ortalamalı küçültmeyle indirilir (yukarı örnekleme yok); 150 dpi altı 2 sayfa ayrı bayrak ve norma girmez. Alternatif: 200 dpi (daha ince çizgi bilgisi, 807 sayfada büyütme gerektirir; büyütme yapay yumuşatma getirir) ya da özelliklerin yerel (native) çözünürlükte hesaplanıp mm'ye çevrilmesi (çözünürlük bağımlılığı artar). 100 dpi (EDA) ince çizgi ve küçük harfler için yetersiz kalabilir; 150 dpi'nin 100 dpi'ye göre özellik farkı A6'da ölçülür.
**Diğer normalizasyon:** sayfa dönüşü uygulanır; eğiklik düzeltme (EDA'da |açı| ≤ 0,55°) açıyla; arka plan aydınlatma düzeltmesi (EDA'daki maksimum-filtre yaklaşımı) ve renk uzayına göre ayrı yol (RGB/ICC → renkli; gri; 1 bit ikili). Alternatif: sayfayı çizgilere göre hizalayıp yeniden örneklemek (daha iyi hizalı, ama eğri çizgili sayfalarda piksel bozulması); önerilmez, açı küçük.
**Doğrulama:** (i) ölçek çapraz kontrolü (yukarı); (ii) düzeltme sonrası çizgi açısı |≤ 0,1°| ≥ %95 sayfada; (iii) küçültme sonrası çizgi aralığının mm değeri çözünürlük grubundan bağımsız (dpi grupları arası fark ≤ %1).

## A3. Basılı çizgiler, kod kutuları, XXX işaretleri ve diğer yapıların ayrıştırılması

**Maskeler (her biri ayrı, birleşik "çocuk mürekkebi" = sayfa karanlık piksel − bunların birleşimi):**

1. **Basılı kâğıt çizgileri**
   | Seçenek | Avantaj | Sınırlama |
   |---|---|---|
   | (a) Yatay morfolojik açma + uzunluk eşiği (EDA'da denendi; 288/288 sayfada 21–25 çizgi) | Hızlı, basit | Harfin çizgiyle kesiştiği yerde harf parçası da silinir; solukta/kırık çizgide kaçırma |
   | (b) **Çizgi şablonu: tek form olduğu için çizgi konumlarını bir kez öğrenip (medyan) sayfaya hizalamak, ardından yalnız çizgi konumlarında silmek** | Harf parçası daha az silinir; çizgi dışındaki yatay vuruşlar (alt çizgi, karalama) korunur | Form tek ve sabit olmalı (doğrulanacak: çizgi konumlarının sayfalar arası kayması) |
   | (c) Silmek yerine **çizgi piksellerini maskeleyip** sonraki ölçümde "bilinmeyen" saymak | Hiçbir harf parçası uydurulmaz | Bileşen bağlantısı kopar (bileşen sayısı etkilenir) |
   Öneri: (b) ile (a)'yı karşılaştır, kesişimde çizgi üstündeki harf parçasını geri kazanma (çizginin alt-üst komşuluğunda ink varsa korumak) küçük deney olarak değerlendirilir. **Doğrulama:** 60 elle işaretli sayfada çizgi maskesi IoU ≥ 0,9 ve "silinen harf pikseli oranı" (harf ∩ çizgi maskesi / harf) raporu.
2. **Kod kutusu ve elle yazılmış kod/başlık** (sağ üst "Deine Nummer/Code" kutusu, kutu içine yazılmış kod, sayfa üstü başlık ve notlar, alt telif satırı)
   | Seçenek | Avantaj | Sınırlama |
   |---|---|---|
   | (a) Sabit konumlu dikdörtgen bölgeyi dışlamak (şablon) | Basit | Tarama kaymasında kutu yer değiştirir; kod kutusu ilk satıra taşan yazıyı da keser |
   | (b) **Basılı dikdörtgeni şablon eşleştirmeyle bulmak** ve içini maskelemek; sayfa üst bandını (ilk çizgiden önce) tümüyle ROI dışı bırakmak | Kaymaya dayanıklı | Kutu yoksa/solmuşsa başarısız; ilk satıra taşan yazı kesilir (bayrak) |
   | (c) Üst bandı başlık/kod için, geri kalanını yazı alanı say | Çok basit | Başlıkla ilk satır arası belirsiz |
   Öneri: (b)+(c). **Doğrulama:** 60 sayfada kod kutusu bulma oranı; ilk satırdaki harf pikseli kaybı (elle işaretli) ≤ %2; kutuya taşan yazı sayısı raporu.
3. **XXX anonimleştirme işareti (236 sayfa, 220 öğrenci)** — imza yerine basılı siyah yazı.
   | Seçenek | Avantaj | Sınırlama |
   |---|---|---|
   | (a) **PDF metin katmanı kelime kutuları** (`get_text("words")` ile "XXX" kutusunu bulup maskelemek) | Kesin ve ucuz (n_xxx EDA'da çıkarıldı) | Yüklenen telefon fotoğrafında metin katmanı yok (yalnız bu veri setinde geçerli, üretim hattında gerekmez) |
   | (b) Görüntüden: tek tip siyah/kalın harf şablonu (XXX tipografisi) eşleştirme | Katmansız çalışır | Elle yazıdan ayırmak zor, yanlış pozitif riski |
   Öneri: **(a)** FD-LEX için; (b) yalnız ileride fotoğraf hattı için ayrı iş. XXX kutusu maskelenip o bölgedeki yazı "bilinmiyor" sayılır; **yanlış negatif denetimi:** metin katmanında XXX bulunmayan sayfalarda görüntüde siyah blok kalıp kalmadığına işaretli kümede elle bakılır (katmansız anonimleştirme olasılığı); sayfa `xxx_maskeli` bayrağı taşır (imza yeri genellikle yazının sonunda, ölçüme etkisi küçük beklenir; ölçülür). **Doğrulama:** 236 sayfanın tümünde XXX kutusu bulundu mu (metin katmanı = kesin); maske sonrası ink'te siyah blok kalıyor mu (60 sayfada elle).
4. **Üzeri çizilmiş/karalanmış kelimeler:** otomatik ayıklama **zorunlu değil**, ama bayrak: renkli kalın blok yoğunluğu (aynı kalem, yüksek yerel mürekkep yoğunluğu, ince çizgi yapısı yok). Alternatif: **dokuya** dayalı (yoğun, yönsüz vuruş kümeleri) ya da yok sayma. Önerilen: yalnızca `ustu_cizili_yogunluk` kalite ölçüsü ve yüksekse sayfa ölçümleri bayraklanır (silmek yeni harf/yapı uydurur). **Doğrulama:** 60 sayfada elle işaretli üzeri çizilmiş bölgelere karşı ölçü; ölçüm kararlılığına etkisi A6'da.
5. **Kenar/tarama artefaktları** (kenar gölgesi, arka plan parlaklığı): yazı alanı kenarlardan uzak bir ROI ile (`roi` sol %4, sağ %3) ve arka plan normalizasyonu ile; gölge kalan sayfalar `kenar_golge` bayrağı.

**Kalem rengi ve eşikleme:** üç yol: (a) renkli sayfalarda kroma tabanlı mürekkep (mavi kalem) + gri düzeyi; (b) gri düzeyi için yerel (uyarlanabilir) eşik (Sauvola); (c) 1 bit sayfalarda doğrudan kullanılır. Karşılaştırma kriteri: elle işaretli mürekkep maskesine IoU; siyah/kurşun/yeşil kalem ve soluk kurşun için ayrı rapor (tek global eşik soluk kurşunu kaçırır: EDA'da bazı sayfalar neredeyse okunmuyor).

**Elle işaretleme kümesi (doğrulamanın tek kaynağı):** **100 sayfa** (EDA önerisi; 60 sayfa küçük bulundu), yalnız train'den; tabakalama **üç etkenle** (dpi grubu x renk tipi/kalem [renkli mavi, renkli diğer, gri/ikili] x sınıf ≈ 18 hücre, hücre başına ≈ 5–6 sayfa; 5 etkenli tabaka uygulanamaz); XXX'li sayfalardan en az 20, 150 dpi altı ya da soluk kurşun kalemden en az 10. İşaretlenecekler: çizgi/kutu/XXX maskeleri, üzeri çizilmiş bölgeler, her satır için 3 taban çizgisi noktası, 10 harf için x-yüksekliği. **İşaretlemeyi kim yapar:** karar bekliyor (kullanıcı); Claude otomatik maskeyi önceden çizip düzeltme arayüzü hazırlayabilir ama otomatik maskeyi "doğru" saymaz. **İşaretçi tutarlılığı:** tek işaretçi varsa 10 sayfa **bir hafta sonra yeniden** işaretlenir ve uyum (IoU, nokta farkı) raporlanır; ölçüt işaretçi uyumunu aşamaz. Küme **ayar (50) ve sınama (50)** diye ikiye bölünür; parametre ayarı yalnız ayar yarısında yapılır. Kabul ölçütleri (**plan onaylandığında donar, sonuçtan sonra değiştirilmez**): çizgi/ink maskesi IoU ≥ 0,90; satır sayısı uyumu ≥ %95; taban çizgisi hatası ≤ 0,5 mm (medyan); x-yüksekliği hatası ≤ %10 (medyan).

## A4. Yazı alanı ve satır segmentasyonu

**Amaç:** her sayfada yazının bulunduğu alanı ve her yazı satırını (çizgi bandı + taşan harf kısımları) belirlemek.

| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) **Çizgi tabanlı bantlar** (çizgi i'nin üstündeki bant satır i; yazı çizgiden ~0,24 satır aralığı yukarıda, EDA) | Basit; çizgi konumu kesin; satır atlama görünür | Alt uzantılı harfler alttaki banda taşar; iki çizgiye yayılan büyük yazı; çizgi atlanırsa kayma |
| (b) Yatay izdüşüm profili vadi tespiti | Çizgiye bağımlı değil (fotoğraf için genellenebilir) | Üst üste binen satırlarda zayıf; çizgi (güçlü) sinyali bastırır |
| (c) Bağlı bileşenleri yakınlıkla satırlara kümelemek | Eğik satırlara dayanıklı | Bitişik yazıda ve karalamada kararsız |
| (d) **(a) ile başlayıp (b)/(c) ile alt uzantı atamasını düzeltmek** (karma) | Her ikisinin güçlü yanı | Daha karmaşık, parametreli |
Öneri: (a) + alt uzantı ataması için bileşen merkezine göre bant ataması (b benzeri); karma (d) gerekirse deney. **Yazı alanı:** ROI = ilk ve son çizgi arası + üst bant marjı (**sol marj kesmesi EDA'daki 8 mm'lik en küçük kenar boşluğunu kesmemeli: ROI sol sınırı ≤ 5 mm**); yazı bbox'ı için maskelenmiş mürekkepten (XXX, kod kutusu hariç) hesap. **Satır sayısı tanımı:** ink içeren bant sayısı; "boş satır atlama" ayrı sayılır.
**Doğrulama:** 60 sayfada elle satır sayısı ve satır başına 3 taban çizgisi noktası (hata ≤ 0,5 mm); bölütleme çıktısının görsel kontrolü (renkli bant bindirmesi, notebook'ta bellekte, diske yazılmaz); ardışık iki bantta atama çakışması oranı.

## A5. Özellikler

**Sınıflama kuralı (sonuçtan önce):** öğrenci içi ICC(1) < 0,20 olan özellikler (EDA örneğinde eğim 0,09–0,15, hiza 0,11) baştan **"betimleyici, ayırt edici değil"** sınıfındadır: rapora yalnız değer olarak girer, A6'da yalnız Test 1'in çözünürlük ve kalem bozmalarından geçer (tam matris değil). İşaretli sınamada ölçütü geçmeyen özellik **"dışlandı"**; bir bozma ailesinde ölçütü kaçıran **"koşullu"**; ≥ 2 aileyi kaçıran **dışlanır**. Bu kural olmadan "dışlandı" her zaman geçit olurdu.
Ortak: her özellik **mm** cinsinden (ölçek A2'den), sayfa düzeyinde ve satır düzeyinde hesaplanır; sayfa özetleri medyan/IQR; her özellik bir **kalite bayrağı** taşır (üzeri çizili yoğunluk, soluk mürekkep, XXX maskesi, küçük örnek sayısı, devam sayfası); öğrenci içi kararlılığı ICC(1) ile raporlanır (EDA örneği: harf boyutu 0,55, eğim 0,15, hiza 0,11).

### 5.1 Bağlı bileşen / harf boyutu ve tutarlılığı
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) Bağlı bileşen yüksekliği/genişliği medyanı (EDA'da kullanıldı) | Basit | Bitişik yazıda birden çok harf = bir bileşen; çizgi silmede harfler bölünür; "bileşen ≠ harf" |
| (b) **Satır bandında x-yüksekliği:** taban çizgisi ile "orta çizgi" arası mürekkep yoğunluğu profilinden (dikey profil histogramı, orta bölgede platonun genişliği) | Bileşen bölünmesinden bağımsız; harf boyutuna yakın | Tek satırda az yazıda gürültülü; büyük harf ve uzantılar profili bozar |
| (c) Vuruş kalınlığı dönüşümü (stroke width) ve vuruş yüksekliği | Çizgi kalınlığından bağımsız boyut | Hesap pahalı; küçük harflerde belirsiz |
| (d) Harf adayı bölütleme (bileşen bölme) + harf boyu | Daha harf benzeri | Bitişik yazıda hatalı bölme, doğrulama için çok emek |
Öneri: birincil (b), ikincil (a) (karşılaştırma). Tutarlılık: satır içi ve satırlar arası IQR/medyan (CV). **Doğrulama:** 60 sayfada 10 harflik elle x-yüksekliği: hata ≤ %10; (a) ve (b)'nin elle ölçümle Spearman'ı; ölçeğin mm doğruluğu için çizgi aralığıyla çapraz kontrol (harf boyu çizgi aralığının makul bir oranı).

### 5.2 Satır hizası ve çizgilere uyum
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) Satır mürekkep ağırlık merkezinin çizgiye göre konumu (EDA) | Basit, sağlam | Uzantılar ve büyük harfler merkezi çeker |
| (b) **Taban çizgisi:** satır bandında ink'in alt zarfı (her x aralığında en düşük "gövde" vuruşunun medyanı) ile çizgi arası uzaklık | Harf yüksekliğinden bağımsız; "çizgiye oturma" doğrudan | Alt uzantıları ayıklamak gerek (yüzde 20–80 aralığı), kısa satırda gürültü |
| (c) Çizgiye değen/kesen ink piksellerinin oranı | Çok basit | Harf boyuna ve uzantıya bağımlı |
Öneri: birincil (b) (satır başına medyan uzaklık ve satırlar arası SD), karşılaştırma (a). **Doğrulama:** elle taban noktalarına göre hata ≤ 0,5 mm; satır sayısı ve kısa/uzun satır duyarlılığı. Bağımlılık: yazının uzunluğuna ve görev biçimine (mektup başlığı) duyarlı; görev bazlı raporlanır.

### 5.3 Yazı eğimi
Alt tanım: **taban çizgisi eğimi** (çizgiye göre). **Harf eğimi (italik açısı) bu planın kapsamı dışında** (ileride ayrı karar).
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) Satır başına taban çizgisi doğrusu (Theil–Sen / RANSAC) eğimi, çizgi eğimi çıkarılmış | Dayanıklı; çizgiye bağıl | Kısa satırda belirsiz; ICC düşük (EDA 0,09–0,15): gürültü mü gerçek mi ayrılamadı |
| (b) Sayfa/izdüşüm taraması (EDA'da tarama eğikliği için) | Tek sayı | Çizgi (güçlü sinyal) baskın; satır yazısı eğimini karıştırır, tarama eğikliğini yazı eğimi sanma riski |
| (c) **Harf eğimi:** dikey vuruşların yönelim histogramı (yamuk dönüşümüyle kayma taraması, Hough ya da gradyan yönü) | Gerçek "eğim" tanımına yakın | Elle yazıda belirsiz; ek doğrulama gerekir |
Öneri: (a) birincil (satır içi eğim, SD); (c) kapsam dışı. **Doğrulama:** elle taban noktalarından eğim; tekrar-ölçüm kararlılığı (aynı sayfanın farklı çözünürlükte, A6); öğrenci içi ICC düşükse "betimleyici ama ayırt edici değil" notu.

### 5.4 Sayfa kullanımı
Alt ölçümler: sol kenar boşluğu, sağ kenar kullanımı (satır sonu taşma), yazı bbox'ı, kullanılan satır oranı, ilk/son kullanılan çizgi, satır doluluk oranı.
| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) Maskeli mürekkepten bbox ve satır istatistikleri | Basit | Kod kutusu/XXX/not ve üzeri çizilmişlerden etkilenir; maske doğruluğuna bağlı |
| (b) Çizgi bandı kullanımına göre (hangi çizgilere yazıldı) | Sayfa organizasyonuna doğrudan | Yazı uzunluğuna bağlı |
| (c) **Yazı uzunluğuna göre düzeltilmiş** karşılaştırma (Textlänge kovaryat, görev x zaman içinde) | Uzunluk karıştırıcısını azaltır | Fotoğraf yüklemede kelime sayısı yok: o durumda yazı uzunluğu bandı (ink miktarı) ile aynı görev x zaman karşılaştırması kalır |
Öneri: (a)+(b) üretim özelliği olarak; (c) FD-LEX içi normlarda karşılaştırma stratejisi (kullanıcı fotoğrafında yalnız (a)+(b)). **Doğrulama:** kenar boşluğu elle ölçüm; kullanılan satır oranı ile Textlänge ilişkisinin görev x zaman içinde sayısallaştırılması (karıştırıcı kanıtı).

### 5.5 Çıktı biçimi
Sayfa başına JSON (özellik, değer, birim, kalite bayrakları, `HW_MEASUREMENT_VERSION`); öğrenci/ görev/ zaman bilgisi yalnız yerel analizde. Kapsam dışı: kelime aralığı, okunabilirlik skoru. Rapor dili: betimleyici, tanı yok.

## A6. Dayanıklılık testleri: çözünürlük, kalem rengi, tarama

**İlke:** çözünürlük–sınıf ilişkisi gözlemsel veriyle tam ayrıştırılamaz. **Aynı sayfaya uygulanan yapay bozmalar ölçümün çözünürlüğe/kaliteye duyarlılığının nedensel testidir**; gerçek tarayıcı, kâğıt ve sıkıştırma farklarını ve sınıf farkını **ayırmaz**. Gözlemsel kontrol (Test 2) bunu tamamlar, yerini almaz. **Hangi veri üzerinde:** bozma alt kümesi yalnız train'den (+ işaretli küme); ayar val'de; test'e dokunulmaz (§A7.4).

**Test 1 — Yapay bozma (kontrollü, aynı sayfa üzerinde).** Sabit bir alt küme (tabakalı 150 sayfa, train'den + 60'lık elle işaretli küme). Bozmalar: (i) çözünürlük 300→200→150→100 dpi (A2'deki ortak 150'ye indirgemeden önce de sonra da); (ii) JPEG kalitesi (yeniden sıkıştırma 90/70/50); (iii) bulanıklık (Gauss σ 0,5–1,5 px); (iv) kontrast/parlaklık değişimi; (v) renkli → gri → 1 bit eşikleme; (vi) hafif eğiklik (±0,5°) ve gürültü; (vii) kalem rengi: renkli sayfayı gri tonlamaya çevirmek, mavi kanal zayıflatma (soluk mürekkep benzetimi). Ölçüt (her özellik): **sıra korunumu** (Spearman, orijinal vs bozulmuş sayfa ölçümü) ≥ 0,90; **mutlak/göreli fark** medyan ≤ %5 (boyut: ≤ 0,2 mm; eğim: ≤ 0,1°); **kayma** ≤ öğrenciler arası IQR'nin %25'i. Sonuçlar özellik x bozma matrisi olarak yayımlanır; bir bozmada ölçütü kaçıran özellik "bu koşula duyarlı" bayrağı alır ve o koşuldaki sayfalarda kalite bayrağı yükselir.

**Test 2 — Gözlemsel sınıf/dpi karışıklığı (ikincil).** (a) Sınıf içinde dpi gruplarını karşılaştır (PDF03/04 vb. aynı sınıfta 150/200/300 birlikte, PDF05 iki sınıf); (b) PDF içi karşılaştırma; (c) sınıf farkının, dpi grubu **eşitlenmiş** alt kümelerde (örn. yalnız ~300 dpi sayfalar: sınıf 5'te 880, sınıf 9'da 2070 sayfa) yeniden hesaplanması. **Ölçüt (Test 1'den ayrı, eşdeğerlik testi):** dpi grupları arası fark için öğrenci bazlı bootstrap %90 güven aralığı, **±0,2 x havuzlanmış SD** eşdeğerlik payının tamamen içinde kalmalı (TOST mantığı). Her karşılaştırmada hücre başına öğrenci sayısı (n) ve aralık genişliği raporlanır; aralık payı aşacak kadar genişse (güç yetersiz) sonuç "eşdeğerlik gösterilemedi" sayılır (geçmiş değil). **Karıştırıcılar:** karşılaştırma PDF ve müdahale grubu içinde yapılır; ~300 dpi alt kümesinin hangi PDF/okul/gruptan geldiği (seçilim yanlılığı) ayrıca raporlanır. Geçmezse tek karar kuralı (§1): sınıf bazlı yüzdelik o özellik için raporlanmaz ya da dpi tabakalı raporlanır.

**Test 3 — Kalem ve renk uzayı.** Mavi/siyah/kurşun/yeşil kalem ve RGB/ICC/gri/1 bit sayfalarında özellik dağılımı (tabakalı; sınıf ve PDF kontrollü); elle işaretli kümede kalem türüne göre maske kalitesi. Soluk kurşun kalem ve gri/ikili sayfalar `mürekkep_zayıf`/`renksiz` bayrağıyla ayrı kovada.

(Devam sayfaları yalnız `devam_sayfasi` bayrağı taşır; ayrı test yapılmaz, n küçük.)

**Sonuç kararı:** her özellik için "kararlı / koşullu kararlı (hangi koşulda) / betimleyici, ayırt edici değil / dışlandı" tablosu (A5 kuralı) `docs/` altında; yalnız kararlı ve koşullu kararlı olanlar normlara girer.

## A7. Öğrenci bazlı bölme stratejisi

**Birim:** öğrenci kodu (938). Aynı öğrencinin 6 sayfası tek bölümde (KIDO'daki kuralla aynı). PDF'e göre değil koda göre gruplanır: 5 öğrenci PDF sınırında bölünmüş; tekilleştirilen sayfa kalan sayfalarla aynı öğrencide kalır.

**Bölmenin işlevi:** model yok; bölme (i) normların (referans dağılımlarının) yalnız **train**'den çıkarılması, (ii) ölçüm kararlarının (özellik seçimi, eşikler, bayraklar) **val**'de verilmesi, (iii) nihai raporlamanın (norm aktarımı) **test**'te bir kez yapılması içindir. Çizim modülündeki kuralla aynı: test, son değerlendirmeye kadar kullanılmaz.

| Seçenek | Avantaj | Sınırlama |
|---|---|---|
| (a) **Öğrenci bazlı, tabakalı** (sınıf x okul türü x grup x cinsiyet = 16 hücre; seed 42; 70 / 15 / 15 = ≈ 657 / 141 / 140 öğrenci) — **önerilen birincil** | Çizim modülüyle tutarlı; her hücreden temsil; en küçük hücre 38 (sınıf x okul x cinsiyet x grup) → val/test'te ≈ 6 öğrenci | Aynı sınıf/okuldan öğrenciler farklı bölümlerde olabilir (kümelenme sızıntısı) |
| (b) **Küme bazlı** (kodun ilk 4 karakteri: 49 küme, medyan 20 öğrenci; hipotez: sınıf/okul) | Sınıf/okul sızıntısını engeller | Küme sınıfa özgü: sınıf stratifikasyonu bozulur, küçük kümeler dengesiz bölünür, kümenin anlamı doğrulanmadı |
| (c) Hem (a) hem (b): (a) birincil, (b) **duyarlılık analizi** olarak aynı özelliklerin küme bazlı bölmede norm aktarımı (train normu → val/test) | İki ucu raporlar | İki bölme yönetmek gerekir |
Öneri: **(a) birincil, (c) duyarlılık**. Sızıntı etkisi: normlar özellik dağılımı olduğundan klasik anlamda "ezber" yok; ama aynı sınıfın/okulun (aynı öğretmen ve tarama partisi) normu val/test'e sızabilir; (b)'nin sonucu bu iyimserliğin boyutunu gösterir (çizimdeki "okul bazında sızıntı ölçümü" açık sorusunun karşılığı).
**Dpi dengesi (bölmeden önce yazılı kural):** öğrencinin dpi grubu = sayfalarının çoğunluk dpi grubu. Bölme sonrası, **yalnız meta veri düzeyinde** (ölçüm değerlerine bakmadan), sınıf içinde ~300 dpi öğrenci payı train/val/test arasında > 10 yüzde puan farklıysa (ya da PDF payı > 10 puan), **seed değiştirilmez**: dpi çoğunluk grubu beşinci tabaka olarak eklenip bölme **bir kez** aynı seed'le yeniden yapılır. Hâlâ aşılırsa dengesizlik raporlanır ve A6 Test 2 sonuçları bölümlere göre ayrı verilir. Dağılım raporu yalnız bölme anahtarlarını (sınıf, okul türü, grup, cinsiyet, dpi/PDF) içerir.
**Belirsiz öğrenciler:** bölmeye girerler (öğrenci düzeyinde); görev/zaman özgü norm hesabında `belirsiz` olan sayfalar dışlanır. **A7.4 Test bölümünün kullanımı (kural, A6'dan önce ayrı `docs/plan_el_yazisi_test.md` ile sabitlenir):** test özellik tablosu **bir kez** üretilir ve hash'i `docs/kararlar.md`'ye yazılır (çizimdeki `plan_test_metrikleri.md` kuralı gibi); "norm aktarımı makul" ölçütü (hangi özellik, hangi grup, hangi aralık) test üretilmeden önce yazılır; test özelliklerine seçim/ayar için bakılmaz; `splits.csv` hash'i ayrı dondurulur.
**Doğrulama:** aynı öğrenci iki bölümde değil (birim testi, çizimdeki `test_splits.py` gibi), tabaka sayıları ve sınıf/okul/grup/cinsiyet dengeleri, dpi/PDF dağılımı; `splits.csv`'nin sha256'sı `docs/kararlar.md`'ye yazılır (dondurma). Bölme **özellik hesabından önce** dondurulur (sonuca bakıp bölme seçilmesin).

## 4. Riskler ve açık sorular
1. **Kullanım izni** (EDA §5): yanıt olumsuzsa FD-LEX ana veri seti olamaz; planın A0 adımı ve yerel-only kuralı bu yüzden başta. Yanıt gelene kadar A1–A6 yerelde yapılır; çıktı olarak yalnız belgeler (özetler) commit'e girer, sayfa görüntüsü/kod/özellik tablosu girmez.
2. **Elle işaretleme emeği** (60 sayfa): kullanıcıdan ya da onaylı bir yöntemden gelmeli; yapılmazsa A3–A5 kabul ölçütleri doğrulanamaz, özellikler "doğrulanmadı" damgası taşır.
3. **Tarama/dpi/sınıf karışıklığı** tam çözülemeyebilir: gözlemsel ayrıştırma sınırlı; yapay bozma deneyi yalnız ölçümün bozmaya duyarlılığını gösterir, gerçek tarama farkının (örn. farklı tarayıcı cihazı) tüm etkisini göstermez. Raporda "sınıf farkı" yorumlanırken bu sınırlama yazılır.
4. **Kullanıcı fotoğrafları** ≠ FD-LEX taramaları (perspektif, gölge, farklı kâğıt): bu plan yalnız FD-LEX üzerinde ölçüm; fotoğraf hattı ayrı bir plan (sayfa bulma, perspektif düzeltme, çizgi aralığıyla ölçek).
5. `Rating`, `AlphabetTask`, `SLS`, `Wortschatz` anlamları bilinmiyor; veri sahibinden kod kitabı isteği ayrı iş (kullanıcı); o zamana kadar hiçbir amaçla kullanılmaz.
6. Norm adı: "referans dağılım" (popülasyon normu değil). Rapor taslağındaki "norm" dili el yazısı için gözden geçirilir.
7. **Ortak JSON sözleşmesi** (`docs/durum.md` sıradaki adım): sözleşme planı henüz yok; A5.5'in JSON biçimi **geçici** işaretlidir ve sözleşme kesinleşince uyarlanır (burada yalnız "değer + birim + kalite bayrakları + sürüm" öngörülür). A5 çıktı biçimi sözleşmeden önce dondurulmaz.
8. **Rapor satırı ve uyarı kuralı (taslak):** örnek satır: "Harf boyutu (x-yüksekliği): 2,8 mm; bu çalışma örnekleminde 5. sınıf akranlarının X. yüzdelik diliminde (görev: rapor, ölçüm zamanı 1)". Referans kırılımı **sınıf x görev x ölçüm zamanı** (495 / 443 öğrenci); okul türü, cinsiyet, grup kırılımı **norm için kullanılmaz** (hücre 38–150, çizimdeki `MIN_GROUP = 100` ölçütünü karşılamaz; cinsiyet ayrımı ilkesi). Çizimdeki ⚠ kuralı (akranların %5'inden azı bu kadar uçtaysa) aynen devralınır; grup 100'den küçükse "grup küçük" notu. `rapor_taslagi.md`'ye el yazısı bölümü, plan onaylanınca eklenir.
9. **Malaysian veri seti** bu planda kullanılmaz (yardımcı olarak korunur); olası tek rolü, ileride piksel düzeyinde dış sağlama (etiketsiz) olabilir ve ayrı karar gerektirir. Disgrafi etiketleri hiçbir ölçümde ya da raporda kullanılmaz (tanı/risk ilkesi).

## 5. Uygulama sırası, süre tahmini, iş akışı
A0 (0,5 gün) → A1 (1) → A7 (0,5) → A2 (1) → A3 (2, işaretleme dahil) → A4 (1) → A5 (3) → A6 (2) → rapor ve kapanış (1). Her adımda: küçük commit'ler (temizlenmiş), `tests/test_handwriting_*.py` sentetik testler, dogrulayici raporu `docs/dogrulama/`. Aşama sonunda denetleyici sonucu denetler. Tahminler kaba; elle işaretleme ve bozma deneyi süreyi belirler.

## 6. Onay bekleyen kararlar
1. Çalışma çözünürlüğü: 150 dpi (öneri) mi 200 dpi mi?
2. Bölme: 70/15/15, (a) birincil + (c) duyarlılık (öneri) mi?
3. Elle işaretleme: 100 sayfa (ayar 50 + sınama 50, 10 sayfa tekrar), kim işaretler? Onaydan sonra **donan** kabul ölçütleri: A3 maske/taban/x-yüksekliği ölçütleri, A5 sınıflama kuralı, A6 Test 1 (Spearman ≥ 0,90, medyan fark ≤ %5, kayma ≤ IQR'nin %25'i) ve Test 2 (%90 GA ±0,2 SD içinde), A7 dpi dengesi kuralı (> 10 puan), 910 öğrenci doğrulama ölçütü. Hangileri açık bırakılacak?
4. Bu ölçütler uygun mu (yukarıdaki liste)?
5. (Karar verildi, önerilen:) Harf eğimi bu planda kapsam dışı; yalnız taban çizgisi eğimi.
6. `extracted/` klasöründe kayıpsız çıkarma yerel diske yazılır (öğrenci tarama kopyası): kabul mü? (Yerel kalır, git ve Drive dışı; kapak sayfaları çıkarılmaz.)
7. OneDrive "klasör yedekleme" ayarının kapalı olduğunun doğrulanması (kullanıcı).
8. Kullanım izni yanıtı gelmeden A3'e geçilmemesi (izin geçidi) kabul mü?
