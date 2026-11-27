"""HLS maddeleri için ordinal tahmin: Model A (geometrik özellik tabanlı) ve ortak değerlendirme araçları.

Girdi yalnız statik görüntüden hesaplanan geometrik özellikler (+ görev türü `is_copy`). Hız, basınç, zaman, vuruş sırası, cinsiyet/yaş/sınıf girdi değildir.
Her HLS maddesi (layout, letter, alter) için ayrı model. Değerlendirme: MAE, Quadratic Weighted Kappa, Spearman, karışıklık matrisi; baseline = eğitim medyanı.
Seçim ilkesi (sonuçlardan önce yazıldı): yapılandırma, eğitim kümesinde okul-gruplu 5 katlı CV ortalama QWK'si ile val QWK'sinin ortalamasına göre seçilir;
test kümesi yalnız `final_test` ile bir kez kullanılır (kilit dosyası).
"""
import json
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import QuantileTransformer

from .analysis import TARGETS, select_features
from .io import ROOT

LABELS = [1, 2, 3, 4, 5]
LOCK = ROOT / "metadata" / "test_used.json"


class OrdinalLogit:
    """Frank–Hall ordinal lojistik: P(y > k) için K−1 L2-düzenlileştirilmiş ikili lojistik regresyon; olasılıklar monotonlaştırılır."""

    def __init__(self, C=0.3):
        self.C = C

    def fit(self, X, y):
        y = np.asarray(y)
        self.k_ = LABELS[:-1]
        self.m_, self.const_ = [], []
        for k in self.k_:
            yk = (y > k).astype(int)
            if yk.sum() < 3 or (1 - yk).sum() < 3:      # çok az örnek: sabit olasılık
                self.m_.append(None); self.const_.append(float(yk.mean()))
            else:
                self.m_.append(LogisticRegression(C=self.C, max_iter=3000).fit(X, yk)); self.const_.append(None)
        return self

    def proba(self, X):
        gt = np.column_stack([np.full(len(X), c) if m is None else m.predict_proba(X)[:, 1] for m, c in zip(self.m_, self.const_)])
        gt = np.minimum.accumulate(gt, axis=1)
        full = np.column_stack([np.ones(len(X)), gt, np.zeros(len(X))])
        return np.clip(full[:, :-1] - full[:, 1:], 0, 1)

    def predict_cont(self, X):
        return self.proba(X) @ np.array(LABELS, float)


class RFOrdinal:
    """Rastgele orman regresyonu (sıralı etiketi sayı olarak): sürekli çıktı; sınıf = yuvarlama."""

    def __init__(self, n=400, leaf=5, seed=0):
        self.m = RandomForestRegressor(n_estimators=n, min_samples_leaf=leaf, max_features=0.4, random_state=seed, n_jobs=-1)

    def fit(self, X, y):
        self.m.fit(X, y); return self

    def predict_cont(self, X):
        return self.m.predict(X)


def to_class(c):
    return np.clip(np.rint(c), 1, 5).astype(int)


def metrics(y, cont):
    y = np.asarray(y, int); p = to_class(cont)
    return dict(mae=float(np.abs(y - p).mean()), qwk=float(cohen_kappa_score(y, p, labels=LABELS, weights="quadratic")) if len(set(p)) > 1 or len(set(y)) > 1 else 0.0,
                spearman=float(stats.spearmanr(y, cont)[0]) if np.ptp(cont) > 1e-9 else np.nan, mae_cont=float(np.abs(y - cont).mean()))


def cluster_ci(y, cont, clusters, fn, reps=1000, seed=0):
    """Okul-küme bootstrap %95 GA (yüzdelik)."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"y": y, "c": cont, "g": clusters})
    gs = [g[["y", "c"]].values for _, g in df.groupby("g")]
    v = []
    for _ in range(reps):
        a = np.vstack([gs[i] for i in rng.integers(0, len(gs), len(gs))])
        if len(set(a[:, 0])) > 1:
            r = fn(a[:, 0], a[:, 1])
            if np.isfinite(r): v.append(r)
    return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if v else (np.nan, np.nan)


@dataclass
class Config:
    name: str
    model: str            # baseline | ol | rf
    feats: str = "selected"   # selected | all
    C: float = 0.3
    leaf: int = 5


CONFIGS = [Config("baseline_medyan", "baseline"), Config("OL_secilen_C0.1", "ol", "selected", 0.1), Config("OL_secilen_C0.3", "ol", "selected", 0.3), Config("OL_tum_C0.03", "ol", "all", 0.03),
           Config("RF_secilen", "rf", "selected", leaf=5), Config("RF_tum", "rf", "all", leaf=5)]


def _xmat(d, cols):
    return d[cols + ["is_copy"]].astype(float)


def fit_model(cfg: Config, train, target, feats):
    """Eğitir. Döner: (predict(df) -> sürekli tahmin, kullanılan özellikler)."""
    if cfg.model == "baseline":
        med = train.groupby("is_copy")[target].median()
        return (lambda df: df.is_copy.map(med).astype(float).values), []
    cols = select_features(train, feats)[target] if cfg.feats == "selected" else list(feats)
    if not cols:
        const = float(train[target].median())
        return (lambda df: np.full(len(df), const)), []
    pre = make_pipeline(SimpleImputer(strategy="median"), QuantileTransformer(n_quantiles=min(200, len(train)), output_distribution="normal", random_state=0))
    m = (OrdinalLogit(cfg.C) if cfg.model == "ol" else RFOrdinal(leaf=cfg.leaf)).fit(pre.fit_transform(_xmat(train, cols)), train[target].values)
    return (lambda df: m.predict_cont(pre.transform(_xmat(df, cols)))), cols


def fit_predict(cfg: Config, train, test, target, feats):
    """train/test: DataFrame. Döner: test için sürekli tahmin, kullanılan özellikler."""
    f, cols = fit_model(cfg, train, target, feats)
    return f(test), cols


def oof_predictions(cfg, train, target, feats, k=5):
    """Okul-gruplu CV dışı (out-of-fold) tahminler: belirsizlik aralığı için kalıntı dağılımı."""
    oof = np.full(len(train), np.nan)
    for tr, te in GroupKFold(k).split(train, groups=train.school):
        oof[te] = fit_predict(cfg, train.iloc[tr], train.iloc[te], target, feats)[0]
    return oof


def grouped_cv(cfg, train, target, feats, k=5):
    """Okul-gruplu CV (özellik seçimi her kat içinde): birleştirilmiş OOF tahminlerinden metrikler + kat başına QWK."""
    oof = np.full(len(train), np.nan); q = []
    for tr, te in GroupKFold(k).split(train, groups=train.school):
        a, b = train.iloc[tr], train.iloc[te]
        c, _ = fit_predict(cfg, a, b, target, feats)
        oof[te] = c; q.append(metrics(b[target].values, c)["qwk"])
    m = metrics(train[target].values, oof); m["qwk_fold_mean"] = float(np.mean(q)); m["qwk_fold_sd"] = float(np.std(q))
    return m


def development_table(d, feats, targets=TARGETS, configs=CONFIGS):
    """Her hedef x yapılandırma: CV(train) ve val (train'de eğitilip val'de) metrikleri. Test kullanılmaz."""
    tr, va = d[d.bolum == "train"], d[d.bolum == "val"]
    rows = []
    for t in targets:
        a, b = tr[tr[t].notna()], va[va[t].notna()]
        for cfg in configs:
            cv = grouped_cv(cfg, a, t, feats)
            c, cols = fit_predict(cfg, a, b, t, feats)
            v = metrics(b[t].values, c)
            rows.append(dict(hedef=t, config=cfg.name, cv_mae=cv["mae"], cv_qwk=cv["qwk"], cv_spearman=cv["spearman"], cv_qwk_fold_mean=cv["qwk_fold_mean"], cv_qwk_fold_sd=cv["qwk_fold_sd"],
                             val_mae=v["mae"], val_qwk=v["qwk"], val_spearman=v["spearman"], n_ozellik=len(cols), n_train=len(a), n_val=len(b)))
    r = pd.DataFrame(rows)
    r["secim_puani"] = (r.cv_qwk + r.val_qwk) / 2
    return r


def choose(table):
    """Hedef başına en yüksek (CV QWK + val QWK)/2 olan yapılandırma (baseline hariç değil: baseline QWK ≈ 0 olduğundan doğal olarak elenir)."""
    return {t: g.sort_values("secim_puani", ascending=False).iloc[0].config for t, g in table.groupby("hedef")}


def final_test(d, feats, chosen, force=False):
    """Seçilen yapılandırmalar train+val'de eğitilir, test kümesinde BİR KEZ değerlendirilir (kilit dosyası)."""
    if LOCK.exists() and not force:
        raise RuntimeError(f"Test kümesi zaten kullanıldı ({LOCK.name}); yeniden kullanım yalnız kullanıcı kararıyla.")
    dev, te = d[d.bolum.isin(["train", "val"])], d[d.bolum == "test"]
    cfgs = {c.name: c for c in CONFIGS}
    out, preds = [], {}
    for t, name in chosen.items():
        a, b = dev[dev[t].notna()], te[te[t].notna()]
        c, cols = fit_predict(cfgs[name], a, b, t, feats)
        base, _ = fit_predict(cfgs["baseline_medyan"], a, b, t, feats)
        m, mb = metrics(b[t].values, c), metrics(b[t].values, base)
        ci_q = cluster_ci(b[t].values, c, b.school.values, lambda y, x: metrics(y, x)["qwk"])
        ci_m = cluster_ci(b[t].values, c, b.school.values, lambda y, x: metrics(y, x)["mae"])
        out.append(dict(hedef=t, config=name, n=len(b), mae=m["mae"], mae_ci_lo=ci_m[0], mae_ci_hi=ci_m[1], qwk=m["qwk"], qwk_ci_lo=ci_q[0], qwk_ci_hi=ci_q[1], spearman=m["spearman"],
                        baseline_mae=mb["mae"], baseline_qwk=mb["qwk"], n_ozellik=len(cols)))
        preds[t] = dict(y=b[t].values.tolist(), pred=to_class(c).tolist(), cont=np.asarray(c).tolist(), images=b.image.tolist(), cm=confusion_matrix(b[t].values, to_class(c), labels=LABELS).tolist(), features=cols)
    LOCK.write_text(json.dumps({"kullanildi": True, "yapilandirmalar": chosen}, ensure_ascii=False), encoding="utf-8")
    return pd.DataFrame(out), preds
