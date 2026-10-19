"""Ölçüm normları: KIDO train bölümündeki çizimlerin ölçümleri, sınıf düzeyi x görev (mutlu/üzgün) bazında.

Val ve test norma girmez. Dosya {output}/normlar/olcum_normlari.csv: train'deki her çizim için bir satır
(dosya, sinif, duygu, ölçümler, surum). Yüzdelik doğrudan bu dağılımdan hesaplanır (orta sıra: eşit değerlerin
yarısı altta sayılır; renk sayısı gibi tam sayılı ölçümlerde eşitlikler çoktur).

Kullanım: python -m src.measurements.norms   (train'deki bütün çizimleri ölçer, birkaç dakika)
"""
import os
from multiprocessing import Pool

import numpy as np
import pandas as pd

from ..config import PATHS
from ..data import image_path, load_metadata
from .metrics import MEASURES, MEASUREMENT_VERSION, measure

NORM_SPLIT = "train"


def norms_path(output_dir=PATHS["output"]):
    return f"{output_dir}/normlar/olcum_normlari.csv"


def _measure_row(item):
    dosya, path = item
    return {"dosya": dosya, **measure(path)}


def build_norms(df, output_dir=PATHS["output"], processes=6):
    table = df[df.bolum == NORM_SPLIT]
    items = [(r.dosya, image_path(r)) for _, r in table.iterrows()]
    with Pool(processes) as p:
        measured = pd.DataFrame(p.map(_measure_row, items, chunksize=50))
    norms = table[["dosya", "sinif", "duygu"]].merge(measured, on="dosya")
    norms["surum"] = MEASUREMENT_VERSION
    path = norms_path(output_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    norms.to_csv(path, index=False)
    return norms


def load_norms(path=None):
    norms = pd.read_csv(path or norms_path())
    versions = set(norms.surum.unique())
    if versions != {MEASUREMENT_VERSION}:
        raise RuntimeError(f"Normlar ölçüm sürümü {versions}, kod {MEASUREMENT_VERSION}: normları yeniden hesapla "
                           "(python -m src.measurements.norms).")
    return norms


def percentile(values, x):
    """x'in values dağılımındaki yüzdeliği (0-100, orta sıra). Değer ya da dağılım yoksa None."""
    values = np.asarray(pd.Series(values).dropna(), float)
    if x is None or len(values) == 0:
        return None
    return float(100 * ((values < x).sum() + 0.5 * (values == x).sum()) / len(values))


def tail_shares(values, x):
    """Akranların yüzde kaçı x'e eşit ya da daha düşük, yüzde kaçı eşit ya da daha yüksek.

    Aralık dışı (⚠) kararı bunlarla verilir, orta sıra yüzdelikle değil: koyu ton oranı 0 olan çizimler
    grupların %5-12'si olduğu halde orta sıra yüzdelikleri 2,5-6'ya düşer; sıradan bir değer işaretlenmesin.
    """
    values = np.asarray(pd.Series(values).dropna(), float)
    if x is None or len(values) == 0:
        return None, None
    return float(100 * (values <= x).mean()), float(100 * (values >= x).mean())


def norm_group(norms, grade, emotion):
    return norms[(norms.sinif == grade) & (norms.duygu == emotion)]


def summary(norms):
    """Grup bazında n ve her ölçümün %5 / %50 / %95 değerleri (kontrol için)."""
    rows = []
    for (grade, emotion), g in norms.groupby(["sinif", "duygu"]):
        row = {"sinif": grade, "duygu": emotion, "n": len(g)}
        for m in MEASURES:
            for q in (5, 50, 95):
                row[f"{m}_p{q}"] = round(float(g[m].quantile(q / 100)), 4)
        rows.append(row)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    norms = build_norms(load_metadata())
    print(f"{len(norms)} train çizimi ölçüldü -> {norms_path()}")
    print(f"soluk renk bayrağı: {norms.soluk_renk_bayragi.mean():.1%}")
    print(summary(norms).to_string(index=False))
