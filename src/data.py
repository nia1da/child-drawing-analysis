import os
import zipfile
from functools import partial
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from .config import PATHS

ROOT = PATHS["root"]
LABELS = {"Happiness": 0, "Sadness": 1}
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]
KIDO_GDRIVE_ID = "1Ip5HI3kqnZ0Lpc0jQKxl30IjHmksqkrf"  # açık KIDO veri seti


def prepare_data(root=ROOT, zip_path=PATHS["zip"]):
    # Görseller yoksa KIDO zip'ini açar; zip de yoksa önce bir kez indirir (Colab'da Drive'a kaydolur).
    # Zip içi Dataset/... ile başlar, bu yüzden root'un iki üstüne açılır.
    if os.path.isdir(root):
        return
    if not os.path.exists(zip_path):
        import gdown
        print(f"{zip_path} yok; KIDO indiriliyor (bir kez)...")
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        gdown.download(id=KIDO_GDRIVE_ID, output=f"{zip_path}.part", quiet=False)
        os.replace(f"{zip_path}.part", zip_path)  # yarım kalan indirme zip gibi görünmesin
    target = Path(root).parents[1]
    print(f"{zip_path} -> {target} açılıyor...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(target)


def collect_images(category, root=ROOT):
    records = {}  # dosya_adi -> (split, etiket)
    for split in ["train", "test"]:
        for label in os.listdir(f"{root}/{category}/{split}"):
            for file in os.listdir(f"{root}/{category}/{split}/{label}"):
                records[file] = (split, label)
    return records


def build_metadata(root=ROOT):
    """Emotion/Gender/Education klasörlerinden tek bir metadata tablosu kurar."""
    emotion = collect_images("Emotion", root)
    gender = collect_images("Gender", root)
    education = collect_images("Education", root)

    rows = []
    for file in emotion:
        parts = file.replace(".jpg", "").split("-")
        rows.append({
            "dosya": file,
            "split": emotion[file][0],
            "duygu": emotion[file][1],
            "cinsiyet": gender[file][1],
            "egitim": education[file][1],
            "ogrenci": "-".join(parts[:3]),  # okul-sınıf-no
        })
    return pd.DataFrame(rows)


def load_metadata(path=PATHS["metadata"]):
    return pd.read_csv(path)


def image_path(s, root=ROOT):
    return f"{root}/Emotion/{s.split}/{s.duygu}/{s.dosya}"


class KidoDataset(Dataset):
    def __init__(self, table, tf, root=ROOT):
        self.table, self.tf, self.root = table.reset_index(drop=True), tf, root

    def __len__(self):
        return len(self.table)

    def __getitem__(self, i):
        s = self.table.iloc[i]
        return self.tf(Image.open(image_path(s, self.root))), LABELS[s.duygu]


def pad_to_square(img, size):
    # Oranı koruyarak size x size'a sığdırır, boşlukları beyazla doldurur
    return ImageOps.pad(img.convert("RGB"), (size, size), color="white")


AUGMENTATIONS = ["temel", "renk"]


def build_transforms(size=224, aug="temel"):
    """aug="temel": yatay çevirme + küçük döndürme.
    aug="renk": + renk bozma ve gri tonlama; modeli renk yerine içerik ve şekle bakmaya zorlamak için."""
    if aug not in AUGMENTATIONS:
        raise ValueError(f"Bilinmeyen aug: {aug} (seçenekler: {AUGMENTATIONS})")
    # lambda yerine partial: macOS/Windows'ta DataLoader worker'ları spawn ile açıldığı için pickle edilebilmeli
    pad = partial(pad_to_square, size=size)
    train_steps = [transforms.Lambda(pad), transforms.RandomHorizontalFlip(), transforms.RandomRotation(5, fill=255)]
    if aug == "renk":
        train_steps += [transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.6, hue=0.1),
                        transforms.RandomGrayscale(p=0.3)]
    train_tf = transforms.Compose(train_steps + [transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    eval_tf = transforms.Compose([transforms.Lambda(pad), transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    return train_tf, eval_tf


def build_loaders(df, size=224, root=ROOT, num_workers=2, batch=32, aug="temel"):
    train_tf, eval_tf = build_transforms(size, aug)
    # persistent_workers: worker'lar her epoch yeniden açılmasın (spawn ile açılış Windows/macOS'ta pahalı)
    kw = {"num_workers": num_workers, "persistent_workers": num_workers > 0}
    tr = DataLoader(KidoDataset(df[df.bolum == "train"], train_tf, root), batch_size=batch, shuffle=True, **kw)
    va = DataLoader(KidoDataset(df[df.bolum == "val"], eval_tf, root), batch_size=batch * 2, **kw)
    return tr, va
