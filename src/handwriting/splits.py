"""Öğrenci bazlı, tabakalı train/val/test bölmesi (70/15/15, seed 42) ve dpi dengesi kuralı.

Birim: öğrenci kodu (bir öğrencinin bütün sayfaları tek bölümde). Tabakalar: sınıf x okul türü x grup x cinsiyet.
Yalnız meta veriye bakar (ölçüm değerlerine değil). dpi dengesi kuralı bölmeden ÖNCE yazılmıştır (docs/plan_el_yazisi.md §A7):
sınıf içinde ~300 dpi öğrenci payı bölümler arasında > 10 yüzde puan farklıysa seed değiştirilmez; öğrencinin çoğunluk dpi
grubu beşinci tabaka olarak eklenip bölme bir kez aynı seed'le yeniden yapılır.
"""
import hashlib

import numpy as np
import pandas as pd

from .paths import fd_lex_dir

STRATA = ["Klassenstufe", "Schulform", "Gruppe", "Geschlecht"]
FRACTIONS = (0.70, 0.15, 0.15)
SEED = 42
DPI_TOLERANCE = 0.10
DPI_BINS = [0, 120, 170, 230, 400, 10_000]
DPI_LABELS = ["<120", "~150", "~200", "~300", ">400"]


def student_table(pages):
    """Sayfa tablosundan (pages.csv) öğrenci tablosu: tabaka sütunları, çoğunluk dpi grubu, sayfa sayısı."""
    p = pages.dropna(subset=["code"]).copy()
    p["dpi_grup"] = pd.cut(p["dpi_eff"], DPI_BINS, labels=DPI_LABELS)
    first = p.groupby("code")[STRATA].first()
    major = p.groupby("code")["dpi_grup"].agg(lambda s: s.value_counts().idxmax()).rename("dpi_major")
    n = p.groupby("code").size().rename("n_pages")
    return first.join(major).join(n).reset_index()


def make_splits(students, seed=SEED, fractions=FRACTIONS, strata=STRATA):
    """Her tabaka içinde öğrencileri karıştırıp train/val/test'e böler. Döner: students + `bolum` sütunu."""
    rng = np.random.default_rng(seed)
    out = students.copy()
    out["bolum"] = ""
    for _, g in out.groupby(list(strata), observed=True):
        idx = rng.permutation(g.index.values)
        n = len(idx); n_tr = int(round(fractions[0] * n)); n_va = int(round(fractions[1] * n))
        out.loc[idx[:n_tr], "bolum"] = "train"
        out.loc[idx[n_tr:n_tr + n_va], "bolum"] = "val"
        out.loc[idx[n_tr + n_va:], "bolum"] = "test"
    return out


def dpi_balance(split):
    """Sınıf içinde ~300 dpi öğrenci payı (bölüme göre) ve en büyük bölüm farkı. Yalnız meta veri."""
    s = split.assign(is300=(split["dpi_major"].astype(str) == "~300"))
    share = s.groupby(["Klassenstufe", "bolum"])["is300"].mean().unstack()
    return share, float((share.max(1) - share.min(1)).max())


def make_splits_with_rule(students, seed=SEED):
    """Bölme + dpi dengesi kuralı. Döner: (bölme, rapor). Seed değiştirilmez; kural en çok bir kez yeniden bölme yapar."""
    split = make_splits(students, seed)
    share, gap = dpi_balance(split)
    report = dict(first_gap=gap, used_dpi_stratum=False)
    if gap > DPI_TOLERANCE:
        split = make_splits(students, seed, strata=STRATA + ["dpi_major"])
        share, gap = dpi_balance(split)
        report["used_dpi_stratum"] = True
    report.update(final_gap=gap, still_unbalanced=gap > DPI_TOLERANCE, share=share)
    return split, report


def write_splits(split, root=None):
    """`splits.csv`'yi yerel FD-LEX klasörüne yazar (öğrenci kodları içerir: yalnız yerel). Döner: (yol, sha256)."""
    base = fd_lex_dir(root)
    path = base / "splits.csv"
    split[["code", "bolum"]].sort_values("code").to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()
