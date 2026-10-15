"""Kayıtlı bir modeli (.pt) seçilen bölümde (varsayılan: test) değerlendirir.

Genel macro F1 ve karışıklık matrisinin yanında cinsiyet, eğitim seviyesi ve ikisinin
kesişimindeki alt gruplar için ayrı F1 verir. Tahminler {cikti}/tahminler/ altına kaydedilir.

Kullanım: .venv/bin/python -m src.degerlendir --deney convnext_tiny_448px_lr0.0001_ls0.1_s42
"""
import argparse
import os
import re

import pandas as pd
import torch
from sklearn.metrics import confusion_matrix, f1_score
from torch.utils.data import DataLoader

from .config import YOLLAR
from .egitim import HIZLI_ORNEK, MODELLER, cihaz, model_kur
from .veri import ETIKET, KOK, KidoDataset, donusumler, metadata_yukle

ALT_GRUPLAR = [["cinsiyet"], ["egitim"], ["egitim", "cinsiyet"]]


def deney_coz(isim):
    # Hem eski (resnet50_448px_lr...) hem yeni (resnet50_448_ep8_lr...) adlardan model ve boyutu çıkarır
    m = re.match(rf"^(?P<model>{'|'.join(MODELLER)})_(?P<boyut>\d+)(px)?_", isim)
    if m is None:
        raise ValueError(f"Deney adından model/boyut çıkarılamadı: {isim}; model= ve boyut= ver.")
    return m["model"], int(m["boyut"])


def tahmin_et(model, tablo, boyut, kok=KOK, batch=64, num_workers=2):
    _, d_tf = donusumler(boyut)
    dl = DataLoader(KidoDataset(tablo, d_tf, kok), batch_size=batch, num_workers=num_workers)
    model.eval(); olasilik = []
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=cihaz == "cuda"):
        for x, _ in dl:
            olasilik += model(x.to(cihaz)).float().softmax(1)[:, ETIKET["Sadness"]].cpu().tolist()
    sonuc = tablo.reset_index(drop=True)[["dosya", "duygu", "cinsiyet", "egitim", "ogrenci"]].copy()
    sonuc["gercek"] = sonuc.duygu.map(ETIKET)
    sonuc["olasilik_uzgun"] = olasilik
    sonuc["tahmin"] = (sonuc.olasilik_uzgun >= 0.5).astype(int)
    return sonuc


def ozet(t):
    return pd.Series({
        "n": len(t),
        "dogruluk": round((t.gercek == t.tahmin).mean(), 4),
        "macro_f1": round(f1_score(t.gercek, t.tahmin, average="macro", labels=[0, 1], zero_division=0), 4),
    })


def metrikler(sonuc):
    genel = ozet(sonuc)
    karisiklik = pd.DataFrame(confusion_matrix(sonuc.gercek, sonuc.tahmin, labels=[0, 1]),
                              index=[f"gercek_{k}" for k in ETIKET], columns=[f"tahmin_{k}" for k in ETIKET])
    gruplar = {"+".join(g): sonuc.groupby(g).apply(ozet, include_groups=False).astype({"n": int}) for g in ALT_GRUPLAR}
    return genel, karisiklik, gruplar


def degerlendir(df, deney, model=None, boyut=None, bolum="test", kok=KOK, cikti=YOLLAR["cikti"], hizli=False):
    """hizli=True: bölümden her sınıftan birkaç görsel; .pt yoksa ImageNet ağırlıklı model kullanılır
    (sadece kod yolunu test etmek için) ve tahminler kaydedilmez."""
    if model is None or boyut is None:
        model, boyut = deney_coz(deney)
    tablo = df[df.bolum == bolum]
    num_workers = 2
    if hizli:
        tablo = tablo.groupby("duygu", group_keys=False).sample(n=HIZLI_ORNEK, random_state=42)
        num_workers = 0

    pt = f"{cikti}/{deney}.pt"
    if os.path.exists(pt):
        m = model_kur(model, onegitimli=False)
        m.load_state_dict(torch.load(pt, map_location=cihaz))
    elif hizli:
        print(f"[hızlı mod] {pt} yok; ImageNet ağırlıklı model kullanılıyor")
        m = model_kur(model)
    else:
        raise FileNotFoundError(pt)

    sonuc = tahmin_et(m, tablo, boyut, kok, num_workers=num_workers)
    genel, karisiklik, gruplar = metrikler(sonuc)

    print(f"== {deney} | {bolum} | {cihaz} ==")
    print(f"Genel: n={int(genel.n)} | doğruluk {genel.dogruluk:.4f} | macro F1 {genel.macro_f1:.4f}\n")
    print(karisiklik, "\n")
    for ad, t in gruplar.items():
        print(f"-- {ad} --\n{t}\n")

    if hizli:
        print("[hızlı mod] tahminler kaydedilmedi")
    else:
        os.makedirs(f"{cikti}/tahminler", exist_ok=True)
        sonuc.to_csv(f"{cikti}/tahminler/{deney}_{bolum}.csv", index=False)
    return {"genel": genel, "karisiklik": karisiklik, "gruplar": gruplar, "tahminler": sonuc}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Kayıtlı modeli değerlendirme")
    p.add_argument("--deney", required=True, help=".pt dosyasının uzantısız adı")
    p.add_argument("--model", choices=MODELLER)
    p.add_argument("--boyut", type=int)
    p.add_argument("--bolum", default="test", choices=["train", "val", "test"])
    p.add_argument("--hizli", action="store_true")
    a = p.parse_args()
    degerlendir(metadata_yukle(), a.deney, a.model, a.boyut, a.bolum, hizli=a.hizli)
