"""deneyler.csv'yi güncel sütun düzenine (training.COLUMNS) taşır. İki durum:

1. İlk düzen (deney, en_iyi_val_f1, epoch, dakika): parametreler deney adından çıkarılır.
   Orijinal deneyler_eski.csv olarak saklanır.
2. Sonradan eklenen sütunları eksik dosya (örn. augmentation): eksik sütunlar
   training.ADDED_COLUMNS'daki değerle doldurulur. Orijinal deneyler_yedek_<tarih>.csv olarak saklanır.

İlk düzen için ayrıntılar:

Parametreler eski deney adından (örn. resnet50_320px_lr0.0001_ls0.1_s42) çıkarılır.
Ad epoch sayısını içermediği için toplam_epoch, notebook'taki "Sonuç:" çıktılarıyla
eşleşen satırlar için oradan alınır; eşleşmeyenlerde boş kalır. tarih bilinmediği için boştur.

Kullanım: python -m src.migrate_experiments
"""
import ast
import json
import os
import re
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from .config import PATHS, REPO
from .training import ADDED_COLUMNS, COLUMNS

OLD_NAME = re.compile(r"^(?P<model>.+)_(?P<boyut>\d+)px_lr(?P<lr>[^_]+)_ls(?P<smoothing>[^_]+)_s(?P<seed>\d+)$")
NOTEBOOK = f"{REPO}/notebooks/grad_proj.ipynb"
FIRST_LAYOUT = ["deney", "en_iyi_val_f1", "epoch", "dakika"]
INT_COLUMNS = ["boyut", "seed", "toplam_epoch", "en_iyi_epoch"]


def notebook_results(path=NOTEBOOK):
    """Notebook çıktılarındaki her "Sonuç:" kaydı -> o çalıştırmada görülen epoch sayısı."""
    results = {}
    for cell in json.load(open(path, encoding="utf-8"))["cells"]:
        for output in cell.get("outputs", []):
            last_epoch = 0
            for line in "".join(output.get("text", "")).splitlines():
                if m := re.match(r"Epoch (\d+):", line):
                    last_epoch = int(m.group(1))
                elif line.startswith("Sonuç: "):
                    k = ast.literal_eval(line[len("Sonuç: "):])
                    key = (k["deney"], k["en_iyi_val_f1"], k["epoch"], k["dakika"])
                    results[key] = last_epoch
                    last_epoch = 0
    return results


def _from_first_layout(old):
    nb = notebook_results()
    rows = []
    for _, r in old.iterrows():
        p = OLD_NAME.match(r.deney)
        if p is None:
            raise ValueError(f"Deney adı çözülemedi: {r.deney}")
        key = (r.deney, round(float(r.en_iyi_val_f1), 4), int(r.epoch), round(float(r.dakika), 1))
        rows.append({
            "tarih": None, "deney": r.deney, "model": p["model"], "boyut": int(p["boyut"]),
            "lr": float(p["lr"]), "smoothing": float(p["smoothing"]), "seed": int(p["seed"]),
            "toplam_epoch": nb.get(key), "en_iyi_epoch": int(r.epoch),
            "en_iyi_val_f1": r.en_iyi_val_f1, "dakika": r.dakika, "not": "eski kayıt",
        })
    return pd.DataFrame(rows, columns=COLUMNS)


def migrate(output_dir=PATHS["output"]):
    path = f"{output_dir}/deneyler.csv"
    old = pd.read_csv(path)
    columns = old.columns.tolist()
    missing = set(COLUMNS) - set(columns)
    if columns == COLUMNS:
        print("deneyler.csv zaten güncel düzende, bir şey yapılmadı.")
        return
    if columns == FIRST_LAYOUT:
        backup, new = f"{output_dir}/deneyler_eski.csv", _from_first_layout(old)
    elif set(columns) < set(COLUMNS) and missing <= set(ADDED_COLUMNS):
        stamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y%m%d-%H%M")
        backup, new = f"{output_dir}/deneyler_yedek_{stamp}.csv", old.reindex(columns=COLUMNS)
    else:
        raise ValueError(f"Tanınmayan sütun düzeni: {columns}")
    if os.path.exists(backup):
        raise FileExistsError(f"{backup} zaten var; üzerine yazmamak için durdum.")

    for column, value in ADDED_COLUMNS.items():
        new[column] = new[column].fillna(value)
    new = new.astype({k: "Int64" for k in INT_COLUMNS})

    shutil.copy2(path, backup)
    new.to_csv(path, index=False)
    print(f"{len(new)} satır güncel düzene taşındı; orijinal: {backup}")
    print(new.to_string(index=False))


if __name__ == "__main__":
    migrate()
