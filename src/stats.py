"""Alt grup F1'leri için öğrenci bazlı bootstrap güven aralıkları.

Aynı öğrencinin çizimleri birbirinden bağımsız değildir; çizimleri tek tek yeniden örneklemek
aralıkları olduğundan dar gösterir. Bu yüzden öğrenciler (tüm çizimleriyle birlikte) yerine
koyarak yeniden örneklenir. Her öğrencinin cinsiyeti ve eğitim seviyesi tektir, yani öğrenciler
alt gruplara tam olarak bölünür.
"""
import numpy as np
import pandas as pd

from .config import PATHS

# (ad, sütun -> değer filtresi); boş filtre = tüm bölüm
GROUPS = [
    ("Genel", {}),
    ("Female", {"cinsiyet": "Female"}),
    ("Male", {"cinsiyet": "Male"}),
    ("Primary", {"egitim": "Primary"}),
    ("Secondary", {"egitim": "Secondary"}),
    ("Primary Female", {"egitim": "Primary", "cinsiyet": "Female"}),
    ("Primary Male", {"egitim": "Primary", "cinsiyet": "Male"}),
    ("Secondary Female", {"egitim": "Secondary", "cinsiyet": "Female"}),
    ("Secondary Male", {"egitim": "Secondary", "cinsiyet": "Male"}),
]
DIFFERENCES = [  # (birinci - ikinci)
    ("Female", "Male"),
    ("Secondary", "Primary"),
    ("Primary Female", "Primary Male"),
    ("Secondary Female", "Secondary Male"),
]


def load_predictions(experiment, split="test", output_dir=PATHS["output"]):
    return pd.read_csv(f"{output_dir}/tahminler/{experiment}_{split}.csv")


def _macro_f1(counts):
    # counts[..., :] = (g0t0, g0t1, g1t0, g1t1); g = gerçek, t = tahmin, 1 = Sadness
    tn, fp, fn, tp = np.moveaxis(counts, -1, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1_1 = np.where(2 * tp + fp + fn > 0, 2 * tp / (2 * tp + fp + fn), 0.0)
        f1_0 = np.where(2 * tn + fp + fn > 0, 2 * tn / (2 * tn + fp + fn), 0.0)
    return (f1_0 + f1_1) / 2


def confidence_intervals(result, n_boot=2000, seed=42, alpha=0.05):
    """Her alt grup için macro F1 ve %95 GA; seçili grup çiftleri için F1 farkı ve GA.

    Fark aralığı 0'ı içermiyorsa fark %5 düzeyinde anlamlıdır.
    """
    cell = result.gercek * 2 + result.tahmin  # 0..3, _macro_f1'deki sırayla
    counts = pd.crosstab(result.ogrenci, cell).reindex(columns=range(4), fill_value=0)
    info = result.groupby("ogrenci")[["cinsiyet", "egitim"]].first().loc[counts.index]
    C = counts.to_numpy(float)  # öğrenci x 4

    rng = np.random.default_rng(seed)
    S = len(C)
    W = rng.multinomial(S, np.full(S, 1 / S), size=n_boot)  # n_boot x öğrenci: kaç kez seçildi

    point, dist, rows = {}, {}, []
    for name, filt in GROUPS:
        mask = np.ones(S, bool)
        for column, value in filt.items():
            mask &= (info[column] == value).to_numpy()
        point[name] = float(_macro_f1(C[mask].sum(0)))
        # einsum: macOS Accelerate'teki matmul sahte uyarı verdiği için BLAS'sız çarpım (boyutlar küçük)
        dist[name] = _macro_f1(np.einsum("bs,sk->bk", W[:, mask], C[mask]))
        low, high = np.quantile(dist[name], [alpha / 2, 1 - alpha / 2])
        rows.append({"grup": name, "n_cizim": int(C[mask].sum()), "n_ogrenci": int(mask.sum()),
                     "macro_f1": round(point[name], 4), "ga_alt": round(low, 4), "ga_ust": round(high, 4)})
    groups = pd.DataFrame(rows)

    diffs = []
    for a, b in DIFFERENCES:
        d = dist[a] - dist[b]
        low, high = np.quantile(d, [alpha / 2, 1 - alpha / 2])
        diffs.append({"fark": f"{a} - {b}", "f1_farki": round(point[a] - point[b], 4),
                      "ga_alt": round(low, 4), "ga_ust": round(high, 4), "anlamli": bool(low > 0 or high < 0)})
    return groups, pd.DataFrame(diffs)
