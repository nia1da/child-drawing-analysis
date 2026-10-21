# Çizim Analiz: çocuk çizimleri için uzman karar desteği

Bitirme projesi. Çocuk ve ergen psikiyatrisi uzmanına, çocuğun çiziminden **betimleyici bir ön-analiz raporu**
sunan bir karar destek sistemi. Sistem tanı koymaz ve risk skoru üretmez. Çizimi ölçer ve aynı sınıf düzeyindeki
akranlarıyla karşılaştırır ("akranlarının X. yüzdelik diliminde"); yorum uzmana kalır.

Şu an sadece **Çizim** modülü var (Yazı ve Konuşma modülleri planlı). Veri: KIDO veri seti,
Şanlıurfa'da 1–8. sınıf öğrencilerinin "mutlu" ve "üzgün" görevlerine çizdiği resimler (her öğrenciden iki çizim).
Gerçek klinik veri bu repoya girmez; veri ve model dosyaları git'te değil, Google Drive'dadır.

## Ne üretir

`python -m src.report <çizim>` bir çizim için JSON ve metin rapor yazar:

```
Çizim ölçümleri: 110-3H-1081-F-S.jpg
Karşılaştırma grubu: 3. sınıf, "üzgün" görevi (KIDO train, 696 çizim)

  Doluluk oranı             0,003   akranlarının 1. yüzdelik diliminin altında  ⚠
  Farklı renk sayısı            0   akranlarının 1. yüzdelik diliminin altında  *
  ...
```

- **Ölçümler** klasik görüntü işlemeyle (makine öğrenmesi yok): kompozisyon (doluluk, ağırlık merkezi, kapsayan
  kutu, bölge dolulukları), renk (renk sayısı, doygunluk, koyu ton, sıcak ton payı, renklilik, boyama), çizgi ve
  yapı (kenar yoğunluğu, çizgi uzunluğu ve kalınlığı, bileşen sayısı). Normlar KIDO train bölümünden, sınıf düzeyi
  x görev bazında.
- **⚠** akranların %5'inden azı bu kadar uç bir değere sahipse; **\*** çizim çok küçük olduğu için güvenilir
  olmayan ölçümler.
- Bir **duygu sınıflandırıcısı** (ConvNeXt-Tiny, val macro F1 0,81) "görev uyumu" ve "mutlu–üzgün ayrışma" için
  kullanılacak (geliştiriliyor). Çocuğun ruh hali olarak yorumlanmaz.

## Klasör yapısı

```
src/                  kod
  config.py           ortam algılama (yerel / Colab), yollar (PATHS), eğitim varsayılanları
  data.py             KIDO'yu açma, metadata, veri kümesi ve dönüşümler
  splits.py           öğrenci bazında train / val / test bölmesi
  training.py         sınıflandırıcı eğitimi (resnet50, efficientnet_b0, convnext_tiny)
  evaluation.py       kayıtlı modeli bir bölümde değerlendirme, alt grup F1'leri, tahmin dosyaları
  stats.py            öğrenci bazlı bootstrap güven aralıkları
  analysis.py         güven bandı, hata yönü, deney karşılaştırması
  migrate_experiments.py  deneyler.csv'nin sütun düzeni ve satır ekleme
  report.py           çizim raporu (JSON + metin)
  measurements/       çizim maskesi (mask.py), ölçümler (metrics.py), normlar (norms.py),
                      maske kontrol sayfası (mask_check.py)
tests/                unittest testleri (sentetik veriyle, KIDO gerekmez)
notebooks/            colab.ipynb (güncel; sadece src/ fonksiyonlarını çağırır), grad_proj.ipynb (arşiv)
docs/                 belgeler (aşağıda)
data/                 yerel veri (git'te değil)
```

## Belgeler (`docs/`)

| Dosya | İçerik |
|---|---|
| `durum.md` | Şu anki aşama, son biten iş, sıradaki adım, açık sorular. Başlamak için ilk okunacak dosya. |
| `plan.md` | Aşamalar (0–8), her birinin bitme ölçütü ve durumu. |
| `kararlar.md` | Verilmiş kararlar: tarih, karar, gerekçe. |
| `rapor_taslagi.md` | Hedef rapor (uydurma değerlerle örnek). |
| `olcumler.md` | Ölçümlerin tanımları, maske sınırlamaları, norm ve kalite kuralları. |
| `plan_<konu>.md` | Büyük işlerin ayrıntılı planları (örn. `plan_gorev_uyumu.md`). |
| `dogrulama/` | Her işten sonra yazılan doğrulama raporları. |

Proje kuralları ve çalışma ortamı ayrıntıları: `CLAUDE.md`.

## Kurulum

Python sanal ortamı `.venv/`. Aşağıda `PY` yerine Mac'te `.venv/bin/python`, Windows'ta `.venv\Scripts\python`.

```sh
# Mac
python3.11 -m venv .venv
PY -m pip install -r requirements.txt

# Windows (NVIDIA GPU): önce CUDA'lı torch, sonra geri kalanlar
py -3.12 -m venv .venv
PY -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
PY -m pip install -r requirements.txt
```

Veri: `PY -c "from src.data import prepare_data; prepare_data()"` KIDO zip'ini `data/kido/` altına açar. Çıktılar
(modeller, `deneyler.csv`, normlar, raporlar) Google Drive'daki `bitirme` klasörüne gider (yerelde Google Drive for
desktop; `CIZIM_DRIVE` ile verilebilir). Drive bulunamazsa `data/ciktilar/` kullanılır.

## Temel komutlar

```sh
# Testler
PY -m unittest discover -s tests -t .

# Çizim raporu (JSON + metin, Drive raporlar/)
PY -m src.report data/kido/Dataset/Images/Emotion/train/Sadness/110-3H-1081-F-S.jpg
PY -m src.report <çizim.jpg> --grade 3 --task mutlu        # KIDO dışı dosya adı için

# Ölçüm normlarını yeniden hesapla (train, birkaç dakika)
PY -m src.measurements.norms

# Eğitim: önce hızlı deneme (kayıt yazmaz), sonra tam eğitim (asıl eğitimler Colab'da)
PY -m src.training --model convnext_tiny --size 320 --quick
PY -m src.training --model convnext_tiny --size 320 --epochs 12

# Kayıtlı modeli değerlendirme (varsayılan bölüm test; seçim için --split val)
PY -m src.evaluation --experiment convnext_tiny_320px_lr0.0001_ls0.1_s42 --split val
```

Eğitimler Colab'da (T4) `notebooks/colab.ipynb` ile yapılır; notebook repoyu `git pull` ile çeker.
