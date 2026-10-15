import os
import time

import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torchvision import models

from .veri import KOK, yukleyiciler

cihaz = "cuda" if torch.cuda.is_available() else "cpu"


def model_kur(ad):
    if ad == "resnet50":
        m = models.resnet50(weights="DEFAULT"); m.fc = nn.Linear(m.fc.in_features, 2)
    elif ad == "efficientnet_b0":
        m = models.efficientnet_b0(weights="DEFAULT"); m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    elif ad == "convnext_tiny":
        m = models.convnext_tiny(weights="DEFAULT"); m.classifier[2] = nn.Linear(m.classifier[2].in_features, 2)
    else:
        raise ValueError(f"Bilinmeyen model: {ad}")
    return m.to(cihaz)


def egit(df, ad, boyut=224, epoch=8, lr=1e-4, smoothing=0.1, seed=42, kok=KOK, cikti="models"):
    torch.manual_seed(seed)
    os.makedirs(cikti, exist_ok=True)
    tr, va = yukleyiciler(df, boyut, kok)
    model = model_kur(ad)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    plan = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epoch * len(tr))
    kayip_fn = nn.CrossEntropyLoss(label_smoothing=smoothing)
    amp = cihaz == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    isim = f"{ad}_{boyut}px_lr{lr}_ls{smoothing}_s{seed}"
    en_iyi, en_iyi_ep, bas = 0, 0, time.time()

    for ep in range(epoch):
        model.train()
        for x, y in tr:
            x, y = x.to(cihaz), y.to(cihaz)
            optim.zero_grad()
            with torch.autocast(cihaz, dtype=torch.float16, enabled=amp):
                kayip = kayip_fn(model(x), y)
            scaler.scale(kayip).backward(); scaler.step(optim); scaler.update(); plan.step()

        model.eval(); tahmin, gercek = [], []
        with torch.no_grad(), torch.autocast(cihaz, dtype=torch.float16, enabled=amp):
            for x, y in va:
                tahmin += model(x.to(cihaz)).argmax(1).cpu().tolist(); gercek += y.tolist()
        f1 = f1_score(gercek, tahmin, average="macro")
        print(f"Epoch {ep+1}: val F1 {f1:.4f}")
        if f1 > en_iyi:
            en_iyi, en_iyi_ep = f1, ep + 1
            torch.save(model.state_dict(), f"{cikti}/{isim}.pt")

    kayit = {"deney": isim, "en_iyi_val_f1": round(en_iyi, 4), "epoch": en_iyi_ep, "dakika": round((time.time() - bas) / 60, 1)}
    yol = f"{cikti}/deneyler.csv"
    pd.DataFrame([kayit]).to_csv(yol, mode="a", header=not os.path.exists(yol), index=False)
    print("Sonuç:", kayit)
    return kayit
