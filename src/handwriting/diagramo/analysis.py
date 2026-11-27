"""Özellik tablosu, koordinat doğrulaması, hedef dağılımları ve özellik–HLS ilişki analizi (yalnız train bölümünde).

Hedefler: `layout` (sayfa düzeni), `letter` (harf biçimi), `alter` (düzeltmeler); HLS toplamı/okunabilirlik/çaba kullanılmaz.
İstatistik ilkeleri: aynı çocuğun iki kaydı (dikte + kopya) ayrı ailelerde analiz edilir (her çocuk bir ailede bir kez); okul (aynı kurumdan çocuklar) kümelenmesi için
okul-küme bootstrap güven aralığı ve okul-içi (okul ortalaması çıkarılmış) korelasyon; karıştırıcılar (sınıf, yaş, cinsiyet, görev sürümü) için kısmi korelasyon; çoklu karşılaştırma: Benjamini–Hochberg.
"""
import numpy as np
import pandas as pd
from scipy import stats

from .io import ROOT, SVC_DIR, read_svc
from .render import split_strokes

TARGETS = ["layout", "letter", "alter"]
COVARS = ["class", "age", "sex_female", "grade_ver"]
EXCLUDE_FEATS = {"ok", "error", "image", "n_lines_ok"}
# kenar boşluğu özellikleri: kâğıdın tablet üzerindeki konumu bilinmiyor (güvenilirlik sınırlı)
LAYOUT_ABS = ["left_margin_tb", "right_margin_tb", "top_margin_tb", "bottom_margin_tb", "left_margin_raw_tb", "bottom_margin_raw_tb"]


def load_table():
    m = pd.read_csv(ROOT / "manifests" / "images.csv", encoding="utf-8")
    ft = pd.read_csv(ROOT / "manifests" / "features_tablet.csv", encoding="utf-8").drop(columns=["ok"], errors="ignore")
    fc = pd.read_csv(ROOT / "manifests" / "features_crop.csv", encoding="utf-8").drop(columns=["ok"], errors="ignore")
    fc = fc.add_prefix("crop_").rename(columns={"crop_image": "image"})
    sp = pd.read_csv(ROOT / "manifests" / "splits.csv", encoding="utf-8")[["pid", "bolum"]]
    d = m.merge(ft, on="image", how="left").merge(fc, on="image", how="left").merge(sp, on="pid", how="left")
    d["school"] = d.id_school_ppp.fillna("school_na")
    d["is_copy"] = (d.family == "copy").astype(int)
    return d


def feature_columns(d):
    skip = EXCLUDE_FEATS | {c for c in d if c.startswith("coord_") or c.startswith("crop_")}
    cols = [c for c in ft_cols(d) if c not in skip]
    return [c for c in cols if d[c].notna().mean() > 0.9 and d[c].nunique() > 5]


def ft_cols(d):
    base = pd.read_csv(ROOT / "manifests" / "features_tablet.csv", nrows=1, encoding="utf-8").columns
    return [c for c in base if c in d.columns and c != "ok"]


# ---------------------------------------------------------------- koordinat doğrulaması
def _coord_row(path):
    from .geom import coord_lines
    return coord_lines(split_strokes(read_svc(SVC_DIR / path)))


def coordinate_validation(d, workers=4):
    """Görüntüden hesaplanan özellikleri, aynı kayıtların koordinatlarından doğrudan hesaplananlarla karşılaştırır (mutlak hata ve korelasyon)."""
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(workers) as ex:
        cl = pd.DataFrame(list(ex.map(_coord_row, d.path.tolist(), chunksize=8)))
    v = d.reset_index(drop=True).join(cl)
    out = {}
    pairs = {"yazı kutusu genişliği (tb)": (v.bbox_w_tb, v.coord_x1 - v.coord_x0), "yazı kutusu yüksekliği (tb)": (v.bbox_h_tb, v.coord_y1 - v.coord_y0),
             "sol kenar (tb)": (v.left_margin_raw_tb, v.coord_x0), "iskelet uzunluğu / koordinat yol uzunluğu": (v.skel_len_tb, v.coord_path_len),
             "satır sayısı": (v.n_lines, v.coord_n_lines), "satır aralığı (tb)": (v.pitch_tb, v.coord_pitch_tb)}
    for k, (a, b) in pairs.items():
        e = (a - b)
        out[k] = dict(n=int(len(e)), mae=float(e.abs().mean()), median_err=float(e.median()), spearman=float(stats.spearmanr(a, b, nan_policy="omit")[0]),
                      ratio_median=float((a / b).median()) if "iskelet" in k else None)
    out["satır sayısı eşit oranı"] = float((v.n_lines == v.coord_n_lines).mean())
    out["satır sayısı ±1 oranı"] = float(((v.n_lines - v.coord_n_lines).abs() <= 1).mean())
    return pd.DataFrame(out).T, v


# ---------------------------------------------------------------- hedef özeti
def target_summary(d):
    rows = []
    for fam, g in d.groupby("family"):
        for t in TARGETS:
            s = g[t]
            rows.append(dict(aile=fam, hedef=t, n_gecerli=int(s.notna().sum()), n_eksik=int(s.isna().sum()), **{f"d{k}": int((s == k).sum()) for k in range(1, 6)},
                             ort=round(float(s.mean()), 2), medyan=float(s.median())))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- ilişki analizi
def _ranks(x):
    return stats.rankdata(np.asarray(x, float))


def _resid(y, Z):
    Z = np.c_[np.ones(len(y)), Z]
    b, *_ = np.linalg.lstsq(Z, y, rcond=None)
    return y - Z @ b


def partial_spearman(x, y, Z):
    """Kısmi Spearman: x, y ve karıştırıcıların hepsi sıralanır, sıralar üzerinde kısmi Pearson."""
    Z = np.asarray(Z, float)
    Zr = np.column_stack([_ranks(Z[:, j]) for j in range(Z.shape[1])])
    rx, ry = _ranks(x), _ranks(y)
    return float(np.corrcoef(_resid(rx, Zr), _resid(ry, Zr))[0, 1])


def within_group_spearman(x, y, g):
    """Grup (okul) ortalaması çıkarılmış sıra korelasyonu; tek kayıtlı gruplar atılır."""
    df = pd.DataFrame({"x": _ranks(x), "y": _ranks(y), "g": np.asarray(g)})
    df = df[df.groupby("g").g.transform("size") >= 2]
    if len(df) < 10:
        return np.nan
    df["x"] -= df.groupby("g").x.transform("mean"); df["y"] -= df.groupby("g").y.transform("mean")
    return float(np.corrcoef(df.x, df.y)[0, 1])


def cluster_bootstrap_ci(x, y, clusters, reps=1000, seed=0):
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"x": x, "y": y, "c": clusters}).dropna()
    groups = [g[["x", "y"]].values for _, g in df.groupby("c")]
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, len(groups), len(groups))
        a = np.vstack([groups[i] for i in pick])
        if np.ptp(a[:, 0]) > 0 and np.ptp(a[:, 1]) > 0:
            vals.append(stats.spearmanr(a[:, 0], a[:, 1])[0])
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))) if vals else (np.nan, np.nan)


def bh(p):
    p = np.asarray(p, float); n = len(p); o = np.argsort(p)
    q = np.empty(n); q[o] = np.minimum.accumulate((p[o] * n / (np.arange(n) + 1))[::-1])[::-1]
    return np.minimum(q, 1.0)


def association_table(d, feats, reps=500):
    """d: yalnız train satırları. Her (aile, özellik, hedef) için Spearman ρ, ρ²; çocuk-düzeyi Fisher GA; okul-küme bootstrap GA; kısmi ρ (sınıf, yaş, cinsiyet, sürüm);
    okul-içi ρ; p ve BH q (tüm testler birlikte)."""
    rows = []
    for fam, g in d.groupby("family"):
        Z = g[COVARS].apply(pd.to_numeric, errors="coerce")
        for f in feats:
            for t in TARGETS:
                m = g[f].notna() & g[t].notna() & Z.notna().all(axis=1)
                if m.sum() < 30 or g.loc[m, f].nunique() < 3:
                    continue
                x, y = g.loc[m, f].values, g.loc[m, t].values
                rho, p = stats.spearmanr(x, y)
                n = int(m.sum()); z = np.arctanh(rho); se = 1.06 / np.sqrt(n - 3)    # Spearman için Fieller yaklaşık SE
                lo, hi = cluster_bootstrap_ci(x, y, g.loc[m, "school"].values, reps=reps)
                rows.append(dict(aile=fam, ozellik=f, hedef=t, n=n, rho=rho, rho2=rho ** 2, ci_cocuk_lo=np.tanh(z - 1.96 * se), ci_cocuk_hi=np.tanh(z + 1.96 * se), ci_okul_lo=lo, ci_okul_hi=hi,
                                 kismi_rho=partial_spearman(x, y, Z[m].values), okul_ici_rho=within_group_spearman(x, y, g.loc[m, "school"].values), p=p))
    r = pd.DataFrame(rows)
    r["q"] = bh(r.p.values)
    return r


def redundancy_clusters(d, feats, thr=0.85):
    """Spearman |ρ| > thr olan özellikler aynı kümede (ortalama bağlantılı hiyerarşik küme)."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    C = d[feats].corr(method="spearman").fillna(0).abs().values
    dist = 1 - C; np.fill_diagonal(dist, 0)
    lab = fcluster(linkage(squareform(dist, checks=False), "average"), t=1 - thr, criterion="distance")
    return pd.Series(lab, index=feats), pd.DataFrame(C, index=feats, columns=feats)


def select_features(d, feats, q_thr=0.10, reps=0):
    """Özellik seçimi (yalnız verilen eğitim satırlarında): bir özellik, en az bir hedefte en az bir ailede BH q < q_thr ve iki ailede işaret uyumluysa 'ilişkili';
    aynı yedeklilik kümesinden (|ρ| > 0.85) hedefle en güçlü ilişkili temsilci seçilir. Döner: {hedef: [özellikler]}."""
    r = association_table(d, feats, reps=reps) if reps else _assoc_fast(d, feats)
    clusters, _ = redundancy_clusters(d, feats)
    out = {}
    for t in TARGETS:
        rt = r[r.hedef == t]
        piv = rt.pivot(index="ozellik", columns="aile", values="rho")
        qmin = rt.groupby("ozellik").q.min()
        ok = [f for f in piv.index if qmin[f] < q_thr and (piv.loc[f].isna().any() or np.sign(piv.loc[f]).nunique() == 1)]
        strength = rt.groupby("ozellik").rho.apply(lambda s: s.abs().max())
        reps_ = []
        for c in sorted({clusters[f] for f in ok}):
            members = [f for f in ok if clusters[f] == c]
            reps_.append(max(members, key=lambda f: strength[f]))
        out[t] = sorted(reps_)
    return out


def _assoc_fast(d, feats):
    """Bootstrap'sız hızlı sürüm (çapraz doğrulama içi özellik seçimi için)."""
    rows = []
    for fam, g in d.groupby("family"):
        for f in feats:
            for t in TARGETS:
                m = g[f].notna() & g[t].notna()
                if m.sum() < 30 or g.loc[m, f].nunique() < 3:
                    continue
                rho, p = stats.spearmanr(g.loc[m, f], g.loc[m, t])
                rows.append(dict(aile=fam, ozellik=f, hedef=t, rho=rho, p=p))
    r = pd.DataFrame(rows); r["q"] = bh(r.p.values)
    return r


def covariate_table(d):
    """Hedefler ile karıştırıcılar arasındaki ilişki (train, aileye göre)."""
    rows = []
    for fam, g in d.groupby("family"):
        for t in TARGETS:
            for c in COVARS + ["group", "site_type_ppp"]:
                m = g[t].notna() & g[c].notna()
                if m.sum() > 20:
                    rho, p = stats.spearmanr(g.loc[m, c], g.loc[m, t]); rows.append(dict(aile=fam, hedef=t, degisken=c, rho=round(rho, 3), p=round(p, 4), n=int(m.sum())))
            m = g[t].notna()
            groups = [x[t].values for _, x in g[m].groupby("school") if len(x) >= 3]
            if len(groups) > 3:
                H, p = stats.kruskal(*groups); rows.append(dict(aile=fam, hedef=t, degisken="school (Kruskal)", rho=np.nan, p=round(p, 4), n=int(sum(len(x) for x in groups))))
    return pd.DataFrame(rows)
