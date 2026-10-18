"""deneyler.csv'yi güncel sütun düzenine (egitim.SUTUNLAR) taşır. İki durum:

1. İlk düzen (deney, en_iyi_val_f1, epoch, dakika): parametreler deney adından çıkarılır.
   Orijinal deneyler_eski.csv olarak saklanır.
2. Sonradan eklenen sütunları eksik dosya (örn. augmentation): eksik sütunlar
   egitim.EKLENEN_SUTUNLAR'daki değerle doldurulur. Orijinal deneyler_yedek_<tarih>.csv olarak saklanır.

İlk düzen için ayrıntılar:

Parametreler eski deney adından (örn. resnet50_320px_lr0.0001_ls0.1_s42) çıkarılır.
Ad epoch sayısını içermediği için toplam_epoch, notebook'taki "Sonuç:" çıktılarıyla
eşleşen satırlar için oradan alınır; eşleşmeyenlerde boş kalır. tarih bilinmediği için boştur.

Kullanım: .venv/bin/python -m src.deneyler_tasi
"""
import ast
import json
import os
import re
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from .config import REPO, YOLLAR
from .egitim import EKLENEN_SUTUNLAR, SUTUNLAR

ESKI_AD = re.compile(r"^(?P<model>.+)_(?P<boyut>\d+)px_lr(?P<lr>[^_]+)_ls(?P<smoothing>[^_]+)_s(?P<seed>\d+)$")
NOTEBOOK = f"{REPO}/notebooks/grad_proj.ipynb"
ILK_DUZEN = ["deney", "en_iyi_val_f1", "epoch", "dakika"]
TAM_SAYI = ["boyut", "seed", "toplam_epoch", "en_iyi_epoch"]


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


def _ilk_duzenden(eski):
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
    return pd.DataFrame(satirlar, columns=SUTUNLAR)


def tasi(cikti=YOLLAR["cikti"]):
    yol = f"{cikti}/deneyler.csv"
    eski = pd.read_csv(yol)
    sutunlar = eski.columns.tolist()
    eksik = set(SUTUNLAR) - set(sutunlar)
    if sutunlar == SUTUNLAR:
        print("deneyler.csv zaten güncel düzende, bir şey yapılmadı.")
        return
    if sutunlar == ILK_DUZEN:
        yedek, yeni = f"{cikti}/deneyler_eski.csv", _ilk_duzenden(eski)
    elif set(sutunlar) < set(SUTUNLAR) and eksik <= set(EKLENEN_SUTUNLAR):
        zaman = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y%m%d-%H%M")
        yedek, yeni = f"{cikti}/deneyler_yedek_{zaman}.csv", eski.reindex(columns=SUTUNLAR)
    else:
        raise ValueError(f"Tanınmayan sütun düzeni: {sutunlar}")
    if os.path.exists(yedek):
        raise FileExistsError(f"{yedek} zaten var; üzerine yazmamak için durdum.")

    for sutun, deger in EKLENEN_SUTUNLAR.items():
        yeni[sutun] = yeni[sutun].fillna(deger)
    yeni = yeni.astype({k: "Int64" for k in TAM_SAYI})

    shutil.copy2(yol, yedek)
    yeni.to_csv(yol, index=False)
    print(f"{len(yeni)} satır güncel düzene taşındı; orijinal: {yedek}")
    print(yeni.to_string(index=False))


if __name__ == "__main__":
    tasi()
