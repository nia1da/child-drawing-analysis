import os
import zipfile
from functools import partial
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from .config import YOLLAR

KOK = YOLLAR["kok"]
ETIKET = {"Happiness": 0, "Sadness": 1}
ORT, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
KIDO_GDRIVE_ID = "1Ip5HI3kqnZ0Lpc0jQKxl30IjHmksqkrf"  # açık KIDO veri seti


def veri_hazirla(kok=KOK, zip_yolu=YOLLAR["zip"]):
    # Görseller yoksa KIDO zip'ini açar; zip de yoksa önce bir kez indirir (Colab'da Drive'a kaydolur).
    # Zip içi Dataset/... ile başlar, bu yüzden kok'un iki üstüne açılır.
    if os.path.isdir(kok):
        return
    if not os.path.exists(zip_yolu):
        import gdown
        print(f"{zip_yolu} yok; KIDO indiriliyor (bir kez)...")
        os.makedirs(os.path.dirname(zip_yolu), exist_ok=True)
        gdown.download(id=KIDO_GDRIVE_ID, output=f"{zip_yolu}.part", quiet=False)
        os.replace(f"{zip_yolu}.part", zip_yolu)  # yarım kalan indirme zip gibi görünmesin
    hedef = Path(kok).parents[1]
    print(f"{zip_yolu} -> {hedef} açılıyor...")
    with zipfile.ZipFile(zip_yolu) as z:
        z.extractall(hedef)


def resimleri_topla(kategori, kok=KOK):
    kayitlar = {}  # dosya_adi -> (split, etiket)
    for split in ["train", "test"]:
        for etiket in os.listdir(f"{kok}/{kategori}/{split}"):
            for dosya in os.listdir(f"{kok}/{kategori}/{split}/{etiket}"):
                kayitlar[dosya] = (split, etiket)
    return kayitlar


def metadata_olustur(kok=KOK):
    """Emotion/Gender/Education klasörlerinden tek bir metadata tablosu kurar."""
    duygu = resimleri_topla("Emotion", kok)
    cinsiyet = resimleri_topla("Gender", kok)
    egitim = resimleri_topla("Education", kok)

    satirlar = []
    for dosya in duygu:
        parca = dosya.replace(".jpg", "").split("-")
        satirlar.append({
            "dosya": dosya,
            "split": duygu[dosya][0],
            "duygu": duygu[dosya][1],
            "cinsiyet": cinsiyet[dosya][1],
            "egitim": egitim[dosya][1],
            "ogrenci": "-".join(parca[:3]),  # okul-sınıf-no
        })
    return pd.DataFrame(satirlar)


def metadata_yukle(yol=YOLLAR["metadata"]):
    return pd.read_csv(yol)


def resim_yolu(s, kok=KOK):
    return f"{kok}/Emotion/{s.split}/{s.duygu}/{s.dosya}"


class KidoDataset(Dataset):
    def __init__(self, tablo, tf, kok=KOK):
        self.tablo, self.tf, self.kok = tablo.reset_index(drop=True), tf, kok

    def __len__(self):
        return len(self.tablo)

    def __getitem__(self, i):
        s = self.tablo.iloc[i]
        return self.tf(Image.open(resim_yolu(s, self.kok))), ETIKET[s.duygu]


def kareye_pad(img, boyut):
    # Oranı koruyarak boyut x boyut'a sığdırır, boşlukları beyazla doldurur
    return ImageOps.pad(img.convert("RGB"), (boyut, boyut), color="white")


def donusumler(boyut=224):
    # lambda yerine partial: macOS'ta DataLoader worker'ları spawn ile açıldığı için pickle edilebilmeli
    pad = partial(kareye_pad, boyut=boyut)
    e_tf = transforms.Compose([transforms.Lambda(pad), transforms.RandomHorizontalFlip(),
                               transforms.RandomRotation(5, fill=255), transforms.ToTensor(), transforms.Normalize(ORT, STD)])
    d_tf = transforms.Compose([transforms.Lambda(pad), transforms.ToTensor(), transforms.Normalize(ORT, STD)])
    return e_tf, d_tf


def yukleyiciler(df, boyut=224, kok=KOK, num_workers=2, batch=32):
    e_tf, d_tf = donusumler(boyut)
    tr = DataLoader(KidoDataset(df[df.bolum == "train"], e_tf, kok), batch_size=batch, shuffle=True, num_workers=num_workers)
    va = DataLoader(KidoDataset(df[df.bolum == "val"], d_tf, kok), batch_size=batch * 2, num_workers=num_workers)
    return tr, va
