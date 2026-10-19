"""Kayıtlı tahminler (tahminler/{deney}_{bolum}.csv) üzerinde analizler.

- Güven bandı: model "emin" mi "belirsiz" mi? Eşik val'de belirlenir, {output}/{deney}_esik.json'a kaydedilir.
- Hata yönü: mutlu çizimi "üzgün" ya da üzgünü "mutlu" sanma oranları, alt grup bazında.
- Deney karşılaştırma: aynı ayarın seed'lerini birlikte özetler.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .config import PATHS
from .stats import GROUPS, _macro_f1, load_predictions


def confidence(result):
    # 0 = kararsız (olasılık 0.5), 1 = tam emin
    return (result.olasilik_uzgun - 0.5).abs() * 2


def _iter_groups(result):
    for name, filt in GROUPS:
        t = result
        for column, value in filt.items():
            t = t[t[column] == value]
        yield name, t


def find_threshold(val, target=0.90):
    """'Emin' denen tahminlerin doğruluğu en az target olacak şekilde en düşük güven eşiği.

    En düşük eşik seçilir, böylece hedefi tutturan en çok sayıda tahmin "emin" sayılır.
    """
    g = confidence(val).to_numpy()
    correct = (val.gercek == val.tahmin).to_numpy()
    order = np.argsort(-g)  # en emin olandan başla
    cumulative = np.cumsum(correct[order]) / np.arange(1, len(g) + 1)
    valid = np.nonzero(cumulative >= target)[0]
    if len(valid) == 0:
        raise ValueError(f"Hiçbir eşikte doğruluk {target} olmuyor.")
    k = valid.max()
    # Aynı güven değerine sahip tahminler bölünmesin: eşik, k. tahminin güveni
    threshold = float(g[order][k])
    confident = g >= threshold
    # Anahtarlar Drive'daki {deney}_esik.json dosyalarıyla aynı kalmalı
    return {"hedef": target, "esik": round(threshold, 4), "val_kapsama": round(float(confident.mean()), 4),
            "val_emin_dogruluk": round(float(correct[confident].mean()), 4)}


def save_threshold(experiment, target=0.90, output_dir=PATHS["output"]):
    """Val tahminlerinden eşiği belirler ve modelin yanına kaydeder (val tahminleri önceden üretilmiş olmalı)."""
    result = find_threshold(load_predictions(experiment, "val", output_dir), target)
    result = {"deney": experiment, **result,
              "tarih": datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")}
    with open(f"{output_dir}/{experiment}_esik.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def load_threshold(experiment, output_dir=PATHS["output"]):
    with open(f"{output_dir}/{experiment}_esik.json", encoding="utf-8") as f:
        return json.load(f)["esik"]


def confidence_band(result, threshold):
    """Alt grup bazında: tahminlerin ne kadarı 'emin', emin ve belirsiz tahminlerin doğruluğu."""
    rows = []
    for name, t in _iter_groups(result):
        confident = confidence(t) >= threshold
        correct = t.gercek == t.tahmin
        rows.append({"grup": name, "n": len(t), "emin_orani": round(confident.mean(), 3),
                     "emin_dogruluk": round(correct[confident].mean(), 3),
                     "belirsiz_dogruluk": round(correct[~confident].mean(), 3) if (~confident).any() else np.nan})
    return pd.DataFrame(rows)


def error_direction(result):
    """Alt grup bazında: mutlu çizimlerin yüzde kaçı 'üzgün', üzgünlerin yüzde kaçı 'mutlu' tahmin edildi."""
    rows = []
    for name, t in _iter_groups(result):
        happy, sad = t[t.gercek == 0], t[t.gercek == 1]
        rows.append({"grup": name, "mutlu_uzgun_yuzde": round(100 * (happy.tahmin == 1).mean(), 1),
                     "uzgun_mutlu_yuzde": round(100 * (sad.tahmin == 0).mean(), 1)})
    return pd.DataFrame(rows)


def _f1(t):
    cell = (t.gercek * 2 + t.tahmin).value_counts().reindex(range(4), fill_value=0).to_numpy(float)
    return float(_macro_f1(cell))


def compare(experiments, split="val", output_dir=PATHS["output"]):
    """Her deney için genel ve alt grup F1'i, ilkokul erkek hata yönü; sonra ayar (seed hariç) bazında ortalama.

    experiments: {deney_adı: ayar_etiketi}, örn. {"..._s1": "temel", "..._s1_aug-renk": "renk"}
    """
    rows = []
    for experiment, setting in experiments.items():
        t = load_predictions(experiment, split, output_dir)
        f1 = {name: _f1(g) for name, g in _iter_groups(t)}
        pm = t[(t.egitim == "Primary") & (t.cinsiyet == "Male") & (t.gercek == 0)]
        rows.append({"ayar": setting, "deney": experiment, "f1_genel": f1["Genel"],
                     "f1_ilkokul_erkek": f1["Primary Male"], "f1_ilkokul_kiz": f1["Primary Female"],
                     "kiz_erkek_farki": f1["Female"] - f1["Male"],
                     "ilkokul_erkek_mutlu_uzgun_yuzde": 100 * (pm.tahmin == 1).mean()})
    single = pd.DataFrame(rows).round(4)
    numeric = single.columns.drop(["ayar", "deney"])
    summary = single.groupby("ayar")[list(numeric)].agg(["mean", "std"]).round(4)
    summary.insert(0, ("n_seed", ""), single.groupby("ayar").size())
    return single, summary
