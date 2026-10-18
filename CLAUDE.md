# Çizim Analiz — Çocuk çizimlerinden duygu sınıflandırma

## Proje
- KIDO veri setiyle (açık, etiketli) çocuk çizimlerinden duygu sınıflandırma: Happiness / Sadness.
- Uzun vadede uzmana ön-analiz sunan bir karar destek sistemi; Çizim, Yazı, Konuşma ayrı modüller.
  Şu an sadece **Çizim** modülü. Sistem tanı koymaz, sadece uzmana destek sunar.
- Modüller bağımsız çalışır; birleşik "risk skoru" üretilmez.
- Gerçek klinik çocuk verisi asla bu repoya girmez.

## Çalışma ortamı
- Kod yerelde (Mac) yazılır ve test edilir; eğitim Colab'da (T4) yapılır.
- Colab repoyu `git pull` ile çeker. Notebook sadece `src/` fonksiyonlarını çağırıp sonuç gösterir,
  notebook'a mantık kodu yazılmaz.
- Veri ve modeller git'e girmez (`.gitignore`: `data/`, `kido/`, `*.pt`, `*.pth`).
  Drive kökü: `/content/drive/MyDrive/bitirme/` (metadata CSV, `.pt` dosyaları, `deneyler.csv`, KIDO zip'i).
- Colab'da KIDO zip'i (`bitirme/kido_dataset`) `veri.veri_hazirla()` ile `/content/kido` altına açılır; görseller Drive'dan doğrudan okunmaz (yavaş).
- Yollar `src/config.py`'deki `YOLLAR`'dan alınır; kodda ve notebook'ta sabit yol yazma.
  Ortam `COLAB_RELEASE_TAG` ile algılanır, `CIZIM_ORTAM=yerel|colab` ile zorlanabilir.
  Yerelde: `data/kido/Dataset/Images`, `data/kido_metadata.csv`, `data/ciktilar/`.
- Cihaz otomatik (`egitim.cihaz_sec`): CUDA > MPS > CPU. float16 AMP sadece CUDA'da.
- macOS'ta DataLoader worker'ları spawn ile açılır: dönüşümlerde lambda kullanma (pickle edilemez), modül düzeyi fonksiyon + `partial` kullan.
  Aynı sebeple DataLoader kullanan betikler stdin'den değil dosyadan, `if __name__ == "__main__":` altında çalıştırılmalı.

## Yerel kurulum ve komutlar
- Sanal ortam: `.venv/` (Python 3.11). Her komut `.venv/bin/python` ile çalışır.
- `requirements.txt` Colab runtime sürümlerine sabitli (Colab: Python 3.13, torch 2.11.0, torchvision 0.26.0).
  Colab sürümleri değişirse güncelle: github.com/googlecolab/backend-info `pip-freeze.txt`.
- Veri: `data/kido_dataset` (zip) → `data/kido/`. `data/kido_metadata.csv` klasörlerden
  `stratifiye_bol(metadata_olustur())` ile üretildi; bölüm sayıları Colab çıktısıyla aynı.
- Hızlı test: `.venv/bin/python -m src.egitim --model convnext_tiny --boyut 320 --hizli`,
  `.venv/bin/python -m src.degerlendir --deney convnext_tiny_448px_lr0.0001_ls0.1_s42 --hizli`

## Kod yapısı
- `src/config.py`: ortam algılama ve `YOLLAR` (`kok`, `zip`, `metadata`, `cikti`).
- `src/veri.py`: `veri_hazirla` (zip'i açar), metadata tablosu, `KidoDataset`, dönüşümler (beyaz pad ile kare;
  `aug`: `temel` = çevirme + döndürme, `renk` = + renk bozma, gri tonlama), `yukleyiciler`.
- `src/bolme.py`: `stratifiye_bol` → `bolum` sütunu (train/val/test).
- `src/egitim.py`: `cihaz_sec`, `model_kur` (resnet50, efficientnet_b0, convnext_tiny), `egit`; `python -m src.egitim` CLI'ı.
- `src/degerlendir.py`: `.pt`'yi bir bölümde (varsayılan test) değerlendirir: macro F1, karışıklık matrisi,
  cinsiyet / eğitim / ikisinin kesişimi alt grup F1'leri; tahminleri `{cikti}/tahminler/{deney}_{bolum}.csv`'ye yazar.
  `python -m src.degerlendir --deney <ad> [--hizli]`.
- `src/istatistik.py`: alt grup macro F1'leri ve grup farkları için öğrenci bazlı bootstrap %95 GA
  (`guven_araliklari(kayitli_tahminler(deney))`). Çizim değil öğrenci yeniden örneklenir (aynı öğrencinin çizimleri bağımlı).
- `src/analiz.py`: kayıtlı tahminler üzerinde güven bandı (`esik_kaydet`/`esik_yukle`/`guven_bandi`; eşik val'de,
  `{deney}_esik.json`), `hata_yonu` (mutlu→üzgün / üzgün→mutlu, alt grup) ve `karsilastir` (seed ortalamalı ayar kıyası).
- `src/deneyler_tasi.py`: `deneyler.csv`'yi güncel düzene taşır (ilk 4 sütunlu düzen ya da eksik yeni sütunlar).
- `notebooks/colab.ipynb`: güncel Colab notebook'u; repoyu clone/pull eder, sadece `src/` fonksiyonlarını çağırır.
- `notebooks/grad_proj.ipynb`: arşiv (ilk keşif ve denemeler). Çıktıları eski sonuçların kaynağı, silinmemeli.
- KIDO yapısı: `Dataset/Images/{Emotion,Gender,Education}/{train,test}/<sınıf>/`, `Dataset/Texts/` aynı düzende.
  Etiketler klasör adlarından okunur. Dosya adı: `okul-sınıf-no-<cinsiyet harfi>-<duygu harfi>.jpg`;
  ilk üç parça öğrenci kimliği (`ogrenci`).

## Alınmış kararlar (kullanıcıya sormadan değiştirme)
- Test seti: KIDO'nun resmi `test` klasörü. Val: train'den **öğrenci bazında** %15,
  eğitim seviyesi + cinsiyete göre stratifiye, seed 42. Aynı öğrencinin çizimleri tek bölümde kalır.
- Baseline hedef: makaledeki görüntü modeli ≈ %79 F1. Metrik: macro F1.
- Çözünürlük önemli: 320px, 224px'ten ≈ 3 puan daha iyi.

## Bilinen sonuçlar (2026-10-15)
- En iyi: convnext_tiny 448px, 8 epoch, lr 1e-4, ls 0.1. Val F1 3 seed'de 0.825 ± 0.003 (s42 0.828, s1 0.823, s2 0.823);
  s42 test F1 0.830. resnet50 448px test 0.794. En iyi epoch genelde 3–5.
- Seed'ler arası yayılım ≈ 0.5 puan: 1 puanın altındaki farkları tek seed'le yorumlama, 2–3 seed ile tekrarla.
- Test setine sadece nihai kıyaslama/raporlama için bak; seçim val ile yapılır.
- Alt gruplar (s42, test): erkeklerde F1 belirgin düşük (Female 0.853, Male 0.795; ilkokul erkek 0.765).
- Testte her öğrencinin tam 2 çizimi var (biri mutlu, biri üzgün).
- Hata analizi (s42, test): ilkokul erkek hatası tek yönlü, mutlu çizimlerin %33.7'si "üzgün" (diğer gruplar %11–19).
  Seyrek/az renkli mutlu çizimler etkili ama aynı renklilikte de fark sürüyor. Bootstrap: ilkokul kız−erkek farkı anlamlı,
  ortaokulda değil. Model güveni anlamlı: güven <0.5 → %64, ≥0.8 → %92–97 doğruluk.
- Gruba özel (cinsiyete göre) eşik kullanılmaz: model girdisi olarak cinsiyet gerektirir, etik açıdan sorunlu.

## Çalışma kuralları
- Değişken, fonksiyon ve yorumlar **Türkçe** (`egit`, `boyut`, `kayip_fn` gibi).
- Git işlemlerini (commit, branch, push) kullanıcı yapar. Claude sadece kodu düzenler,
  değişiklikleri küçük ve anlamlı parçalar halinde tutar ve neyin değiştiğini özetler.
- Eğitim kodunda değişiklik yapınca Colab'a göndermeden önce `--hizli` (`egit(..., hizli=True)`) ile yerelde test et:
  bölüm başına her sınıftan 8 görsel, 1 epoch, batch 4. Hızlı mod model kaydetmez ve `deneyler.csv`'ye yazmaz;
  gerçek sonuçlar sadece Colab'daki tam eğitimlerden gelir.
- Her deneme Drive'daki `deneyler.csv`'ye bir satır ekler. Sütunlar:
  `tarih, deney, model, boyut, lr, smoothing, seed, augmentation, toplam_epoch, en_iyi_epoch, en_iyi_val_f1, dakika, not`
  - Yeni bir hiperparametre değiştirilmeye başlanırsa (batch size vb.) o da sütun olarak eklenmeli: `SUTUNLAR`'a ekle,
    önceki deneylerdeki değerini `EKLENEN_SUTUNLAR`'a yaz; `deneyler_tasi` mevcut dosyayı yedekleyip sütunu doldurur.
    Varsayılan değer deney adına eklenmez (eski adlar değişmesin), farklı değer sona ek olarak gelir (`..._s42_aug-renk`).
  - Eski satırlar silinmez; şemaya taşınırken bilinmeyen alanlar boş bırakılır, `not` = "eski kayıt".
  - Sütunlar `egitim.SUTUNLAR`'da. `egit()` başlığı farklı bir dosyaya yazmayı eğitimden önce reddeder.
- Deney adı (`egitim.deney_adi`) benzersizdir ve hem `.pt` dosya adı hem `deney` sütunudur:
  `convnext_tiny_320_ep12_lr1e-4_ls0.1_s42`. Aynı ad `.pt` olarak ya da `deneyler.csv`'de varsa `egit()` eğitimden önce hata verir.
  Eski satırlar eski adları (`..._320px_lr0.0001_ls0.1_s42`) korur; mevcut `.pt` dosyalarının adı değiştirilmez.
- Eski düzendeki `deneyler.csv` `python -m src.deneyler_tasi` ile taşınır (orijinal `deneyler_eski.csv` olarak saklanır).
