# Referans analizi ve makine öğrenmesi fizibilitesi (Scriptoria)

Tarih: 2026-11-25. Bu belge **uygulanabilirlik değerlendirmesidir**; hiçbir araştırma sorusu için gerçek sayfa ölçümü yapılmadı (izin geçidi). Sayılar yalnız meta veriden
(Excel + `pages.csv` + dondurulmuş bölme) ve güç hesaplarından gelir. Hiçbir bulgu bir bozukluk, gelişimsel gerilik ya da risk göstergesi olarak yorumlanmaz; yaş tahmini yapılmaz.
Kaynaklara dayanan bilgi için `docs/el_yazisi_bilimsel_temel.md`.

## 1. Eldeki yapı (meta veri düzeyi, doğrulandı)

- 938 öğrenci, 6 yazı/öğrenci (2 görev x 3 ölçüm zamanı); **910 öğrenci temiz** (6 sayfa, tekrarsız), 28 öğrencide görev/zaman belirsiz (analizlerde görev/zaman bazında dışlanır).
- Temiz öğrenci, sınıf x grup: sınıf 5: 232 müdahale / 245 kontrol; sınıf 9: 221 / 212.
- **Dondurulmuş bölme** (öğrenci bazlı, tabakalı, seed 42; `splits.csv` sha256 `1b53691ce776a85c025ed78c8c0a4ccd7a7ac3cda67f303d0447649d71890ea4`): train 656, val 141, test 141. Train içinde temiz öğrenci: sınıf 5: 334, sınıf 9: 301; sınıf x okul x cinsiyet hücrelerinin en küçüğü 61.
- Çoğunluk tarama çözünürlüğü (temiz öğrenci): sınıf 5: ~150 dpi 96, ~200 dpi 260, ~300 dpi 121; **sınıf 9: ~150 dpi 0, ~200 dpi 49, ~300 dpi 384** (%89 ~300 dpi). dpi dengesi kuralı bölmede tetiklenmedi (en büyük fark 9,2 puan, eşik 10 puan: sınırda).
- PDF'ler sınıfla neredeyse örtüşür (PDF01–04 yalnız sınıf 5, PDF06–08 yalnız sınıf 9, PDF05 karışık) ve kontrol/müdahale grubuyla da kısmen: **sınıf, tarama partisi, çözünürlük ve grup tasarım gereği birlikte değişiyor**.

## 2. Araştırma soruları ve uygulanabilirlik

Gruplanma ilkesi: sayfalar öğrenci içinde bağımlıdır; analizler öğrenci düzeyinde (öğrenci başına ortalama ya da öğrenci rastgele etkili karma model) yapılır. Etki büyüklüğü ve güven aralığı raporlanır; p değeri tek başına karar ölçütü değildir.

| # | Soru | Uygulanabilirlik | Güç (meta veriden) | Temel risk |
|---|---|---|---|---|
| 1 | 5. ve 9. sınıf arasındaki geometrik özellik farkları | **Uygulanabilir, yorumu sınırlı** | Tüm öğrenciyle (938) tespit edilebilir standart fark d ≈ 0,18, temiz 910 ile ≈ 0,19; yalnız train ile ≈ 0,22 (güç .80, α .05; normal yaklaşım) | Sınıf, PDF/tarama partisi, dpi (sınıf 9'da %89 ~300 dpi) ve yaş birbirinden ayrılamıyor |
| 2 | Aynı öğrencinin zaman içindeki değişimi | **Uygulanabilir** (önce kontrol grubu, aynı görev türü) | Eşleşmeli değişim: 938 öğrenci dz ≈ 0,09; yalnız kontrol 457 temiz öğrenci ≈ 0,13 | Ölçüm gürültüsü ile gerçek değişim ayrılamıyor; MZP arası süre bilinmiyor; müdahale etkisi |
| 3 | Benzer sınıf ve görev gruplarındaki referans dağılımları | **Uygulanabilir** (sınıf x görev x ölçüm zamanı) | Train'de hücre başına 334 / 301 öğrenci; yüzdelik standart hatası ≈ ±2,7–2,9 puan (medyan), ≈ ±1,2–1,3 puan (5. ve 95.) | Ek kırılımlarda (okul x cinsiyet) hücre ≥ 61 < 100 (`MIN_GROUP` ve cinsiyet ayrımı ilkesi); tarama farkı referansa girer |
| 4 | Çok değişkenli anomali tespiti | **Teknik olarak uygulanabilir, anlamlı doğrulaması yok** | – | Referans etiket yok: duyarlılık/özgüllük hesaplanamaz; "anomali" büyük ölçüde ölçüm hatası ve tarama partisini yakalar |
| 5 | PCA ve kümeleme ile örüntü keşfi | **PCA: uygulanabilir ve yararlı (tanılama); kümeleme: yalnız keşif** | ~8–10 özellik, ~5.6 bin sayfa | Kümelerin PDF/dpi/görev/yazı uzunluğunu yansıtması beklenir (yapay örüntü) |

### Soru 1: 5. ve 9. sınıf farkları
- **Tasarım:** öğrenci düzeyinde (görev x zaman ortalaması ya da görev ve zamanı sabitleyip karma model). Aynı görev ve ölçüm zamanında karşılaştır (ör. Ber MZP1: sınıf 5 vs sınıf 9); yazı uzunluğunu (`Textlänge`) kovaryat yap, çünkü sayfa kullanımı özellikleri ona bağlı.
- **Karıştırıcılar:** (a) yaş (sınıf içi yaş SD ≈ 6 ay, sınıf ile neredeyse doğrusal bağlı); (b) tarama: sınıf 9'un %89'u ~300 dpi, sınıf 5'inki %25; (c) PDF/parti: sınıf 5 ve 9 farklı PDF'lerde; (d) okul türü ve müdahale grubu; (e) görev metinleri sınıfa göre farklı olabilir (bilinmiyor).
- **Azaltma (tam çözüm değil):** ortak 150 dpi çalışma çözünürlüğü; aynı dpi grubunda karşılaştırma (~300 dpi: sınıf 5'ten 121, sınıf 9'dan 384 öğrenci; ~200 dpi: 260'a 49); PDF5 (iki sınıfı birlikte içeriyor) ile iç tutarlılık; eşdeğerlik testi (plan A6 Test 2). Yapay bozma deneyleri ölçümün çözünürlüğe duyarlılığını gösterir, sınıf farkını tarama farkından ayırmaz.
- **İddia sınırı:** "Bu örneklemde 5. ve 9. sınıf öğrencilerinin sayfaları şu özelliklerde farklı" denebilir; "9. sınıfta yazı gelişmiştir" ya da "farkın nedeni yaştır" denemez.

### Soru 2: zaman içinde değişim
- **Tasarım:** aynı görev türü (Ber MZP1→MZP3, Arg MZP1→MZP3) ve öğrenci eşleşmeli fark; **önce kontrol grubu** (müdahalenin hedefi yazı içeriğidir [yayında]; el yazısına etkisi bilinmiyor); müdahale grubu ayrı rapor.
- **Güvenilir değişim eşiği:** statik görüntüde klasik test-tekrar-test yok. Eşik için tahminler: (i) aynı sayfanın yapay yeniden işlenmiş sürümleri (tarama/çözünürlük gürültüsü), (ii) aynı ölçüm zamanında Ber ve Arg arasındaki fark (görev etkisini de içerdiği için gürültünün **üst sınırı**), (iii) elle işaretleme ile ölçüm hatası. Eşik tanımlı olmadan raporda "değişim" yorumlanmaz (`report.py` bunu zorlar).
- **Sınırlar:** MZP'ler arası gerçek süre bilinmiyor; yalnız "1., 2., 3. ölçüm" denir; 28 belirsiz öğrenci dışarıda (uzun yazanlar olabilir, seçilim yanlılığı raporlanır); alıştırma etkisi ve görev farkı.
- **EDA ön bulgusu (n = 48, ön sonuç):** boyut öğrenci içinde kararlı (ICC 0,55); hiza özellikleri düşük (0,09–0,15): hiza değişiminin raporlanması için daha güvenilir ölçüm gerekebilir.

### Soru 3: referans dağılımlar
- **Birim:** sınıf x görev x ölçüm zamanı (train, temiz öğrenci). Yüzdelik, ampirik sıra; karma/ayrı tahmin gerekmez. Standart hata yukarıdaki gibi: uçlarda (≈ %5) ≈ ±1,2–1,3 puan, bu nedenle %5 kuyruk kuralı (≥ 100 kişi) uygulanabilir.
- **Kırılımlar:** okul türü, cinsiyet, müdahale grubu referans ekseni **yapılmaz** (hücre küçülür; cinsiyet ayrımı çizim modülü ilkesiyle uyumsuz). Müdahale grubunun etkisi için duyarlılık analizi (MZP1 ve kontrol grubu).
- **Aktarım:** referans bu taramalar içindir; kullanıcı fotoğrafı (telefon) için ölçek/kâğıt farkı ayrı iştir. Normlar val'de aktarım denemesi, test son (çizim modülü kuralı).

### Soru 4: çok değişkenli anomali tespiti
- **Yöntemler:** sağlam Mahalanobis uzaklığı (MCD), PCA artığı; isolation forest/LOF ek yorumlanabilirlik getirmez.
- **Neden raporun parçası olmamalı (v1):** (1) referans etiket yok: hangi "anomali" bir ölçüm hatası, hangisi gerçek özellik, doğrulanamaz; (2) beklenen bulgular: kötü çizgi tespiti, kalem/tarama farkı, atlanan satırlar, kısa yazılar (kalite bayrağı olması gereken durumlar); (3) çıktı "alışılmadık" dilini yaratır ve tanı yönünde okunma riski taşır.
- **Önerilen kullanım:** yalnız **kalite kontrol** (hangi sayfaların elle bakılması gerektiği); uzman raporunda tek değişkenli yüzdelik ve işaretli bölgeler yeterli. İleride eklenecekse: önce ölçüm güvenilirliği doğrulanır, sağlam Mahalanobis seçilir, her işaretli sayfa görsel incelenir, "bu örneklemde seyrek kombinasyon" dili kullanılır.

### Soru 5: PCA ve kümeleme
- **PCA (yararlı):** özellikler arası fazlalık (ör. boyut ve çizgi aralığı oranları), baskın eksenler, **parti etkisi tanılaması**: ana bileşenlerde sınıf, PDF, dpi, kalem türü ve yazı uzunluğunun açıkladığı varyans (karma model/R²). Ölçüm kalitesi hakkında bilgi verir; çocuk sınıflandırması değildir.
- **Kümeleme (keşif):** k-ortalamalar/Gauss karışımı; **kararlılık** (bootstrap ARI) ve kümelerin PDF/dpi/görev ile kesişimi raporlanır. Kümeler tarama partisi ya da yazı uzunluğuyla örtüşüyorsa yapay sayılır. Etiket yok; kümelerin klinik/gelişimsel anlamı yoktur ve verilmez.
- **Uygulama sırası:** özellikler tüm sayfalarda çıkarıldıktan (izin sonrası, doğrulanmış özellikler) ve parti etkisi PCA ile görüldükten sonra.

## 3. Makine öğrenmesi gerçekten ek fayda sağlar mı?

| İş | Basit istatistik yeterli mi? | ML'nin ek faydası | Karar |
|---|---|---|---|
| Sınıf farkı | Karma model, etki büyüklüğü, eşdeğerlik | Yok (tahmin amacı yok) | ML yok |
| Zaman içi değişim | Eşleşmeli karma model, güvenilir değişim eşiği | Yok | ML yok |
| Referans dağılımı | Ampirik yüzdelik (± nicel regresyon, gerekirse) | Yok; yorumlanabilirlik kaybı | ML yok |
| Anomali tespiti | Tek değişkenli yüzdelik + (kalite için) sağlam Mahalanobis | Küçük; doğrulama imkânsız | Rapor dışı, yalnız QC |
| Yapı keşfi | PCA, korelasyon, varyans ayrıştırma | Kümeleme: sınırlı, yapay örüntü riski | Keşif amaçlı, yorum yok |
| Yaş/sınıf tahmini | – | Normlar zaten sınıfa göre (döngüsel), klinik anlamı yok | **Yapılmaz** |
| Harf/kelime segmentasyonu, HTR | Klasik yöntemler sınırlı (bitişik yazı) | **Gerçek fayda** (transkriptlerle) | Gelecek çalışma: `docs/el_yazisi_gelecek_calisma.md` |

**Öneri:** v1'de eğitilmiş model yok. Sırf ML kullanmış olmak için model geliştirilmez; fayda, görüntü-transkript eşleştirmesiyle karakter/kelime segmentasyonu gibi *ölçümün kendisini* iyileştirecek işlerde beklenir.

## 4. Gerekli önkoşullar (sıra)
1. Kullanım izni → 20 öğrencilik pilot (`docs/el_yazisi_pilot_protokolu.md`) → gözlenen sorunlara göre düzeltme.
2. Elle işaretleme ve ölçüm güvenilirliği (A3/A6) → özelliklerin "kararlı / koşullu / betimleyici / dışlandı" sınıflaması.
3. Yalnız kararlı özelliklerle: tüm sayfalarda çıkarma (train → val → test sırası), PCA tanılaması, sorular 1–3.
4. Soru 4–5 yalnız yukarıdakiler tamamlandıktan sonra.

## 5. Yorum ilkeleri (özet)
- Hiçbir fark, değişim ya da uç değer bozukluk/gelişimsel gerilik göstergesi olarak yorumlanmaz; yaş tahmini yapılmaz.
- Bilimsel kaynakla desteklenen (`docs/el_yazisi_bilimsel_temel.md` [kaynak]) ile hipotez/varsayım ayrı etiketlenir; hipotezler (H1–H4) veriyle sınanır.
- Çoklu karşılaştırma (özellik x görev x zaman): önceden listelenmiş az sayıda ana ölçüm; düzeltme ya da keşif/doğrulama ayrımı (train'de keşif, val'de doğrulama, test son).
