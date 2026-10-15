"""Eski deneyler.csv'yi (deney, en_iyi_val_f1, epoch, dakika) yeni 12 sütunlu düzene taşır.

Parametreler eski deney adından (örn. resnet50_320px_lr0.0001_ls0.1_s42) çıkarılır.
Ad epoch sayısını içermediği için toplam_epoch, notebook'taki "Sonuç:" çıktılarıyla
eşleşen satırlar için oradan alınır; eşleşmeyenlerde boş kalır. tarih bilinmediği için boştur.
Orijinal dosya deneyler_eski.csv olarak saklanır.

Kullanım: .venv/bin/python -m src.deneyler_tasi
"""
import ast
import json
import os
import re
import shutil

import pandas as pd

from .config import REPO, YOLLAR
from .egitim import SUTUNLAR

ESKI_AD = re.compile(r"^(?P<model>.+)_(?P<boyut>\d+)px_lr(?P<lr>[^_]+)_ls(?P<smoothing>[^_]+)_s(?P<seed>\d+)$")
NOTEBOOK = f"{REPO}/notebooks/grad_proj.ipynb"


def notebook_sonuclari(yol=NOTEBOOK):
    """Notebook çıktılarındaki her "Sonuç:" kaydı -> o çalıştırmada görülen epoch sayısı."""
    sonuclar = {}
    for hucre in json.load(open(yol))["cells"]:
        for cikti in hucre.get("outputs", []):
            son_epoch = 0
            for satir in "".join(cikti.get("text", "")).splitlines():
                if m := re.match(r"Epoch (\d+):", satir):
                    son_epoch = int(m.group(1))
                elif satir.startswith("Sonuç: "):
                    k = ast.literal_eval(satir[len("Sonuç: "):])
                    anahtar = (k["deney"], k["en_iyi_val_f1"], k["epoch"], k["dakika"])
                    sonuclar[anahtar] = son_epoch
                    son_epoch = 0
    return sonuclar


def tasi(cikti=YOLLAR["cikti"]):
    yol, eski_yol = f"{cikti}/deneyler.csv", f"{cikti}/deneyler_eski.csv"
    eski = pd.read_csv(yol)
    if eski.columns.tolist() == SUTUNLAR:
        print("deneyler.csv zaten yeni düzende, bir şey yapılmadı.")
        return
    if os.path.exists(eski_yol):
        raise FileExistsError(f"{eski_yol} zaten var; üzerine yazmamak için durdum.")

    nb = notebook_sonuclari()
    satirlar = []
    for _, r in eski.iterrows():
        p = ESKI_AD.match(r.deney)
        if p is None:
            raise ValueError(f"Deney adı çözülemedi: {r.deney}")
        anahtar = (r.deney, round(float(r.en_iyi_val_f1), 4), int(r.epoch), round(float(r.dakika), 1))
        satirlar.append({
            "tarih": None, "deney": r.deney, "model": p["model"], "boyut": int(p["boyut"]),
            "lr": float(p["lr"]), "smoothing": float(p["smoothing"]), "seed": int(p["seed"]),
            "toplam_epoch": nb.get(anahtar), "en_iyi_epoch": int(r.epoch),
            "en_iyi_val_f1": r.en_iyi_val_f1, "dakika": r.dakika, "not": "eski kayıt",
        })
    yeni = pd.DataFrame(satirlar, columns=SUTUNLAR).astype({"toplam_epoch": "Int64"})

    shutil.copy2(yol, eski_yol)
    yeni.to_csv(yol, index=False)
    print(f"{len(yeni)} satır taşındı; orijinal: {eski_yol}")
    print(yeni.to_string(index=False))


if __name__ == "__main__":
    tasi()
