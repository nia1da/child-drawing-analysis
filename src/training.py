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

from .config import DEFAULTS, PATHS
from .data import AUGMENTATIONS, ROOT, build_loaders, load_metadata
# deneyler.csv sütun düzeni ve yazma migrate_experiments'te; COLUMNS buradan da erişilebilir kalsın
from .migrate_experiments import COLUMNS, append_record, check_results_file  # noqa: F401

MODELS = ["resnet50", "efficientnet_b0", "convnext_tiny"]
DEFAULT_EFFECTIVE_BATCH = 32  # deney adına sadece bundan farklıysa eklenir
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


def experiment_name(model_name, size, epochs, lr, smoothing, seed, aug="temel", effective_batch=DEFAULT_EFFECTIVE_BATCH):
    # Örn. convnext_tiny_320_ep12_lr1e-4_ls0.1_s42; .pt dosyası ve deneyler.csv'deki "deney" bu adı kullanır.
    # Varsayılan olmayan değerler sona eklenir (..._s42_aug-renk_eb64); böylece önceki deney adları değişmez.
    # Etkin batch = batch_size x accum_steps: yerel 16x2 ile Colab 32x1 aynı ayar sayılır, ayrım batch/accum_steps sütunlarında.
    suffix = "" if aug == "temel" else f"_aug-{aug}"
    if effective_batch != DEFAULT_EFFECTIVE_BATCH:
        suffix += f"_eb{effective_batch}"
    return f"{model_name}_{size}_ep{epochs}_lr{format_lr(lr)}_ls{smoothing:g}_s{seed}{suffix}"


def check_unique_experiment(name, output_dir):
    # Aynı adlı deney varsa eğitimden önce dur; mevcut .pt dosyasının üzerine yazılmasın
    if os.path.exists(f"{output_dir}/{name}.pt"):
        raise FileExistsError(f"{output_dir}/{name}.pt zaten var; aynı deney tekrar çalıştırılmak isteniyorsa "
                              "önce eski dosyayı taşı.")
    path = f"{output_dir}/deneyler.csv"
    if os.path.exists(path) and name in set(pd.read_csv(path).deney):
        raise FileExistsError(f"{name} zaten deneyler.csv'de kayıtlı.")


def train_epoch(model, loader, optim, scaler, loss_fn, accum_steps=1, schedule=None, amp=False):
    """Bir epoch; accum_steps micro-batch'in gradyanı toplanıp tek optimizer adımı atılır.

    Kayıp gruptaki micro-batch sayısına bölünür; epoch sonundaki yarım grup kendi boyuna bölünüp
    o da adım olarak uygulanır. GradScaler adımı ve zero_grad sadece grup sınırında.
    Eşit boylu micro-batch'lerde batch_size x accum_steps ile tek büyük batch aynı gradyanı verir
    (BatchNorm'lu modellerde değil: istatistikler micro-batch üzerinden hesaplanır).
    Son micro-batch'in kaybını döndürür.
    """
    dev = next(model.parameters()).device
    n = len(loader)
    optim.zero_grad()
    for i, (x, y) in enumerate(loader):
        x, y = x.to(dev), y.to(dev)
        group_start = i - i % accum_steps
        group = min(accum_steps, n - group_start)  # epoch sonundaki yarım grupta daha az
        with torch.autocast("cuda", dtype=torch.float16, enabled=amp):
            loss = loss_fn(model(x), y)
        scaler.scale(loss / group).backward()
        if i - group_start + 1 == group:  # grup sınırı ya da epoch sonu
            scaler.step(optim); scaler.update(); optim.zero_grad()
            if schedule is not None:
                schedule.step()
    return loss


def train(df, model_name, size=224, epochs=8, lr=1e-4, smoothing=0.1, seed=42, root=ROOT,
          output_dir=PATHS["output"], aug="temel", batch_size=DEFAULTS["batch_size"],
          accum_steps=DEFAULTS["accum_steps"], num_workers=DEFAULTS["num_workers"], note="", quick=False):
    """Modeli eğitir, en iyi val F1'li ağırlığı kaydeder ve deneyler.csv'ye bir satır ekler.

    batch_size, accum_steps, num_workers varsayılanları ortama göre (config.TRAINING_DEFAULTS):
    Colab 32 x 1, yerel 16 x 2; etkin batch ikisinde de 32.
    quick=True: her sınıftan birkaç görsel, 1 epoch, batch 4 (accum_steps aynen). Kod yolunu yerelde test etmek
    içindir; model kaydedilmez ve deneyler.csv'ye yazılmaz.
    """
    path = f"{output_dir}/deneyler.csv"
    if quick:
        df, epochs, batch_size, num_workers = quick_sample(df, seed=seed), 1, 4, 0
    name = experiment_name(model_name, size, epochs, lr, smoothing, seed, aug, batch_size * accum_steps)
    if not quick:
        check_results_file(path)  # tanınmayan düzen eğitimden önce yakalansın; taşıma yazarken (append_record)
        check_unique_experiment(name, output_dir)
        os.makedirs(output_dir, exist_ok=True)

    torch.manual_seed(seed)
    tr, va = build_loaders(df, size, root, num_workers=num_workers, batch=batch_size, aug=aug)
    model = build_model(model_name)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    steps_per_epoch = -(-len(tr) // accum_steps)  # yukarı yuvarlama: yarım grup da bir adım
    schedule = torch.optim.lr_scheduler.CosineAnnealingLR(optim, T_max=epochs * steps_per_epoch)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=smoothing)
    amp = device == "cuda"  # float16 AMP sadece CUDA'da; MPS ve CPU float32 çalışır
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    best, best_ep, start = 0, 0, time.time()

    for ep in range(epochs):
        model.train()
        loss = train_epoch(model, tr, optim, scaler, loss_fn, accum_steps, schedule, amp)

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
              "lr": lr, "smoothing": smoothing, "seed": seed, "augmentation": aug, "batch": batch_size,
              "accum_steps": accum_steps, "toplam_epoch": epochs,
              "en_iyi_epoch": best_ep, "en_iyi_val_f1": round(best, 4), "dakika": round((time.time() - start) / 60, 1),
              "not": note}
    if quick:
        print(f"[hızlı mod] {device} | {len(tr.dataset)} train / {len(va.dataset)} val görsel | kayıt yazılmadı")
    else:
        append_record(path, record)
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
    p.add_argument("--batch-size", type=int, default=DEFAULTS["batch_size"])
    p.add_argument("--accum-steps", type=int, default=DEFAULTS["accum_steps"])
    p.add_argument("--num-workers", type=int, default=DEFAULTS["num_workers"])
    p.add_argument("--note", default="")
    p.add_argument("--quick", action="store_true", help="birkaç görsel, 1 epoch; model ve sonuç kaydedilmez")
    a = p.parse_args()
    train(load_metadata(), a.model, size=a.size, epochs=a.epochs, lr=a.lr, smoothing=a.smoothing,
          seed=a.seed, aug=a.aug, batch_size=a.batch_size, accum_steps=a.accum_steps, num_workers=a.num_workers,
          note=a.note, quick=a.quick)
