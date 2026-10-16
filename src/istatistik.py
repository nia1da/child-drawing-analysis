"""Alt grup F1'leri için öğrenci bazlı bootstrap güven aralıkları.

Aynı öğrencinin çizimleri birbirinden bağımsız değildir; çizimleri tek tek yeniden örneklemek
aralıkları olduğundan dar gösterir. Bu yüzden öğrenciler (tüm çizimleriyle birlikte) yerine
koyarak yeniden örneklenir. Her öğrencinin cinsiyeti ve eğitim seviyesi tektir, yani öğrenciler
alt gruplara tam olarak bölünür.
"""
import numpy as np
import pandas as pd

from .config import YOLLAR

# (ad, sütun -> değer filtresi); boş filtre = tüm bölüm
GRUPLAR = [
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
FARKLAR = [  # (birinci - ikinci)
    ("Female", "Male"),
    ("Secondary", "Primary"),
    ("Primary Female", "Primary Male"),
    ("Secondary Female", "Secondary Male"),
]


def kayitli_tahminler(deney, bolum="test", cikti=YOLLAR["cikti"]):
    return pd.read_csv(f"{cikti}/tahminler/{deney}_{bolum}.csv")


def _macro_f1(sayim):
    # sayim[..., :] = (g0t0, g0t1, g1t0, g1t1); g = gerçek, t = tahmin, 1 = Sadness
    tn, fp, fn, tp = np.moveaxis(sayim, -1, 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        f1_1 = np.where(2 * tp + fp + fn > 0, 2 * tp / (2 * tp + fp + fn), 0.0)
        f1_0 = np.where(2 * tn + fp + fn > 0, 2 * tn / (2 * tn + fp + fn), 0.0)
    return (f1_0 + f1_1) / 2


def guven_araliklari(sonuc, tekrar=2000, seed=42, alfa=0.05):
    """Her alt grup için macro F1 ve %95 GA; seçili grup çiftleri için F1 farkı ve GA.

    Fark aralığı 0'ı içermiyorsa fark %5 düzeyinde anlamlıdır.
    """
    hucre = sonuc.gercek * 2 + sonuc.tahmin  # 0..3, _macro_f1'deki sırayla
    sayim = pd.crosstab(sonuc.ogrenci, hucre).reindex(columns=range(4), fill_value=0)
    bilgi = sonuc.groupby("ogrenci")[["cinsiyet", "egitim"]].first().loc[sayim.index]
    C = sayim.to_numpy(float)  # öğrenci x 4

    rng = np.random.default_rng(seed)
    S = len(C)
    W = rng.multinomial(S, np.full(S, 1 / S), size=tekrar)  # tekrar x öğrenci: kaç kez seçildi

    nokta, dagilim, satirlar = {}, {}, []
    for ad, filtre in GRUPLAR:
        maske = np.ones(S, bool)
        for sutun, deger in filtre.items():
            maske &= (bilgi[sutun] == deger).to_numpy()
        nokta[ad] = float(_macro_f1(C[maske].sum(0)))
        # einsum: macOS Accelerate'teki matmul sahte uyarı verdiği için BLAS'sız çarpım (boyutlar küçük)
        dagilim[ad] = _macro_f1(np.einsum("bs,sk->bk", W[:, maske], C[maske]))
        alt, ust = np.quantile(dagilim[ad], [alfa / 2, 1 - alfa / 2])
        satirlar.append({"grup": ad, "n_cizim": int(C[maske].sum()), "n_ogrenci": int(maske.sum()),
                         "macro_f1": round(nokta[ad], 4), "ga_alt": round(alt, 4), "ga_ust": round(ust, 4)})
    gruplar = pd.DataFrame(satirlar)

    farklar = []
    for a, b in FARKLAR:
        d = dagilim[a] - dagilim[b]
        alt, ust = np.quantile(d, [alfa / 2, 1 - alfa / 2])
        farklar.append({"fark": f"{a} - {b}", "f1_farki": round(nokta[a] - nokta[b], 4),
                        "ga_alt": round(alt, 4), "ga_ust": round(ust, 4), "anlamli": bool(alt > 0 or ust < 0)})
    return gruplar, pd.DataFrame(farklar)
