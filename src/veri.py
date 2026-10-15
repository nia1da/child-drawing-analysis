import os

import pandas as pd
from PIL import Image, ImageOps
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

KOK = "kido/Dataset/Images"
ETIKET = {"Happiness": 0, "Sadness": 1}
ORT, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


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


def metadata_yukle(yol):
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


def donusumler(boyut=224):
    # Oranı koruyarak boyut x boyut'a sığdırır, boşlukları beyazla doldurur
    pad = lambda img: ImageOps.pad(img.convert("RGB"), (boyut, boyut), color="white")
    e_tf = transforms.Compose([transforms.Lambda(pad), transforms.RandomHorizontalFlip(),
                               transforms.RandomRotation(5, fill=255), transforms.ToTensor(), transforms.Normalize(ORT, STD)])
    d_tf = transforms.Compose([transforms.Lambda(pad), transforms.ToTensor(), transforms.Normalize(ORT, STD)])
    return e_tf, d_tf


def yukleyiciler(df, boyut=224, kok=KOK, num_workers=2):
    e_tf, d_tf = donusumler(boyut)
    tr = DataLoader(KidoDataset(df[df.bolum == "train"], e_tf, kok), batch_size=32, shuffle=True, num_workers=num_workers)
    va = DataLoader(KidoDataset(df[df.bolum == "val"], d_tf, kok), batch_size=64, num_workers=num_workers)
    return tr, va
