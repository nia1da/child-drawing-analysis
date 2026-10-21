# Çizim Analiz — Çocuk çizimleri için uzman karar desteği

## Proje
- Bitirme projesi: çocuk ve ergen psikiyatrisi uzmanına ön-analiz sunan bir karar destek sistemi.
  Çizim, Yazı, Konuşma ayrı ve bağımsız modüller; şu an sadece **Çizim** modülü.
- Sistem tanı koymaz, risk skoru üretmez (modüller arası birleşik skor da yok). Çocuğun çizimini betimler ve
  akranlarıyla karşılaştırır; yorum uzmana kalır.
- Çizim modülünün asıl çıktısı yorumlanabilir ölçümler:
  - Kompozisyon: doluluk, ağırlık merkezi, kapsayan kutu, çeyrek dağılımı
  - Renk: renk sayısı, doygunluk, koyu ton, sıcak/soğuk oranı, renklilik
  - Çizgi/yapı: kenar yoğunluğu, çizgi uzunluğu ve kalınlığı, bileşen sayısı

  Ölçümler KIDO üzerinden sınıf düzeyine ve göreve (mutlu/üzgün) göre normlara bağlanır; raporda
  "akranlarının X. yüzdelik diliminde" diye sunulur.
- Duygu sınıflandırıcısı (KIDO, Happiness / Sadness) sistemin bir parçası: çizimin tipik mutlu/üzgün çizimlere
  benzerliğini ölçen **görev uyumu** ve aynı çocuğun iki çizimini karşılaştıran **mutlu–üzgün ayrışma** için kullanılır.
  Çocuğun ruh hali olarak yorumlanmaz.
- Gerçek klinik çocuk verisi asla bu repoya girmez.

## Çalışma ortamı
- Kod yerelde (Mac ya da Windows) yazılır ve test edilir; eğitim Colab'da (T4) yapılır.
  Windows makinede RTX 4060 (8 GB) var: CUDA'lı torch kurulu, kısa denemeler yerelde de koşabilir.
- Colab repoyu `git pull` ile çeker. Notebook sadece `src/` fonksiyonlarını çağırıp sonuç gösterir,
  notebook'a mantık kodu yazılmaz.
- Veri ve modeller git'e girmez (`.gitignore`: `data/`, `kido/`, `*.pt`, `*.pth`).
  Drive kökü: `/content/drive/MyDrive/bitirme/` (metadata CSV, `.pt` dosyaları, `deneyler.csv`, KIDO zip'i).
- Colab'da KIDO zip'i (`bitirme/kido_dataset`) `data.prepare_data()` ile `/content/kido` altına açılır; görseller Drive'dan doğrudan okunmaz (yavaş).
- Yollar `src/config.py`'deki `PATHS`'ten alınır; kodda ve notebook'ta sabit yol yazma.
  Ortam `COLAB_RELEASE_TAG` ile algılanır, `CIZIM_ENV=local|colab` ile zorlanabilir.
  Yerelde görseller ve metadata: `data/kido/Dataset/Images`, `data/kido_metadata.csv`.
- Çıktılar (`.pt`, `deneyler.csv`, `tahminler/`) iki ortamda da Drive'daki `bitirme` klasörüne gider: yerel ve Colab
  aynı `deneyler.csv`'ye yazar. Yerelde Google Drive for desktop üzerinden (Windows makinede `H:/My Drive/bitirme`);
  `CIZIM_DRIVE` ile verilir, yoksa sürücü harfleri / macOS `~/Library/CloudStorage/GoogleDrive-*` aranır
  ("My Drive" ya da "Drive'ım"). Bulunamazsa uyarı verip `data/ciktilar/`'a düşer (o zaman ortak kayda gitmez).
  Colab ve yerelde aynı anda eğitim yapma: aynı dosyaya iki yerden yazmak Drive'da çakışma kopyası üretebilir.
- Cihaz otomatik (`training.select_device`): CUDA > MPS > CPU. float16 AMP sadece CUDA'da.
- Eğitim varsayılanları ortama göre (`config.TRAINING_DEFAULTS`): Colab batch 32, accum 1; yerel batch 16, accum 2,
  2 worker. RTX 4060'ta 448px batch 32 belleğe sığmıyor (ölçüm 2026-10-19: batch 16, convnext_tiny 448px,
  1 epoch 2,7 dk, max_reserved 4,96 GB; 4 ve 6 worker daha yavaş). NVIDIA ayarlarında sysmem fallback kapalı:
  bellek yetmezse yavaşlamak yerine OOM verir.
- Gradyan biriktirme (`training.train_epoch`) etkin batch'i korur, ama BatchNorm'lu modellerde (resnet50, efficientnet_b0)
  16 x 2, 32 x 1'e eşdeğer değildir (BN istatistikleri micro-batch'ten); convnext_tiny LayerNorm kullanır, eşdeğer.
- macOS ve Windows'ta DataLoader worker'ları spawn ile açılır: dönüşümlerde lambda kullanma (pickle edilemez), modül düzeyi fonksiyon + `partial` kullan.
  Aynı sebeple DataLoader kullanan betikler stdin'den değil dosyadan, `if __name__ == "__main__":` altında çalıştırılmalı.
- Satır sonları `.gitattributes` ile LF (`* text=auto eol=lf`); iki işletim sisteminde aynı kalır.

## Yerel kurulum ve komutlar
- Sanal ortam: `.venv/` (Mac: Python 3.11, Windows: Python 3.12). Komutlardaki `PY` yerine:
  - Mac: `.venv/bin/python`
  - Windows: `.venv\Scripts\python` (PowerShell) ya da `.venv/Scripts/python` (Git Bash)
- Kurulum:
  - Mac: `python3.11 -m venv .venv` → `PY -m pip install -r requirements.txt`
  - Windows (NVIDIA GPU): `py -3.12 -m venv .venv` → önce CUDA'lı torch:
    `PY -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128`,
    sonra `PY -m pip install -r requirements.txt` (sürüm aynı olduğu için CUDA'lı torch korunur).
- `requirements.txt` Colab runtime sürümlerine sabitli (Colab: Python 3.13, torch 2.11.0, torchvision 0.26.0).
  Colab sürümleri değişirse güncelle: github.com/googlecolab/backend-info `pip-freeze.txt`.
  `tzdata`: Windows'ta `zoneinfo` saat dilimi verisi için gerekli. `scipy`, `scikit-image`: ölçümler (Canny, iskelet).
- Veri: `PY -c "from src.data import prepare_data; prepare_data()"` zip'i indirir (`data/kido_dataset`) ve `data/kido/`'ya açar.
  `data/kido_metadata.csv` klasörlerden `stratified_split(build_metadata())` ile üretilir; bölüm sayıları
  (train 7842, val 1386, test 1632) Colab çıktısıyla aynı.
- Testler: `PY -m unittest discover -s tests -t .` (sentetik veriyle, KIDO gerekmez).
- Hızlı test: `PY -m src.training --model convnext_tiny --size 320 --quick`,
  `PY -m src.evaluation --experiment convnext_tiny_448px_lr0.0001_ls0.1_s42 --quick`
- Çizim raporu: `PY -m src.report data/kido/Dataset/Images/Emotion/test/Sadness/205-7G-940-M-S.jpg`
  (JSON + metin, Drive `raporlar/`). Normlar: `PY -m src.measurements.norms` (train, birkaç dakika).
  Maske kontrol sayfası: `PY -m src.measurements.mask_check`.
- Dosyalar her zaman `encoding="utf-8"` ile açılır (Windows'un varsayılanı cp1254).

## Kod yapısı
- `src/config.py`: ortam algılama, `PATHS` (`root`, `zip`, `metadata`, `output`), yerel Drive'ı bulma
  (`find_local_drive`), ortama göre eğitim varsayılanları (`DEFAULTS`).
- `src/data.py`: `prepare_data` (zip'i açar), metadata tablosu (`build_metadata`, `load_metadata`; `sinif` dosya
  adından hesaplanır, kayıtlı CSV'de yok: `grade_from_filename`, `task_from_filename`), `KidoDataset`,
  dönüşümler (`build_transforms`: beyaz pad ile kare; `aug`: `temel` = çevirme + döndürme, `renk` = + renk bozma,
  gri tonlama), `build_loaders`.
- `src/splits.py`: `stratified_split` → `bolum` sütunu (train/val/test).
- `src/training.py`: `select_device`, `build_model` (resnet50, efficientnet_b0, convnext_tiny), `train_epoch`
  (gradyan biriktirme), `train`; `python -m src.training` CLI'ı (`--batch-size`, `--accum-steps`, `--num-workers`).
- `src/evaluation.py`: `.pt`'yi bir bölümde (varsayılan test) değerlendirir: macro F1, karışıklık matrisi,
  cinsiyet / eğitim / ikisinin kesişimi alt grup F1'leri; tahminleri `{output}/tahminler/{deney}_{bolum}.csv`'ye yazar.
  `python -m src.evaluation --experiment <ad> [--split val] [--quick]`.
- `src/stats.py`: alt grup macro F1'leri ve grup farkları için öğrenci bazlı bootstrap %95 GA
  (`confidence_intervals(load_predictions(deney))`). Çizim değil öğrenci yeniden örneklenir (aynı öğrencinin çizimleri bağımlı).
  (`statistics.py` değil: standart kütüphanedeki `statistics` ile çakışır.)
- `src/analysis.py`: kayıtlı tahminler üzerinde güven bandı (`save_threshold`/`load_threshold`/`confidence_band`;
  eşik val'de, `{deney}_esik.json`), `error_direction` (mutlu→üzgün / üzgün→mutlu, alt grup) ve `compare`
  (seed ortalamalı ayar kıyası).
- `src/migrate_experiments.py`: `deneyler.csv`'nin sütun düzeni (`COLUMNS`, `ADDED_COLUMNS`), eski düzenlerden taşıma
  (ilk 4 sütunlu düzen ya da eksik yeni sütunlar) ve satır ekleme (`append_record`).
- `tests/`: `unittest` testleri (`test_splits.py`: aynı öğrenci iki bölümde olmamalı; `test_accumulation.py`:
  16 x 2 ile 32 x 1 aynı ağırlık güncellemesini veriyor mu, epoch sonundaki yarım grup dahil; SGD ile, çünkü Adam'ın
  ilk adımı gradyan ölçeğinden bağımsız ve hatayı gizler; `test_results_file.py`: eski düzen yedeklenip taşınıyor mu,
  tanınmayan düzende hiçbir şey yazılmıyor mu; `test_measurements.py`: maske, ölçümler, soluk renk bayrağı,
  yüzdelik ve rapor, sentetik görüntülerle).
- `src/measurements/`: çizim ölçümleri, ayrıntılar ve maske sınırlamaları `docs/olcumler.md`'de.
  `mask.py` (çizim maskesi, soluk renk bayrağı), `metrics.py` (tablodaki bütün ölçümler, `MEASURES`;
  `MEASUREMENT_VERSION`),
  `norms.py` (train normları, yüzdelik, kuyruk payları), `mask_check.py` (24 çizimlik görsel kontrol sayfası).
- `src/report.py`: bir çizim için betimleyici rapor (JSON + metin); JSON'da bütün ölçümler, metinde sadece
  `TEXT_MEASURES` (doluluk, renk sayısı, renklilik, koyu ton, detay = kenar yoğunluğu; son ikisi çizim pikselleriyle).
  ⚠ akranların %5'inden azı bu kadar uçtaysa; grup 100'den küçükse (`MIN_GROUP`) ⚠ yerine "grup küçük" notu.
- `notebooks/colab.ipynb`: güncel Colab notebook'u; repoyu clone/pull eder, sadece `src/` fonksiyonlarını çağırır.
- `notebooks/grad_proj.ipynb`: arşiv (ilk keşif ve denemeler). Çıktıları eski sonuçların kaynağı, silinmemeli
  (`migrate_experiments` bu çıktıları okur); import'lar yeni adlara güncellendi, çıktılar olduğu gibi.
- KIDO yapısı: `Dataset/Images/{Emotion,Gender,Education}/{train,test}/<sınıf>/`, `Dataset/Texts/` aynı düzende.
  Etiketler klasör adlarından okunur. Dosya adı: `okul-sınıf-no-<cinsiyet harfi>-<duygu harfi>.jpg`;
  ilk üç parça öğrenci kimliği (`ogrenci`).

## Alınmış kararlar (kullanıcıya sormadan değiştirme)
- Test seti: KIDO'nun resmi `test` klasörü. Val: train'den **öğrenci bazında** %15,
  eğitim seviyesi + cinsiyete göre stratifiye, seed 42. Aynı öğrencinin çizimleri tek bölümde kalır.
- Baseline hedef: makaledeki görüntü modeli ≈ %79 F1. Metrik: macro F1.
- Çözünürlük önemli: 320px, 224px'ten ≈ 3 puan daha iyi.
- **Duygu sınıflandırıcısı donduruldu (2026-10-19).** Yeni sınıflandırıcı denemesi yapılmaz; model raporda sadece
  "görev uyumu" ve "mutlu–üzgün ayrışma" için kullanılır. Referans model: Drive'daki
  `convnext_tiny_320px_lr0.0001_ls0.1_s42.pt` (val F1 **0.8095**; 12 epoch'luk çalıştırma, en iyi epoch 11).
  `deneyler.csv`'deki 0.811'lik 8 epoch'luk satırın ağırlıkları yok: eski adlar epoch içermediği için sonraki
  12 epoch'luk çalıştırma aynı `.pt`'nin üzerine yazdı (val'de yeniden değerlendirilerek doğrulandı).
- Aynı anda hem yerelde hem Colab'da eğitim çalıştırılmaz: ikisi de Drive'daki aynı `deneyler.csv`'ye yazar, çakışır.
- Sınıf düzeyi (1–8) dosya adının 2. parçasının rakamından çıkarılır (`101-3B-...` → 3; harf şube).
  1–4 Primary, 5–8 Secondary ile birebir tutarlı. Normlar sınıf düzeyi × görev (mutlu/üzgün) bazında, sadece
  train bölümünden çıkarılır; val ve test norma girmez.

## Ölçüm modülü ("ince dilim", ilk dilim 2026-10-19'da tamam)
- Amaç: tek komutla herhangi bir KIDO çiziminden betimleyici rapor (ölçümler + akran yüzdelikleri). Makine öğrenmesi yok,
  sadece görüntü işleme. Ölçüm listesi, tanımlar ve maske sınırlamaları: `docs/olcumler.md`.
- İlk dilim: çizim maskesi (kullanıcı 24 çizimlik kontrol sayfasıyla onayladı) + doluluk oranı, farklı renk sayısı,
  koyu ton oranı; train normları (sınıf x görev); soluk renk kalite bayrağı; JSON + metin rapor.
- Rapor betimleyicidir, tanı dili içermez. Bütün çizimleri aynı yönde etkileyen maske hataları kabul (normlar aynı
  maskeyle); bazı çizimleri etkileyenler raporda kalite bayrağıyla görünür olmalı.
- Sürüm 2 (2026-10-19): `docs/olcumler.md` tablosundaki bütün ölçümler JSON'da ve normlarda; metin rapor beş ölçüm.
- Sürüm 3 (2026-10-21): metin rapordaki renklilik (Hasler–Süsstrunk) ve detay (kenar yoğunluğu) çizim piksellerine
  göre (`renklilik_cizim`, `kenar_yogunlugu_cizim`); sayfa tabanlı halleri (`renklilik`, `kenar_yogunlugu`, dolulukla
  Spearman 0,76 / 0,87) JSON'da ve normlarda kalır. Detay boyama oranıyla −0,67, çizgi kalınlığıyla −0,75 ilişkili;
  |0,7|'yi geçerse detay için başka tanım konuşulacaktı (geçmedi, sınırda).
- Maske ya da ölçüm tanımı değişirse `MEASUREMENT_VERSION` artır, normları yeniden hesapla.

## Bilinen sonuçlar (2026-10-15)
- En iyi: convnext_tiny 448px, 8 epoch, lr 1e-4, ls 0.1. Val F1 3 seed'de 0.825 ± 0.003 (s42 0.828, s1 0.823, s2 0.823);
  s42 test F1 0.830. resnet50 448px test 0.794. En iyi epoch genelde 3–5.
- Seed'ler arası yayılım ≈ 0.5 puan: 1 puanın altındaki farkları tek seed'le yorumlama, 2–3 seed ile tekrarla.
- Yerel tekrar (2026-10-19, RTX 4060, 16 x 2): convnext_tiny 320px 8 epoch val F1 0.8022 (ep 6), 8,4 dk. Colab'daki
  aynı seed'li 12 epoch çalıştırmasının 8. epoch'u 0.8036; aynı aralıkta kabul edildi.
- Test setine sadece nihai kıyaslama/raporlama için bak; seçim val ile yapılır.
- Alt gruplar (s42, test): erkeklerde F1 belirgin düşük (Female 0.853, Male 0.795; ilkokul erkek 0.765).
- Testte her öğrencinin tam 2 çizimi var (biri mutlu, biri üzgün).
- Hata analizi (s42, test): ilkokul erkek hatası tek yönlü, mutlu çizimlerin %33.7'si "üzgün" (diğer gruplar %11–19).
  Seyrek/az renkli mutlu çizimler etkili ama aynı renklilikte de fark sürüyor. Bootstrap: ilkokul kız−erkek farkı anlamlı,
  ortaokulda değil. Model güveni anlamlı: güven <0.5 → %64, ≥0.8 → %92–97 doğruluk.
- Gruba özel (cinsiyete göre) eşik kullanılmaz: model girdisi olarak cinsiyet gerektirir, etik açıdan sorunlu.

## Çalışma kuralları
- Kod adları (dosya, fonksiyon, sınıf, değişken, CLI bayrakları) **İngilizce**; yorumlar ve ekrana yazdırılan mesajlar Türkçe olabilir.
- Kayıtlı dosyalardaki adlar **Türkçe kalır**, değiştirilmez (eski kayıtlar bunlara bağlı): `deneyler.csv` sütunları,
  metadata sütunları (`dosya, split, duygu, cinsiyet, egitim, ogrenci, bolum`), tahmin CSV'leri (`gercek, olasilik_uzgun, tahmin`),
  `{deney}_esik.json` anahtarları, deney adı biçimi, aug değerleri (`temel`, `renk`), Drive klasör/dosya adları.
  Koddaki `df.duygu`, `t.gercek` gibi erişimler bu yüzden Türkçe.
- Git işlemlerini (commit, branch, push) kullanıcı yapar. Claude sadece kodu düzenler,
  değişiklikleri küçük ve anlamlı parçalar halinde tutar ve neyin değiştiğini özetler.
- Ölçüm veya norm kodunda bir iş bitince, bana raporlamadan önce dogrulayici subagent'ını çalıştır.
- Yeni bir aşamaya başlamadan önce planı ve bir aşama bitince sonucu denetleyici subagent'ına göster; çıktısını bana
  raporla. Aşamalar `docs/plan.md`, hedef rapor `docs/rapor_taslagi.md`.
- Eğitim kodunda değişiklik yapınca Colab'a göndermeden önce `--quick` (`train(..., quick=True)`) ile yerelde test et:
  bölüm başına her sınıftan 8 görsel, 1 epoch, batch 4 (accum ortam varsayılanı). Hızlı mod model kaydetmez ve `deneyler.csv`'ye yazmaz;
  gerçek sonuçlar sadece Colab'daki tam eğitimlerden gelir.
- Her deneme Drive'daki `deneyler.csv`'ye bir satır ekler. Sütunlar:
  `tarih, deney, model, boyut, lr, smoothing, seed, augmentation, batch, accum_steps, toplam_epoch, en_iyi_epoch, en_iyi_val_f1, dakika, not`
  (`batch`, `accum_steps` 2026-10-19'da eklendi; önceki deneyler 32 ve 1.)
  - Yeni bir hiperparametre değiştirilmeye başlanırsa (batch size vb.) o da sütun olarak eklenmeli: `COLUMNS`'a ekle,
    önceki deneylerdeki değerini `ADDED_COLUMNS`'a yaz; `migrate_experiments` mevcut dosyayı yedekleyip sütunu doldurur.
    Varsayılan değer deney adına eklenmez (eski adlar değişmesin), farklı değer sona ek olarak gelir (`..._s42_aug-renk`).
    Etkin batch (batch x accum) 32 değilse `_eb<n>` eki gelir (`..._s42_aug-renk_eb64`). Yerel 16 x 2 ile Colab 32 x 1
    aynı adı alır; ayrım `batch`/`accum_steps` sütunlarında.
  - Eski satırlar silinmez; şemaya taşınırken bilinmeyen alanlar boş bırakılır, `not` = "eski kayıt".
  - Sütunlar `migrate_experiments.COLUMNS`'ta (`training.COLUMNS` olarak da erişilir). Satır her zaman
    `append_record` ile yazılır: eski düzendeki dosyayı önce yedekleyip taşır, sonra ekler; ortam fark etmez.
    Tanınmayan düzende hiçbir şey yazmadan hata verir; `train()` bunu eğitimden önce de kontrol eder.
- Deney adı (`training.experiment_name`) benzersizdir ve hem `.pt` dosya adı hem `deney` sütunudur:
  `convnext_tiny_320_ep12_lr1e-4_ls0.1_s42`. Aynı ad `.pt` olarak ya da `deneyler.csv`'de varsa `train()` eğitimden önce hata verir.
  Eski satırlar eski adları (`..._320px_lr0.0001_ls0.1_s42`) korur; mevcut `.pt` dosyalarının adı değiştirilmez.
- Eski düzendeki `deneyler.csv` ilk yazmada kendiliğinden taşınır; yazmadan taşımak için `python -m src.migrate_experiments`
  (orijinal `deneyler_eski.csv` ya da `deneyler_yedek_<tarih>.csv` olarak saklanır).
