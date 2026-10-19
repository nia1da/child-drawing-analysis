"""deneyler.csv'nin sütun düzeni, eski düzenlerden taşıma ve satır ekleme.

Sonuç satırı her zaman append_record ile yazılır: dosya eski düzendeyse önce yedeklenip taşınır,
sonra satır eklenir; tanınmayan düzende hiçbir şey yazılmadan hata verilir. Böylece hangi ortamdan
(Colab ya da yerel) yazılırsa yazılsın dosya bozulmaz. Tanınan eski düzenler:

1. İlk düzen (deney, en_iyi_val_f1, epoch, dakika): parametreler deney adından çıkarılır.
   Orijinal deneyler_eski.csv olarak saklanır.
2. Sonradan eklenen sütunları eksik dosya (örn. augmentation, batch): eksik sütunlar
   ADDED_COLUMNS'daki değerle doldurulur. Orijinal deneyler_yedek_<tarih>.csv olarak saklanır.

İlk düzen için ayrıntılar:

Parametreler eski deney adından (örn. resnet50_320px_lr0.0001_ls0.1_s42) çıkarılır.
Ad epoch sayısını içermediği için toplam_epoch, notebook'taki "Sonuç:" çıktılarıyla
eşleşen satırlar için oradan alınır; eşleşmeyenlerde boş kalır. tarih bilinmediği için boştur.

Elle taşıma (yazmadan): python -m src.migrate_experiments
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

# deneyler.csv sütunları (adları Drive'daki kayıtlarla aynı kalmalı).
# Yeni bir hiperparametre değiştirilmeye başlanırsa buraya sütun olarak eklenmeli
COLUMNS = ["tarih", "deney", "model", "boyut", "lr", "smoothing", "seed", "augmentation", "batch", "accum_steps",
           "toplam_epoch", "en_iyi_epoch", "en_iyi_val_f1", "dakika", "not"]
# Sonradan eklenen sütunlar ve eklenmeden önceki deneylerdeki değerleri
ADDED_COLUMNS = {"augmentation": "temel", "batch": 32, "accum_steps": 1}
OLD_NAME = re.compile(r"^(?P<model>.+)_(?P<boyut>\d+)px_lr(?P<lr>[^_]+)_ls(?P<smoothing>[^_]+)_s(?P<seed>\d+)$")
NOTEBOOK = f"{REPO}/notebooks/grad_proj.ipynb"
FIRST_LAYOUT = ["deney", "en_iyi_val_f1", "epoch", "dakika"]
INT_COLUMNS = ["boyut", "seed", "batch", "accum_steps", "toplam_epoch", "en_iyi_epoch"]


def notebook_results(path=NOTEBOOK):
    """Notebook çıktılarındaki her "Sonuç:" kaydı -> o çalıştırmada görülen epoch sayısı."""
    results = {}
    with open(path, encoding="utf-8") as f:
        cells = json.load(f)["cells"]
    for cell in cells:
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


def layout(columns):
    """Başlığın düzeni: "current", "first" ya da "missing" (sonradan eklenen sütunlar eksik). Tanınmazsa hata."""
    if columns == COLUMNS:
        return "current"
    if columns == FIRST_LAYOUT:
        return "first"
    if set(columns) < set(COLUMNS) and set(COLUMNS) - set(columns) <= set(ADDED_COLUMNS):
        return "missing"
    raise ValueError(f"deneyler.csv tanınmayan sütun düzeninde: {columns}. Beklenen: {COLUMNS}")


def check_results_file(path):
    # Eğitimden önce, hiçbir şey yazmadan: dosya güncel ya da taşınabilir düzende mi (değilse hata)
    if os.path.exists(path):
        layout(pd.read_csv(path, nrows=0).columns.tolist())


def migrate_file(path):
    """Dosya eski düzendeyse yedekleyip güncel düzene taşır. Güncelse None, taşındıysa (yedek yolu, yeni tablo)."""
    old = pd.read_csv(path)
    kind = layout(old.columns.tolist())
    if kind == "current":
        return None
    folder = os.path.dirname(path)
    if kind == "first":
        backup, new = f"{folder}/deneyler_eski.csv", _from_first_layout(old)
    else:
        stamp = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y%m%d-%H%M")
        backup, new = f"{folder}/deneyler_yedek_{stamp}.csv", old.reindex(columns=COLUMNS)
    if os.path.exists(backup):
        raise FileExistsError(f"{backup} zaten var; üzerine yazmamak için durdum.")

    for column, value in ADDED_COLUMNS.items():
        new[column] = new[column].fillna(value)
    new = new.astype({k: "Int64" for k in INT_COLUMNS})

    shutil.copy2(path, backup)
    new.to_csv(path, index=False)
    print(f"deneyler.csv: {len(new)} satır güncel düzene taşındı; orijinal: {backup}")
    return backup, new


def append_record(path, record):
    """Sonuç satırını ekler; dosya eski düzendeyse önce taşır. Tanınmayan düzende hiçbir şey yazmadan hata verir."""
    if set(record) != set(COLUMNS):
        raise ValueError(f"Kayıt anahtarları sütunlarla uyuşmuyor: {sorted(set(record) ^ set(COLUMNS))}")
    exists = os.path.exists(path)
    if exists:
        migrate_file(path)
    pd.DataFrame([record], columns=COLUMNS).to_csv(path, mode="a", header=not exists, index=False)


def migrate(output_dir=PATHS["output"]):
    result = migrate_file(f"{output_dir}/deneyler.csv")
    if result is None:
        print("deneyler.csv zaten güncel düzende, bir şey yapılmadı.")
    else:
        print(result[1].to_string(index=False))


if __name__ == "__main__":
    migrate()
