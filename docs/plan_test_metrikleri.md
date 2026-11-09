# Plan: görev uyumu planı adım 6, test metrikleri (aşama 3'ün parçası)

Durum: onaylandı (2026-11-10; denetleyici önerileri işlendi). Kullanıcı kararları: norm aktarımı
eşiği ±5 puan makul; çalıştırma yerelde. Üst plan: `docs/plan_gorev_uyumu.md` (adım 6).

## Amaç
Donmuş referans modelin (`convnext_tiny_320px_lr0.0001_ls0.1_s42`) görev uyumu ve ayrışma çıktılarının doğruluğunu,
test setinde **bir kez** ölçüp rapora "bu ölçümün doğruluğu" olarak yazmak. Sonuç tanımı, eşiği, normları ya da
modeli **değiştirmez** (üst plan). Sonuç kötü çıksa da sayılar olduğu gibi raporlanır.

## Dürüstlük notu (olcumler.md ve kararlar.md'ye de yazılır)
Test seti daha önce 448px modelle görüldü (test F1, alt grup F1'leri, hata yönü %33,7, bootstrap farkları). Alt grup
hipotezleri (ilkokul erkek) o bakıştan geliyor; burada 320px referans modelde ilk ve tek kez ölçülüyor. Bu bir
yeniden doğrulamadır, bağımsız keşif değil.

## Önce yazılan kurallar (test tahminleri üretilmeden önce; sonra değiştirilmez)
- **Bu plan, test tahminleri üretilmeden önce commit'lenir** (metrik listesi ve hüküm kuralı sonuçtan önce yazılmış
  sayılsın diye).
- "Bir kez" koda bağlanır: `evaluation` var olan bir `*_test.csv`'nin üzerine yazmaz (hata verir). `final_metrics`
  modele hiç girmez, yalnız CSV'yi okur. Çalıştırma sonrası CSV'nin hash'i ve tarihi `docs/kararlar.md`'ye yazılır.
  Çalıştırma sırasında Colab'da eğitim/yazma olmadığı teyit edilir.
- `d` skoru val'de seçilip donduruldu (`separation_score`: olasılık farkı); testte aynısı kullanılır.
- **Birincil metrikler:** genel AUC, `d > 0` oranı, norm aktarımı (iki uç oranı). Diğer her şey (alt gruplar, hata yönü,
  alt %5, farklar) betimleyici ve düzeltmesizdir; alt grup farkları için "anlamlı" denmez, GA'lar sadece aralık olarak
  verilir (çoklu karşılaştırma; üst plandaki Bonferroni kaygısıyla tutarlı).
- Test görüntüleri modele **bir kez** sokulur: `PY -m src.evaluation --experiment convnext_tiny_320px_lr0.0001_ls0.1_s42
  --split test` → `tahminler/{deney}_test.csv`. Dosya zaten varsa komut çalıştırılmaz. Bütün metrikler bu CSV'den
  hesaplanır; test görüntüsü başka yerde kullanılmaz.
- Metrik listesi aşağıdakiyle sınırlı; sonuca bakıp metrik eklenmez ya da çıkarılmaz. Hesaplanan her şey raporlanır.
- Normlar val'den (`model_normlari.csv`, sürüm 1) olduğu gibi kullanılır; test çizimleri norma girmez.
- **Norm aktarımı hükmü (eşik ±5 puan, kullanıcı onayladı), GA'ya bağlı:** iki uç oranı: test çizimlerinin val
  normundaki yüzdeliği ≤ 5 olanların oranı ve ≥ 95 olanların oranı (beklenen %5). Bir uç oranının bootstrap GA'sının
  alt sınırı %10'un üstündeyse o uç için "zayıf"; üst sınırı %10'u geçmiyorsa "makul"; GA %10'u içeriyorsa
  "belirsiz". Sapmanın yönü yazılır (alt uç beklenenden fazlaysa "sistematik düşük skor", iyimserlik değil). Oran
  < 5 / < 50 / < 95 yerine ≤ 5, ≥ 95 olarak tanımlanır; 50. yüzdelik altı oranı betimleyici olarak ayrıca verilir,
  hükme girmez. Grup n < 100 ise hüküm verilmez, yalnız sayı ve GA. Yüzdelik, test skorunun **val dağılımındaki
  konumudur** (rapordaki `norms.percentile` ile aynı orta sıra), test içi sıra değil.

## Metrikler (test: 1632 çizim, 816 öğrenci; her öğrenci 1 mutlu + 1 üzgün)
1. **Ayırt edicilik:** AUC (çizim düzeyinde, `olasilik_uzgun` ile gerçek etiket), val ve test yan yana; macro F1
   (0,5 eşiği, yalnız referans); öğrenci çiftlerinde `d > 0` oranı (= eşleştirilmiş AUC), `d` olasılık farkı
   (val kararı). Val–test AUC farkı tek sayı olarak, yorumsuz verilir (iyimserlik payı; kümeler ayrı olduğu için
   fark GA'sı gerekmez).
2. **Norm aktarımı:** her test çiziminin val normlarındaki yüzdeliği (rapordakiyle aynı fonksiyon, `norm_group`
   mantığı: görev uyumu için seviye x görev, `d` için seviye). Oranlar: yüzdelik < 5, < 50, < 95 (beklenen 5 / 50 /
   95). Görev uyumu ve `d` ayrı; hücre başına (seviye x görev) ve genel.
3. **Alt gruplar** (hepsi için AUC, macro F1, `d > 0` oranı, görev uyumu ortalaması; betimleyici, düzeltmesiz): cinsiyet, eğitim seviyesi,
   sınıf düzeyi (1–8), ilkokul x cinsiyet kesişimi (diğer kesişimler `stats.GROUPS` ile tutarlı olsun diye de
   eklenir: ortaokul x cinsiyet).
4. **Hata yönü:** `analysis.error_direction` 320px modelde (mutlu→üzgün oranı, alt gruplara göre). Raporun
   sınırlama notundaki "448px, test %33,7" ifadesi bu sayıyla **değiştirilir** (`task_fit.LIMITATIONS`); not hâlâ
   cinsiyete göre koşullu gösterilmez.
5. **En alt %5 sıklığı:** alt gruplara göre görev uyumu yüzdeliği < 5 olan çizim oranı (val normuyla). Sadece
   belgeleme; ⚠ kararını değiştirmez.
6. **Güven aralıkları:** öğrenci bazlı bootstrap %95 GA (aynı öğrencinin iki çizimi bağımlı; 2000 yeniden örnekleme,
   seed 42): AUC, macro F1, `d > 0` oranı, norm aktarımı oranları, `stats.DIFFERENCES` farkları (sınıf düzeyleri
   arası fark yazılmaz, sınıf düzeyi için yalnız grup değerleri). Küçük grupta (n < 30 öğrenci) GA yazılır ama
   "geniş" notuyla. Sınırlama olarak yazılır: norm aktarımı GA'sında val normu sabit alınır, val'in kendi örnekleme
   belirsizliği dışarıda.

## Uygulama (onaydan sonra)
1. **Test tahminleri:** yukarıdaki tek `evaluation` çalıştırması (yerelde, RTX 4060; ~1632 görüntü). Colab'da değil:
   Drive'daki `tahminler/` klasörüne yazar, `deneyler.csv`'ye yazmaz.
2. **Bootstrap yardımcısı:** `stats.confidence_intervals` (multinomial ağırlık + einsum, F1'e özel) **değişmez**.
   AUC rank tabanlı olduğundan ağırlıkla hesaplanamaz; yeni yardımcı öğrenci indekslerini gerçekten yeniden örnekler
   (2000 x ~816 öğrenci, döngü yeterli) ve istatistik fonksiyonu alır. Test: macro F1 için eski fonksiyonla yaklaşık
   aynı GA (aynı seed'de birebir beklenmez, örnekleme biçimi farklı).
   `evaluation`'a "var olan test CSV'sinin üzerine yazma" koruması eklenir (küçük değişiklik, testle).
3. **`src/final_metrics.py`** (yeni; adı `test_*` ile başlamasın, `unittest discover` ile karışmasın): yukarıdaki 1–6
   için fonksiyonlar, CLI `PY -m src.final_metrics` → `{output}/test_metrikleri/` altında CSV'ler (`ayirt_edicilik.csv`,
   `norm_aktarimi.csv`, `alt_gruplar.csv`, `hata_yonu.csv`, `alt_5.csv`) ve bir özet JSON (model adı, norm sürümü,
   tarih; hash). Cinsiyet yalnız değerlendirme alt grubu olarak kullanılır; norm, skor ya da rapor girdisi değildir.
4. **Birim testleri** (`tests/test_final_metrics.py`, sentetik tahminlerle): AUC bilinen küçük örnekle; `d > 0`
   oranı; norm aktarımı oranları (norm = test ise tam beklenen oranlar); bootstrap'ın F1 için eski fonksiyonla
   benzer GA; test CSV'si yokken anlaşılır hata; `evaluation` korumasının var olan test CSV'sini ezmemesi;
   `LIMITATIONS`'ta eski "448px, %33,7" ifadesinin kalmaması.
5. **Belgeleme:** `docs/olcumler.md` "Model tabanlı ölçümler" bölümüne "Bu ölçümün doğruluğu" alt başlığı (val vs
   test AUC, norm aktarımı, alt gruplar, hata yönü, alt %5 sıklığı, iyimserlik payı yorumu, sınırlamalar);
   `docs/kararlar.md`'ye test setinin kullanıldığı tarih ve "bir daha bakılmaz" kaydı; `docs/rapor_taslagi.md`
   görev uyumu satırına doğruluk cümlesi; `LIMITATIONS` güncellemesi (4).
6. **Doğrulama:** dogrulayici → `docs/dogrulama/<tarih>-gorev-uyumu-adim6.md`. Özellikle: test CSV'sinin tek
   çalıştırmadan geldiği, hiçbir norm/eşik/tanımın değişmediği (`git diff` ile `task_fit.py` norm kodu, `analysis`
   eşiği), GA'ların öğrenci bazlı olduğu. Aşama sonunda denetleyici.
7. **Kapanış:** commit ve push; `durum.md`, `plan.md` güncellenir.

## Kapsam dışı
- Sınıf düzeyi tahmini; yeni model, kalibrasyon (üst planda ayrı kalem değil), eşik ya da norm değişikliği; test
  üzerinde ayar.
- Test sonucuna göre rapor kuralı (⚠, norm grubu) değiştirmek. Böyle bir ihtiyaç çıkarsa ayrı karar olarak
  kullanıcıya gider ve test setinin bu amaçla kullanıldığı kaydedilir (artık bağımsız değil).

## Kararlar (kullanıcı, 2026-11-10)
- Norm aktarımı eşiği ±5 puan: makul. Çalıştırma yerelde (Drive'a yazar; Colab'la aynı anda değil).
