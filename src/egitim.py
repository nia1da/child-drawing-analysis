import argparse
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torchvision import models

from .config import YOLLAR
from .veri import KOK, metadata_yukle, yukleyiciler

MODELLER = ["resnet50", "efficientnet_b0", "convnext_tiny"]
# Yeni bir hiperparametre değiştirilmeye başlanırsa buraya sütun olarak eklenmeli
SUTUNLAR = ["tarih", "deney", "model", "boyut", "lr", "smoothing", "seed",
            "toplam_epoch", "en_iyi_epoch", "en_iyi_val_f1", "dakika", "not"]
HIZLI_ORNEK = 8  # hızlı modda bölüm başına, her sınıftan görsel sayısı


def cihaz_sec():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


cihaz = cihaz_sec()


def model_kur(ad, onegitimli=True):
    # onegitimli=False: kayıtlı .pt yüklenecekse ImageNet ağırlıklarını indirmeye gerek yok
    w = "DEFAULT" if onegitimli else None
    if ad == "resnet50":
        m = models.resnet50(weights=w); m.fc = nn.Linear(m.fc.in_features, 2)
    elif ad == "efficientnet_b0":
        m = models.efficientnet_b0(weights=w); m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    elif ad == "convnext_tiny":
        m = models.convnext_tiny(weights=w); m.classifier[2] = nn.Linear(m.classifier[2].in_features, 2)
    else:
        raise ValueError(f"Bilinmeyen model: {ad}")
    return m.to(cihaz)


def hizli_ornekle(df, n=HIZLI_ORNEK, seed=42):
    # train ve val'den her duygu sınıfından n görsel
    parca = df[df.bolum.isin(["train", "val"])]
    return parca.groupby(["bolum", "duygu"], group_keys=False).sample(n=n, random_state=seed)


def lr_yaz(lr):
    # 0.0001 -> "1e-4", 0.0003 -> "3e-4", 0.00025 -> "2.5e-4"
    mantis, us = f"{lr:e}".split("e")
    return f"{mantis.rstrip('0').rstrip('.')}e{int(us)}"


def deney_adi(ad, boyut, epoch, lr, smoothing, seed):
    # Örn. convnext_tiny_320_ep12_lr1e-4_ls0.1_s42; .pt dosyası ve deneyler.csv'deki "deney" bu adı kullanır
    return f"{ad}_{boyut}_ep{epoch}_lr{lr_yaz(lr)}_ls{smoothing:g}_s{seed}"


def deney_benzersiz_mi(isim, cikti):
    # Aynı adlı deney varsa eğitimden önce dur; mevcut .pt dosyasının üzerine yazılmasın
    if os.path.exists(f"{cikti}/{isim}.pt"):
        raise FileExistsError(f"{cikti}/{isim}.pt zaten var; aynı deney tekrar çalıştırılmak isteniyorsa önce eski dosyayı taşı.")
    yol = f"{cikti}/deneyler.csv"
    if os.path.exists(yol) and isim in set(pd.read_csv(yol).deney):
        raise FileExistsError(f"{isim} zaten deneyler.csv'de kayıtlı.")


def sonuc_dosyasi_kontrol(yol):
    # Eski düzendeki bir dosyaya yeni satır eklemek CSV'yi bozar; eğitimden önce durdur
    if os.path.exists(yol):
        baslik = pd.read_csv(yol, nrows=0).columns.tolist()
        if baslik != SUTUNLAR:
            raise RuntimeError(f"{yol} eski sütun düzeninde: {baslik}. Önce yeni düzene ({SUTUNLAR}) taşınmalı.")


def egit(df, ad, boyut=224, epoch=8, lr=1e-4, smoothing=0.1, seed=42, kok=KOK, cikti=YOLLAR["cikti"],
         not_="", hizli=False):
    """Modeli eğitir, en iyi val F1'li ağırlığı kaydeder ve deneyler.csv'ye bir satır ekler.

    hizli=True: her sınıftan birkaç görsel, 1 epoch, küçük batch. Kod yolunu yerelde test etmek
    içindir; model kaydedilmez ve deneyler.csv'ye yazılmaz.
    """
    yol = f"{cikti}/deneyler.csv"
    if hizli:
        df, epoch, batch, num_workers = hizli_ornekle(df, seed=seed), 1, 4, 0
    isim = deney_adi(ad, boyut, epoch, lr, smoothing, seed)
    if not hizli:
        sonuc_dosyasi_kontrol(yol)
        deney_benzersiz_mi(isim, cikti)
        os.makedirs(cikti, exist_ok=True)
        batch, num_workers = 32, 2

    torch.manual_seed(seed)
    tr, va = yukleyiciler(df, boyut, kok, num_workers=num_workers, batch=batch)
    model = model_kur(ad)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    plan = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epoch * len(tr))
    kayip_fn = nn.CrossEntropyLoss(label_smoothing=smoothing)
    amp = cihaz == "cuda"  # float16 AMP sadece CUDA'da; MPS ve CPU float32 çalışır
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    en_iyi, en_iyi_ep, bas = 0, 0, time.time()

    for ep in range(epoch):
        model.train()
        for x, y in tr:
            x, y = x.to(cihaz), y.to(cihaz)
            optim.zero_grad()
            with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
                kayip = kayip_fn(model(x), y)
            scaler.scale(kayip).backward(); scaler.step(optim); scaler.update(); plan.step()

        model.eval(); tahmin, gercek = [], []
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            for x, y in va:
                tahmin += model(x.to(cihaz)).argmax(1).cpu().tolist(); gercek += y.tolist()
        f1 = f1_score(gercek, tahmin, average="macro")
        print(f"Epoch {ep+1}: son batch kayıp {kayip.item():.4f} | val F1 {f1:.4f}")
        if f1 > en_iyi:
            en_iyi, en_iyi_ep = f1, ep + 1
            if not hizli:
                torch.save(model.state_dict(), f"{cikti}/{isim}.pt")

    # Colab'ın saati UTC; tarih Türkiye saatiyle yazılır
    tarih = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")
    kayit = {"tarih": tarih, "deney": isim, "model": ad, "boyut": boyut,
             "lr": lr, "smoothing": smoothing, "seed": seed, "toplam_epoch": epoch, "en_iyi_epoch": en_iyi_ep,
             "en_iyi_val_f1": round(en_iyi, 4), "dakika": round((time.time() - bas) / 60, 1), "not": not_}
    if hizli:
        print(f"[hızlı mod] {cihaz} | {len(tr.dataset)} train / {len(va.dataset)} val görsel | kayıt yazılmadı")
    else:
        pd.DataFrame([kayit], columns=SUTUNLAR).to_csv(yol, mode="a", header=not os.path.exists(yol), index=False)
    print("Sonuç:", kayit)
    return kayit


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Çizim duygu modeli eğitimi")
    p.add_argument("--model", choices=MODELLER, default="resnet50")
    p.add_argument("--boyut", type=int, default=224)
    p.add_argument("--epoch", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--smoothing", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--not", dest="not_", default="")
    p.add_argument("--hizli", action="store_true", help="birkaç görsel, 1 epoch; model ve sonuç kaydedilmez")
    a = p.parse_args()
    egit(metadata_yukle(), a.model, boyut=a.boyut, epoch=a.epoch, lr=a.lr, smoothing=a.smoothing,
         seed=a.seed, not_=a.not_, hizli=a.hizli)
