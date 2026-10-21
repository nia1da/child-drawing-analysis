# Plan: görev uyumu ve mutlu–üzgün ayrışma (aşama 3'ün parçası)

Durum: onaylandı (2026-10-21; denetleyici önerileri işlendi). Hedef rapor satırları
(`docs/rapor_taslagi.md`): "Görev uyumu" (her çizim) ve "Mutlu–üzgün ayrışma" (iki çizim birlikte).

## Sabitler (değişmez, CLAUDE.md)
- Model: donmuş referans model `convnext_tiny_320px_lr0.0001_ls0.1_s42.pt` (val F1 0.8095, en iyi epoch 11).
  Yeni eğitim ya da sınıflandırıcı denemesi yok.
- Çıktı ruh hali olarak sunulmaz. Model sadece "bu çizim KIDO'da hangi göreve çizilmiş çizimlere benziyor" sorusunu
  yanıtlar.
- Cinsiyet model girdisi, norm grubu ya da norm dosyası sütunu değildir. Gruba özel eşik ya da gruba özel not yok.
- Test seti en sona kalır; normlar ve bütün seçimler val ile yapılır. Geliştirme sırasında örnek raporlar val ya da
  train görüntülerinden üretilir, test görüntülerinden değil (CLAUDE.md'deki örnek komut bir test görüntüsü
  kullanıyor; bu aşamada kullanılmaz).

## Tanımlar
- **Model skoru** `p` = modelin "üzgün" olasılığı (`olasilik_uzgun`, değerlendirmedeki dönüşümle, 320px).
- **Görev uyumu** (tek çizim): mutlu görevinde `1 − p`, üzgün görevinde `p`. Görev dosya adından ya da `--task`'tan.
  Raporda olasılık olarak değil, karşılaştırma grubundaki **yüzdelik** olarak sunulur; taslaktaki "%83 benzerlik"
  ifadesi kalkar (ham olasılık benzerlik yüzdesi değil). Yüzdelik monoton dönüşümlerden etkilenmez: olasılık / logit
  ya da kalibrasyon seçimi görev uyumu yüzdeliğini değiştirmez. Metin önerisi: "Görev uyumu (mutlu): modelin bu
  çizimi KIDO'daki 'mutlu' görevi çizimlerine benzetme derecesi, karşılaştırma grubunun X. yüzdelik diliminde."
  Ad "görev uyumu" kalır ama metinde her zaman bu açıklamayla; "çocuk görevi yapamadı" diye okunmamalı.
- **Mutlu–üzgün ayrışma** (aynı çocuğun iki çizimi): `d = s(üzgün çizim) − s(mutlu çizim)`; `s` olasılık ya da logit
  (burada sıra değişebilir, karar val'de, adım 2). JSON'da `d` değeri ve işareti tutulur, yüzdeliğin yanında.
  `d < 0` (model mutlu çizimi üzgün çizimden daha "üzgün" görüyor) metinde nötr ifadeyle: "model iki çizimi
  görevlerinin tersi yönünde sıralıyor".

## Normların kaynağı
Train çizimleri modelin eğitim verisi: skorları iyimser, norm olamaz. Out-of-fold skorlar yeniden eğitim gerektirir,
dondurma kararıyla çelişir. Test son değerlendirmeye ayrılı. Norm kaynağı **val**: 1386 çizim, 693 öğrenci (her
öğrencinin tam 2 çizimi). İyimserlik payı: val yalnız epoch seçiminde değil, **bütün model ve ayar seçiminde**
(boyut, lr, ls, model) ve `analysis` eşiğinde kullanıldı; pay testte ölçülür (adım 5, norm aktarımı). Adım 2'deki
tanım kararları da aynı val'den gelir; test ayrı kaldığı sürece kabul, belgelenir.

**Gruplama (karar gerekiyor, adım 2'deki analize bağlı):** val sınıf x görev grupları 44–134 çizim (1: 44, 2: 53,
3: 134, 4: 115, 5: 116, 6: 93, 7: 83, 8: 55). ⚠ verilmediği için `MIN_GROUP`'un gerekçesi (kuyruk birkaç çizime
dayanır) burada geçerli değil; küçük grubun sorunu yüzdeliğin örnekleme oynaklığı.
1. **Eğitim seviyesi x görev** (ilkokul 1–4 / ortaokul 5–8; 346 / 347 çizim): oynaklık düşük. Ama ilkokul havuzunun
   %72'si 3. ve 4. sınıf; seviye içinde skorda sınıf eğilimi varsa 1. sınıf sistematik olarak düşük yüzdelik alır.
2. **Sınıf x görev**, küçük grup notuyla: grup raporun ölçüm bölümüyle aynı, ama yüzdelikler oynak (44 çizimde bir
   sıra ≈ 2,3 yüzdelik puanı).
**Karar ölçütü** (2026-10-21'de, val tahminleri üretilmeden önce yazıldı; analizden sonra değiştirilmez):
- Hücreler: görev uyumu için 4 (ilkokul / ortaokul x mutlu / üzgün, çizim başına bir değer), ayrışma için 2
  (ilkokul / ortaokul, öğrenci başına bir `d`). Toplam 6 karşılaştırma.
- **İstatistiksel ölçüt:** her hücrede sınıf düzeyleri arasında Kruskal–Wallis testi; anlamlı: p < 0,05 / 6 ≈ 0,0083
  (Bonferroni).
- **Pratik ölçüt:** her hücrede, her sınıfın değerlerinin seviye havuzundaki yüzdeliklerinin (orta sıra) medyanı;
  bir sınıfın medyanı 50'den en az 10 puan sapıyorsa belirgin.
- **Belirgin eğilim:** herhangi bir hücrede iki ölçüt birden sağlanırsa.
- Karar: belirgin eğilim yoksa seçenek 1 (eğitim seviyesi x görev); varsa seçenek 2 (sınıf x görev, "grup küçük"
  notuyla). Seviye içi düzeltme (örn. sınıfa göre kaydırma) yapılmaz.
- `d` için skor: olasılık farkı. Val çiftlerinin %25'inden fazlasında iki çizimin skoru da aynı uçta yığılıyorsa
  (iki `p` de < 0,1 ya da iki `p` de > 0,9) logit farkı kullanılır. Bu seçim gruplama ölçütünden önce yapılır.
- Sonuç (test istatistikleri, medyanlar, karar) `docs/olcumler.md`'ye ve `docs/kararlar.md`'ye yazılır.

Seçenek 1 seçilirse metin raporda ve JSON `karsilastirma_grubu`'nda grup ve n açıkça yazılır ("ilkokul (1–4. sınıf)
normu, n=346"); ölçüm bölümünün sınıf normuyla karıştırılmasın.

## ⚠ ve uyarı kuralları
- Görev uyumu ve ayrışmada ⚠ **verilmez**; sadece yüzdelik ve sınırlama notu. Sebep: %5 kuralı modelin hatasını
  (ilkokul erkek mutlu çizimlerinde "üzgün" yönlü hata) ⚠ olarak bu gruba taşır; düzeltmek cinsiyet girdisi
  gerektirir, ki yasak. "%5 kuralı + alt grup sıklığı" alternatifi reddedildi.
- Görev uyumu ve ayrışma taslaktaki "⚠ Tipik aralık dışında kalanlar" özetine girmez ve ileride görüşme önerisi
  kurallarını (aşama 7) tetiklemez.
- Düşük bir yüzdelik ⚠ olmasa da bulgu gibi okunabilir: sınırlama notu her raporda bu bölümün hemen altında durur.

## Adımlar
1. **Val tahminleri:** referans model için `evaluation --split val` (`tahminler/{deney}_val.csv`); mevcut kod yeterli.
   Train tahminleri sadece iyimserliği göstermek için, norm değil.
2. **Val analizi (betimleyici):** görev uyumu ve `d` dağılımları; eğitim seviyesi ve **sınıfa göre eğilim**
   (gruplama kararı); `d` için olasılık mı logit mi; label smoothing yüzünden skorların uçlarda (≈ 0,9–0,95)
   yığılması: üst yarıdaki yüzdelik farkları küçük olasılık farklarına dayanıyorsa kaba bantlar ya da not.
   Kalibrasyon ayrı iş kalemi değil, bir paragraflık not (yüzdeliği etkilemez).
3. **`docs/olcumler.md`'ye "Model tabanlı ölçümler" bölümü** (rapora girmeden önce): tanım, norm kaynağı (val, n),
   iyimserlik payı, monotonluk notu, gruplama ve sınırlamalar.
4. **Norm dosyası:** `normlar/model_normlari.csv`: val çizimleri ve öğrenci çiftleri (dosya, öğrenci, sınıf, seviye,
   görev, skor; cinsiyet sütunu yok), model adı ve dönüşüm sürümüyle. Model ya da dönüşüm değişirse normlar geçersiz
   (`MEASUREMENT_VERSION` benzeri sürüm).
5. **Rapor:** JSON'a `model_olcumleri` bölümü (model adı, görev uyumu yüzdeliği, `d` ve işareti, grup ve n, notlar).
   Rapor komutu iki görüntü alabilir (`src.report mutlu.jpg uzgun.jpg`; KIDO adlarında aynı öğrenci kontrolü).
   Notlar: çizim KIDO **train**'de ise "çizim modelin eğitim verisinde, skor iyimser"; **val**'de ise "çizim
   karşılaştırma grubunun içinde". Model yüklenemezse (torch ya da `.pt` yok) ölçüm raporu yine çıkar, bölüm
   "çalışmadı" olur. Çıkarım CPU'da da çalışır.
6. **Test metrikleri (bir kez, en son; sonuca göre tanım ya da eşik değişmez):**
   - ayırt edicilik: AUC (val ve test karşılaştırmalı), macro F1 (0,5 eşiği, sadece referans), çiftlerde `d > 0`
     oranı (eşleştirilmiş AUC);
   - **norm aktarımı**: test çizimlerinin val normlarındaki yüzdelik dağılımı (5., 50., 95. altında kalan oranlar;
     grup bazında; görev uyumu ve `d` için ayrı) — val iyimserlik payını doğrudan ölçer;
   - alt gruplar: cinsiyet, eğitim seviyesi, **sınıf düzeyi**, ilkokul x cinsiyet kesişimi;
   - 320px modelde hata yönü (`analysis.error_direction`, mutlu→üzgün oranı);
   - alt gruplara göre en alt %5 sıklığı (sadece belgeleme, ⚠ kararını değiştirmez);
   - öğrenci bazlı bootstrap %95 GA: `stats.confidence_intervals` şu an sadece macro F1 veriyor; AUC, `d > 0` oranı
     ve norm aktarımı oranları için genişletilir.
   Sonuçlar rapora ve `docs/olcumler.md`'ye "bu ölçümün doğruluğu" olarak girer.
7. **Denetim:** her adım sonunda dogrulayici; aşama sonunda denetleyici.

## Rapor dili ve sınırlamalar (her raporda aynı, koşulsuz)
- "Görev uyumu, çizimin KIDO'daki aynı görev çizimlerine modelce benzerliğidir; çocuğun duygu durumunu göstermez."
- "Model ilkokul erkek çocukların mutlu çizimlerini daha sık 'üzgün' görevine benzetir; bu gruptaki çocuklarda düşük
  görev uyumu ve düşük ayrışma daha sık beklenir." Sayı kaynağıyla: şimdilik 448px modelde test %33,7; adım 6'da
  referans 320px model için güncellenir. Not cinsiyete göre koşullu gösterilmez (gösterim cinsiyete göre değişmesin);
  koşullu gösterim istenirse ayrı kullanıcı kararı.
- Seyrek / az renkli çizimlerde görev uyumu düşebilir; ölçüm bölümündeki doluluk ve renk sayısıyla birlikte okunmalı.
- Normlar KIDO (Şanlıurfa, 1–8. sınıf) val bölümünden; başka bir örneklemde dağılım farklı olabilir.

## Kapsam dışı
- Sınıf düzeyi tahmini ("gelişimsel konum") aşama 3'ün ayrı parçası, bu planda yok.
- Modeli yeniden eğitme, kalibrasyon için model değiştirme.
