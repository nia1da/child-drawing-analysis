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

from .config import PATHS
from .data import AUGMENTATIONS, ROOT, build_loaders, load_metadata

MODELS = ["resnet50", "efficientnet_b0", "convnext_tiny"]
# deneyler.csv sütunları (adları Drive'daki kayıtlarla aynı kalmalı).
# Yeni bir hiperparametre değiştirilmeye başlanırsa buraya sütun olarak eklenmeli
COLUMNS = ["tarih", "deney", "model", "boyut", "lr", "smoothing", "seed", "augmentation",
           "toplam_epoch", "en_iyi_epoch", "en_iyi_val_f1", "dakika", "not"]
# Sonradan eklenen sütunlar ve eklenmeden önceki deneylerdeki değerleri (migrate_experiments kullanır)
ADDED_COLUMNS = {"augmentation": "temel"}
QUICK_SAMPLES = 8  # hızlı modda bölüm başına, her sınıftan görsel sayısı


def select_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


device = select_device()


def build_model(name, pretrained=True):
    # pretrained=False: kayıtlı .pt yüklenecekse ImageNet ağırlıklarını indirmeye gerek yok
    w = "DEFAULT" if pretrained else None
    if name == "resnet50":
        m = models.resnet50(weights=w); m.fc = nn.Linear(m.fc.in_features, 2)
    elif name == "efficientnet_b0":
        m = models.efficientnet_b0(weights=w); m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    elif name == "convnext_tiny":
        m = models.convnext_tiny(weights=w); m.classifier[2] = nn.Linear(m.classifier[2].in_features, 2)
    else:
        raise ValueError(f"Bilinmeyen model: {name}")
    return m.to(device)


def quick_sample(df, n=QUICK_SAMPLES, seed=42):
    # train ve val'den her duygu sınıfından n görsel
    part = df[df.bolum.isin(["train", "val"])]
    return part.groupby(["bolum", "duygu"], group_keys=False).sample(n=n, random_state=seed)


def format_lr(lr):
    # 0.0001 -> "1e-4", 0.0003 -> "3e-4", 0.00025 -> "2.5e-4"
    mantissa, exp = f"{lr:e}".split("e")
    return f"{mantissa.rstrip('0').rstrip('.')}e{int(exp)}"


def experiment_name(model_name, size, epochs, lr, smoothing, seed, aug="temel"):
    # Örn. convnext_tiny_320_ep12_lr1e-4_ls0.1_s42; .pt dosyası ve deneyler.csv'deki "deney" bu adı kullanır.
    # aug "temel" değilse sona eklenir (..._s42_aug-renk); böylece önceki deney adları değişmez.
    suffix = "" if aug == "temel" else f"_aug-{aug}"
    return f"{model_name}_{size}_ep{epochs}_lr{format_lr(lr)}_ls{smoothing:g}_s{seed}{suffix}"


def check_unique_experiment(name, output_dir):
    # Aynı adlı deney varsa eğitimden önce dur; mevcut .pt dosyasının üzerine yazılmasın
    if os.path.exists(f"{output_dir}/{name}.pt"):
        raise FileExistsError(f"{output_dir}/{name}.pt zaten var; aynı deney tekrar çalıştırılmak isteniyorsa "
                              "önce eski dosyayı taşı.")
    path = f"{output_dir}/deneyler.csv"
    if os.path.exists(path) and name in set(pd.read_csv(path).deney):
        raise FileExistsError(f"{name} zaten deneyler.csv'de kayıtlı.")


def check_results_file(path):
    # Eski düzendeki bir dosyaya yeni satır eklemek CSV'yi bozar; eğitimden önce durdur
    if os.path.exists(path):
        header = pd.read_csv(path, nrows=0).columns.tolist()
        if header != COLUMNS:
            raise RuntimeError(f"{path} eski sütun düzeninde: {header}. Önce yeni düzene ({COLUMNS}) taşınmalı "
                               "(python -m src.migrate_experiments).")


def train(df, model_name, size=224, epochs=8, lr=1e-4, smoothing=0.1, seed=42, root=ROOT,
          output_dir=PATHS["output"], aug="temel", note="", quick=False):
    """Modeli eğitir, en iyi val F1'li ağırlığı kaydeder ve deneyler.csv'ye bir satır ekler.

    quick=True: her sınıftan birkaç görsel, 1 epoch, küçük batch. Kod yolunu yerelde test etmek
    içindir; model kaydedilmez ve deneyler.csv'ye yazılmaz.
    """
    path = f"{output_dir}/deneyler.csv"
    if quick:
        df, epochs, batch, num_workers = quick_sample(df, seed=seed), 1, 4, 0
    name = experiment_name(model_name, size, epochs, lr, smoothing, seed, aug)
    if not quick:
        check_results_file(path)
        check_unique_experiment(name, output_dir)
        os.makedirs(output_dir, exist_ok=True)
        batch, num_workers = 32, 2

    torch.manual_seed(seed)
    tr, va = build_loaders(df, size, root, num_workers=num_workers, batch=batch, aug=aug)
    model = build_model(model_name)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs * len(tr))
    loss_fn = nn.CrossEntropyLoss(label_smoothing=smoothing)
    amp = device == "cuda"  # float16 AMP sadece CUDA'da; MPS ve CPU float32 çalışır
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    best, best_ep, start = 0, 0, time.time()

    for ep in range(epochs):
        model.train()
        for x, y in tr:
            x, y = x.to(device), y.to(device)
            optim.zero_grad()
            with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
                loss = loss_fn(model(x), y)
            scaler.scale(loss).backward(); scaler.step(optim); scaler.update(); schedule.step()

        model.eval(); preds, targets = [], []
        with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            for x, y in va:
                preds += model(x.to(device)).argmax(1).cpu().tolist(); targets += y.tolist()
        f1 = f1_score(targets, preds, average="macro")
        print(f"Epoch {ep+1}: son batch kayıp {loss.item():.4f} | val F1 {f1:.4f}")
        if f1 > best:
            best, best_ep = f1, ep + 1
            if not quick:
                torch.save(model.state_dict(), f"{output_dir}/{name}.pt")

    # Colab'ın saati UTC; tarih Türkiye saatiyle yazılır
    date = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")
    # Anahtarlar deneyler.csv sütunları
    record = {"tarih": date, "deney": name, "model": model_name, "boyut": size,
              "lr": lr, "smoothing": smoothing, "seed": seed, "augmentation": aug, "toplam_epoch": epochs,
              "en_iyi_epoch": best_ep, "en_iyi_val_f1": round(best, 4), "dakika": round((time.time() - start) / 60, 1),
              "not": note}
    if quick:
        print(f"[hızlı mod] {device} | {len(tr.dataset)} train / {len(va.dataset)} val görsel | kayıt yazılmadı")
    else:
        pd.DataFrame([record], columns=COLUMNS).to_csv(path, mode="a", header=not os.path.exists(path), index=False)
    print("Sonuç:", record)
    return record


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Çizim duygu modeli eğitimi")
    p.add_argument("--model", choices=MODELS, default="resnet50")
    p.add_argument("--size", type=int, default=224)
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--smoothing", type=float, default=0.1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--aug", choices=AUGMENTATIONS, default="temel")
    p.add_argument("--note", default="")
    p.add_argument("--quick", action="store_true", help="birkaç görsel, 1 epoch; model ve sonuç kaydedilmez")
    a = p.parse_args()
    train(load_metadata(), a.model, size=a.size, epochs=a.epochs, lr=a.lr, smoothing=a.smoothing,
          seed=a.seed, aug=a.aug, note=a.note, quick=a.quick)
