"""Görev uyumu ve mutlu–üzgün ayrışma: tanımlar ve val analizi (plan: docs/plan_gorev_uyumu.md, adım 2).

- Görev uyumu (çizim başına): mutlu görevinde 1 - p, üzgün görevinde p; p = modelin "üzgün" olasılığı.
- Ayrışma (öğrenci başına): d = s(üzgün çizim) - s(mutlu çizim); s olasılık ya da logit.
- Norm grubu kararı plandaki, val tahminlerinden önce yazılmış ölçütle: her hücrede (seviye x görev; ayrışmada seviye)
  sınıf düzeyleri arasında Kruskal–Wallis (p < ALPHA / hücre sayısı) ve bir sınıfın havuzdaki medyan yüzdeliğinin
  50'den en az MIN_SHIFT puan sapması. İkisi birden bir hücrede sağlanırsa "belirgin eğilim": sınıf x görev normu.

Kullanım: python -m src.task_fit [--experiment <deney>]   (val tahminleri: python -m src.evaluation --split val)
"""
import argparse
import sys

import numpy as np
import pandas as pd
from scipy.stats import kruskal, rankdata

from .data import grade_from_filename
from .stats import load_predictions

REFERENCE = "convnext_tiny_320px_lr0.0001_ls0.1_s42"
SPLIT = "val"
LEVELS = ["Primary", "Secondary"]
TASKS = ["Happiness", "Sadness"]
ALPHA, MIN_SHIFT = 0.05, 10
# d için logit, val çiftlerinin bu oranından fazlasında iki skor da aynı uçtaysa (ikisi de < LOW ya da > HIGH)
SATURATION_SHARE, SATURATION_LOW, SATURATION_HIGH = 0.25, 0.1, 0.9
EPS = 1e-6  # logit için olasılık [EPS, 1 - EPS]'e kırpılır


def with_task_fit(pred):
    """Tahmin tablosuna sinif ve gorev_uyumu sütunları."""
    t = pred.copy()
    t["sinif"] = t.dosya.map(grade_from_filename)
    t["gorev_uyumu"] = np.where(t.duygu == "Sadness", t.olasilik_uzgun, 1 - t.olasilik_uzgun)
    return t


def logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def pairs(pred):
    """Öğrenci başına bir satır: iki çizimin olasılığı ve iki ayrışma (olasılık ve logit farkı).

    Her öğrencinin tam bir mutlu ve bir üzgün çizimi olmalı (KIDO'da öyle); değilse hata.
    """
    t = with_task_fit(pred)
    counts = t.groupby(["ogrenci", "duygu"]).size().unstack(fill_value=0).reindex(columns=TASKS, fill_value=0)
    if not (counts == 1).all().all():
        raise ValueError("Her öğrencinin tam bir mutlu ve bir üzgün çizimi olmalı")
    if (t.groupby("ogrenci")[["egitim", "sinif"]].nunique() > 1).any().any():
        raise ValueError("Bir öğrencinin iki çiziminde eğitim seviyesi ya da sınıf farklı")
    wide = t.pivot(index="ogrenci", columns="duygu", values="olasilik_uzgun")
    info = t.drop_duplicates("ogrenci").set_index("ogrenci")[["egitim", "sinif"]]
    out = info.join(wide.rename(columns={"Happiness": "p_mutlu", "Sadness": "p_uzgun"}))
    out["d_olasilik"] = out.p_uzgun - out.p_mutlu
    out["d_logit"] = logit(out.p_uzgun) - logit(out.p_mutlu)
    return out.reset_index()


def saturation_share(pair_table):
    """İki çizimin skorunun da aynı uçta olduğu çiftlerin oranı."""
    both_low = (pair_table.p_mutlu < SATURATION_LOW) & (pair_table.p_uzgun < SATURATION_LOW)
    both_high = (pair_table.p_mutlu > SATURATION_HIGH) & (pair_table.p_uzgun > SATURATION_HIGH)
    return float((both_low | both_high).mean())


def separation_score(pair_table):
    return "d_logit" if saturation_share(pair_table) > SATURATION_SHARE else "d_olasilik"


def pool_percentiles(values):
    # norms.percentile ile aynı orta sıra: (altta kalanlar + eşitlerin yarısı) / n
    return 100 * (rankdata(values, method="average") - 0.5) / len(values)


def grade_trend(values, grades):
    """Bir hücrede sınıflar arası Kruskal–Wallis p'si ve her sınıfın havuzdaki medyan yüzdeliği."""
    values, grades = np.asarray(values, float), np.asarray(grades)
    pct = pool_percentiles(values)
    groups = sorted(set(grades))
    p = float(kruskal(*[values[grades == g] for g in groups]).pvalue)
    medians = {int(g): float(np.median(pct[grades == g])) for g in groups}
    return p, medians


def cells(pred):
    """Ölçütün hücreleri: (ad, değerler, sınıflar). Görev uyumu 4 hücre, ayrışma 2 hücre."""
    t = with_task_fit(pred)
    pt = pairs(pred)
    score = separation_score(pt)
    out = []
    for level in LEVELS:
        for task in TASKS:
            c = t[(t.egitim == level) & (t.duygu == task)]
            out.append((f"görev uyumu | {level} | {task}", c.gorev_uyumu.values, c.sinif.values))
    for level in LEVELS:
        c = pt[pt.egitim == level]
        out.append((f"ayrışma ({score}) | {level}", c[score].values, c.sinif.values))
    return out


def norm_group_decision(pred):
    """Ölçütü uygular: hücre tablosu ve karar ("seviye" ya da "sinif")."""
    found = cells(pred)
    alpha = ALPHA / len(found)
    rows = []
    for name, values, grades in found:
        p, medians = grade_trend(values, grades)
        shift = max(abs(m - 50) for m in medians.values())
        rows.append({"hucre": name, "n": len(values), "kw_p": p, "anlamli": p < alpha,
                     "en_buyuk_sapma": round(shift, 1), "pratik": shift >= MIN_SHIFT,
                     "belirgin": p < alpha and shift >= MIN_SHIFT,
                     **{f"medyan_{g}": round(m, 1) for g, m in medians.items()}})
    table = pd.DataFrame(rows)
    return table, ("sinif" if table.belirgin.any() else "seviye")


def describe(pred):
    """Betimleyici özet: hücre bazında görev uyumu dağılımı ve uçlardaki yığılma."""
    t = with_task_fit(pred)
    rows = []
    for (level, task), c in t.groupby(["egitim", "duygu"]):
        v = c.gorev_uyumu
        rows.append({"seviye": level, "gorev": task, "n": len(v),
                     **{f"p{q}": round(float(v.quantile(q / 100)), 3) for q in (5, 25, 50, 75, 95)},
                     "uyum>0.9": round(float((v > 0.9).mean()), 3), "uyum<0.1": round(float((v < 0.1).mean()), 3)})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Görev uyumu ve ayrışma: val analizi ve norm grubu kararı")
    a.add_argument("--experiment", default=REFERENCE)
    args = a.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 200)
    pred = load_predictions(args.experiment, SPLIT)
    pt = pairs(pred)
    share = saturation_share(pt)
    print(f"== {args.experiment} | {SPLIT} | {len(pred)} çizim, {len(pt)} öğrenci ==\n")
    print("Görev uyumu dağılımı:\n" + describe(pred).to_string(index=False) + "\n")
    print(f"Ayrışma: iki skoru aynı uçta olan çiftler %{100 * share:.1f} (eşik %{100 * SATURATION_SHARE:.0f}) "
          f"-> {separation_score(pt)}")
    print(f"d > 0 olan çiftler: olasılıkla %{100 * (pt.d_olasilik > 0).mean():.1f}, "
          f"logitle %{100 * (pt.d_logit > 0).mean():.1f}\n")
    table, decision = norm_group_decision(pred)
    print(f"Norm grubu ölçütü (Kruskal–Wallis p < {ALPHA}/{len(table)} = {ALPHA / len(table):.4f}, "
          f"sapma ≥ {MIN_SHIFT} puan):\n" + table.to_string(index=False))
    print(f"\nKarar: {'sınıf x görev' if decision == 'sinif' else 'eğitim seviyesi x görev'}")
