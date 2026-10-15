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
- `src/veri.py`: `veri_hazirla` (zip'i açar), metadata tablosu, `KidoDataset`, dönüşümler (beyaz pad ile kare), `yukleyiciler`.
- `src/bolme.py`: `stratifiye_bol` → `bolum` sütunu (train/val/test).
- `src/egitim.py`: `cihaz_sec`, `model_kur` (resnet50, efficientnet_b0, convnext_tiny), `egit`; `python -m src.egitim` CLI'ı.
- `src/degerlendir.py`: `.pt`'yi bir bölümde (varsayılan test) değerlendirir: macro F1, karışıklık matrisi,
  cinsiyet / eğitim / ikisinin kesişimi alt grup F1'leri; tahminleri `{cikti}/tahminler/{deney}_{bolum}.csv`'ye yazar.
  `python -m src.degerlendir --deney <ad> [--hizli]`.
- `src/deneyler_tasi.py`: eski `deneyler.csv`'yi 12 sütunlu düzene çeviren tek seferlik betik.
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

## Çalışma kuralları
- Değişken, fonksiyon ve yorumlar **Türkçe** (`egit`, `boyut`, `kayip_fn` gibi).
- Git işlemlerini (commit, branch, push) kullanıcı yapar. Claude sadece kodu düzenler,
  değişiklikleri küçük ve anlamlı parçalar halinde tutar ve neyin değiştiğini özetler.
- Eğitim kodunda değişiklik yapınca Colab'a göndermeden önce `--hizli` (`egit(..., hizli=True)`) ile yerelde test et:
  bölüm başına her sınıftan 8 görsel, 1 epoch, batch 4. Hızlı mod model kaydetmez ve `deneyler.csv`'ye yazmaz;
  gerçek sonuçlar sadece Colab'daki tam eğitimlerden gelir.
- Her deneme Drive'daki `deneyler.csv`'ye bir satır ekler. Sütunlar:
  `tarih, deney, model, boyut, lr, smoothing, seed, toplam_epoch, en_iyi_epoch, en_iyi_val_f1, dakika, not`
  - Yeni bir hiperparametre değiştirilmeye başlanırsa (batch size, augmentation vb.) o da sütun olarak eklenmeli.
  - Eski satırlar silinmez; şemaya taşınırken bilinmeyen alanlar boş bırakılır, `not` = "eski kayıt".
  - Sütunlar `egitim.SUTUNLAR`'da. `egit()` başlığı farklı bir dosyaya yazmayı eğitimden önce reddeder.
- Deney adı (`egitim.deney_adi`) benzersizdir ve hem `.pt` dosya adı hem `deney` sütunudur:
  `convnext_tiny_320_ep12_lr1e-4_ls0.1_s42`. Aynı ad `.pt` olarak ya da `deneyler.csv`'de varsa `egit()` eğitimden önce hata verir.
  Eski satırlar eski adları (`..._320px_lr0.0001_ls0.1_s42`) korur; mevcut `.pt` dosyalarının adı değiştirilmez.
- Eski düzendeki `deneyler.csv` `python -m src.deneyler_tasi` ile taşınır (orijinal `deneyler_eski.csv` olarak saklanır).
