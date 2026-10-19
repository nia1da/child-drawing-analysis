"""Kayıtlı bir modeli (.pt) seçilen bölümde (varsayılan: test) değerlendirir.

Genel macro F1 ve karışıklık matrisinin yanında cinsiyet, eğitim seviyesi ve ikisinin
kesişimindeki alt gruplar için ayrı F1 verir. Tahminler {output}/tahminler/ altına kaydedilir.

Kullanım: python -m src.evaluation --experiment convnext_tiny_448px_lr0.0001_ls0.1_s42
"""
import argparse
import os
import re

import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, f1_score
from torch.utils.data import DataLoader

from .config import PATHS
from .data import LABELS, ROOT, KidoDataset, build_transforms, load_metadata
from .training import MODELS, QUICK_SAMPLES, build_model, device

SUBGROUPS = [["cinsiyet"], ["egitim"], ["egitim", "cinsiyet"]]


def parse_experiment(name):
    # Hem eski (resnet50_448px_lr...) hem yeni (resnet50_448_ep8_lr...) adlardan model ve boyutu çıkarır
    m = re.match(rf"^(?P<model>{'|'.join(MODELS)})_(?P<boyut>\d+)(px)?_", name)
    if m is None:
        raise ValueError(f"Deney adından model/boyut çıkarılamadı: {name}; model_name= ve size= ver.")
    return m["model"], int(m["boyut"])


def predict(model, table, size, root=ROOT, batch=64, num_workers=2):
    _, eval_tf = build_transforms(size)
    dl = DataLoader(KidoDataset(table, eval_tf, root), batch_size=batch, num_workers=num_workers)
    model.eval(); probs = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=device == "cuda"):
        for x, _ in dl:
            probs += model(x.to(device)).float().softmax(1)[:, LABELS["Sadness"]].cpu().tolist()
    # Sütun adları Drive'daki tahmin dosyalarıyla aynı kalmalı
    result = table.reset_index(drop=True)[["dosya", "duygu", "cinsiyet", "egitim", "ogrenci"]].copy()
    result["gercek"] = result.duygu.map(LABELS)
    result["olasilik_uzgun"] = probs
    result["tahmin"] = (result.olasilik_uzgun >= 0.5).astype(int)
    return result


def summarize(t):
    return pd.Series({
        "n": len(t),
        "dogruluk": round((t.gercek == t.tahmin).mean(), 4),
        "macro_f1": round(f1_score(t.gercek, t.tahmin, average="macro", labels=[0, 1], zero_division=0), 4),
    })


def compute_metrics(result):
    overall = summarize(result)
    confusion = pd.DataFrame(confusion_matrix(result.gercek, result.tahmin, labels=[0, 1]),
                             index=[f"gercek_{k}" for k in LABELS], columns=[f"tahmin_{k}" for k in LABELS])
    groups = {"+".join(g): result.groupby(g).apply(summarize, include_groups=False).astype({"n": int})
              for g in SUBGROUPS}
    return overall, confusion, groups


def evaluate(df, experiment, model_name=None, size=None, split="test", root=ROOT, output_dir=PATHS["output"],
             quick=False, verbose=True):
    """split: metadata'daki "bolum" (train/val/test).
    quick=True: bölümden her sınıftan birkaç görsel; .pt yoksa ImageNet ağırlıklı model kullanılır
    (sadece kod yolunu test etmek için) ve tahminler kaydedilmez."""
    if model_name is None or size is None:
        model_name, size = parse_experiment(experiment)
    table = df[df.bolum == split]
    num_workers = 2
    if quick:
        table = table.groupby("duygu", group_keys=False).sample(n=QUICK_SAMPLES, random_state=42)
        num_workers = 0

    pt = f"{output_dir}/{experiment}.pt"
    if os.path.exists(pt):
        m = build_model(model_name, pretrained=False)
        m.load_state_dict(torch.load(pt, map_location=device))
    elif quick:
        print(f"[hızlı mod] {pt} yok; ImageNet ağırlıklı model kullanılıyor")
        m = build_model(model_name)
    else:
        raise FileNotFoundError(pt)

    result = predict(m, table, size, root, num_workers=num_workers)
    overall, confusion, groups = compute_metrics(result)

    print(f"== {experiment} | {split} | {device} ==")
    print(f"Genel: n={int(overall.n)} | doğruluk {overall.dogruluk:.4f} | macro F1 {overall.macro_f1:.4f}\n")
    if verbose:
        print(confusion, "\n")
        for name, t in groups.items():
            print(f"-- {name} --\n{t}\n")

    if quick:
        print("[hızlı mod] tahminler kaydedilmedi")
    else:
        os.makedirs(f"{output_dir}/tahminler", exist_ok=True)
        result.to_csv(f"{output_dir}/tahminler/{experiment}_{split}.csv", index=False)
    return {"overall": overall, "confusion": confusion, "groups": groups, "predictions": result}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Kayıtlı modeli değerlendirme")
    p.add_argument("--experiment", required=True, help=".pt dosyasının uzantısız adı")
    p.add_argument("--model", choices=MODELS)
    p.add_argument("--size", type=int)
    p.add_argument("--split", default="test", choices=["train", "val", "test"])
    p.add_argument("--quick", action="store_true")
    a = p.parse_args()
    evaluate(load_metadata(), a.experiment, a.model, a.size, a.split, quick=a.quick)
