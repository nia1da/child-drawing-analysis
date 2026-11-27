"""DiaGraMo deneyleri (tekrarlanabilir komutlar): `python -m src.handwriting.diagramo.experiments <komut>`.

Komutlar (hepsi yerel veriyle; çıktılar `data/handwriting/diagramo/metadata/`):
  analysis       koordinat doğrulaması + eğitim bölümünde özellik–hedef ilişkileri (association_train.csv, coord_validation.csv)
  development_a  Model A geliştirme tablosu (CV(train) + val); test kullanılmaz
  development_b  Model B (gömme) geliştirme tablosu; test kullanılmaz
  ablation       kırpma/konum özellikleri ve bayraklı kayıt duyarlılığı (geliştirme kümesi)
  render         render ayarlarına duyarlılık ve render rastgeleleştirmeli eğitim (val)
  clinical       `group`/disgrafi analizi (geliştirme kümesi; sınıflandırma kurulmaz)
  final_test     seçilen A ve B yapılandırmaları test kümesinde **bir kez** (kilit dosyası; yeniden çalışmaz)
"""
import json
import sys
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from . import analysis as A
from . import cnn as C
from . import models as M
from .io import ROOT, SVC_DIR, read_svc
from .render import render_strokes, split_strokes

META = ROOT / "metadata"
POS = ["left_margin_tb", "right_margin_tb", "top_margin_tb", "bottom_margin_tb", "left_margin_raw_tb", "bottom_margin_raw_tb", "rbbox_area_frac"]
VAL_VARIANTS = {"orijinal(3px,4ppu)": (4.0, 3), "ince(2px)": (4.0, 2), "kalin(5px)": (4.0, 5), "dusuk_coz(3ppu,2px)": (3.0, 2), "yuksek_coz(6ppu,4px)": (6.0, 4)}
TRAIN_VARIANTS = {"a": (4.0, 2), "b": (4.0, 3), "c": (4.0, 4), "d": (4.0, 5), "e": (3.0, 2), "f": (5.0, 3)}  # render rastgeleleştirme: yalnız eğitim kümesi, etiketi değiştirmez


def _save(df, name, **kw):
    df.to_csv(META / name, index=kw.pop("index", False), encoding="utf-8", lineterminator="\n")


def analysis(reps=300):
    d = A.load_table(); feats = A.feature_columns(d)
    val, _ = A.coordinate_validation(d); _save(val, "coord_validation.csv", index=True)
    r = A.association_table(d[d.bolum == "train"], feats, reps=reps); _save(r, "association_train.csv")
    return val, r


def development_a():
    d = A.load_table(); r = M.development_table(d, A.feature_columns(d)); _save(r, "model_a_development.csv"); return r


def development_b():
    d = A.load_table()
    embs = {v: C.embed(d.image.tolist(), v) for v in ("tablet", "crop")}
    r = C.development_table_emb(d, embs); _save(r, "model_b_development.csv"); return r


def ablation():
    d = A.load_table(); full = A.feature_columns(d)
    nopos = [f for f in full if f not in POS]
    crop = [c for c in d.columns if c.startswith("crop_") and c[5:] in full and c[5:] not in POS]
    dc = d.copy()
    for c in crop:
        dc[c[5:]] = d[c]
    cfgs = [c for c in M.CONFIGS if c.name in ("OL_secilen_C0.3", "RF_tum")]
    rows = []
    for label, data, fs in [("tablet_tum", d, full), ("tablet_konumsuz", d, nopos), ("crop_oznitelikleri", dc, [c[5:] for c in crop]),
                            ("bayraklilar_cikarildi", d[~d.flagged], full), ("extra_content_cikarildi", d[~d.extra_content], full)]:
        r = M.development_table(data, fs, configs=cfgs); r["set"] = label; r["n_ozellik_havuz"] = len(fs); rows.append(r)
    out = pd.concat(rows); _save(out, "model_a_ablation.csv"); return out


def _render_feats(args):
    from .geom import features_from_ink
    path, name, variants = args
    st = split_strokes(read_svc(SVC_DIR / path)); rows = []
    for v, (ppu, lp) in variants.items():
        img = render_strokes(st, px_per_mm=ppu, line_px=lp, canvas="tablet").image
        f = features_from_ink(np.asarray(img) < 128, ppu, True); f["variant"] = v; f["image"] = name; rows.append(f)
    return rows


def _feats_for(df, variants, workers=4):
    with ProcessPoolExecutor(workers) as ex:
        return pd.DataFrame([r for rr in ex.map(_render_feats, [(p, n, variants) for p, n in zip(df.path, df.image)], chunksize=4) for r in rr])


def render():
    """val çocukları farklı render ayarlarında: (a) tek render ile eğitilmiş Model A, (b) render rastgeleleştirmeli eğitim (yalnız eğitim kümesi)."""
    from scipy import stats
    d = A.load_table(); feats = A.feature_columns(d)
    tr, va = d[d.bolum == "train"], d[d.bolum == "val"]
    meta = d.set_index("image")[["is_copy", "school", "family"] + A.TARGETS]
    Fva = _feats_for(va, VAL_VARIANTS).join(meta, on="image")
    Ftr = _feats_for(tr, TRAIN_VARIANTS).join(meta, on="image")
    chosen = M.choose(pd.read_csv(META / "model_a_development.csv")); cfgs = {c.name: c for c in M.CONFIGS}
    res, rows = [], []
    for t in A.TARGETS:
        for label, train in [("tek render (3px)", tr[tr[t].notna()]), ("render rastgeleleştirme (6 varyant)", Ftr[Ftr[t].notna()])]:
            pred, _ = M.fit_model(cfgs[chosen[t]], train, t, feats)
            for v, g in Fva.groupby("variant"):
                g = g[g[t].notna()]; m = M.metrics(g[t].values, pred(g)); rows.append(dict(hedef=t, egitim=label, val_render=v, qwk=m["qwk"], mae=m["mae"]))
    R = pd.DataFrame(rows); _save(R, "render_randomization_val.csv")
    single = R[R.egitim == "tek render (3px)"].pivot(index="val_render", columns="hedef", values="qwk")
    _save(single, "render_robustness_qwk.csv", index=True)
    base = Fva[Fva.variant == "orijinal(3px,4ppu)"].set_index("image")
    st = {v: {f: stats.spearmanr(base[f], Fva[Fva.variant == v].set_index("image").loc[base.index, f], nan_policy="omit")[0] for f in feats} for v in VAL_VARIANTS if not v.startswith("orijinal")}
    S = pd.DataFrame(st); S["min"] = S.min(1); _save(S, "render_robustness_features.csv", index=True)
    return R, S


def clinical():
    """`group`/disgrafi: etiket eşdeğerliği, şehir/toplama yeri karıştırıcısı, özellik AUC'leri, karışık okullar (geliştirme kümesi; test yok)."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import GroupKFold
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from .labels import usable_participants
    d = A.load_table(); feats = A.feature_columns(d)
    sc = usable_participants()[["id_participant", "special_care_type"]].rename(columns={"id_participant": "pid"})
    dev = d[d.bolum.isin(["train", "val"])].merge(sc, on="pid", how="left"); ch = dev.drop_duplicates("pid")
    out = dict(n_cocuk=len(ch), group=ch.group.value_counts().to_dict(),
               group_x_disgrafi=pd.crosstab(ch.group, ch.special_care_type_dysgraphia).to_dict(), group_ne_disgrafi=int((ch.group != ch.special_care_type_dysgraphia).sum()),
               city1_x_group=pd.crosstab(ch.group, ch.id_city.eq("city1")).to_dict(), site_x_group=pd.crosstab(ch.group, ch.site_type_ppp).to_dict(),
               auc_sehir=float(roc_auc_score(ch.group, (~ch.id_city.eq("city1")).astype(int))))
    g = dev[dev.family == "dictation"]
    X = g[feats].values; y = g.group.values; grp = g.school.values; city = (~g.id_city.eq("city1")).astype(int).values[:, None]
    for name, XX in [("auc_cv_ozellikler", X), ("auc_cv_sehir", city)]:
        oof = np.full(len(g), np.nan)
        for tr, te in GroupKFold(5).split(XX, groups=grp):
            m = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(C=0.1, max_iter=2000)).fit(XX[tr], y[tr]); oof[te] = m.predict_proba(XX[te])[:, 1]
        out[name] = float(roc_auc_score(y, oof))
    rows = []
    for fam, gg in dev.groupby("family"):
        for f in feats:
            mm = gg[f].notna()
            rows.append(dict(aile=fam, ozellik=f, auc_group=roc_auc_score(gg.group[mm], gg[f][mm]), auc_disgrafi=roc_auc_score(gg.special_care_type_dysgraphia[mm], gg[f][mm])))
    _save(pd.DataFrame(rows), "clinical_feature_auc_dev.csv")
    return out


def final_test():
    """Seçilen A ve B yapılandırmaları (geliştirme tablolarından, önceden yazılı kuralla) test kümesinde **bir kez**; kilit dosyası yazılır."""
    if M.LOCK.exists():
        raise SystemExit("Test kümesi zaten kullanıldı (kilit dosyası var); yeniden kullanım yalnız kullanıcı kararıyla.")
    d = A.load_table(); feats = A.feature_columns(d)
    chosenA = M.choose(pd.read_csv(META / "model_a_development.csv"))
    nameB = M.choose(pd.read_csv(META / "model_b_development.csv"))
    cfgB = {t: (n.split("_")[1], int(n.split("_")[2][3:]), float(n.split("_")[3][1:])) for t, n in nameB.items()}
    embs = {v: C.embed(d.image.tolist(), v) for v in ("tablet", "crop")}
    resB, predsB = C.final_test_emb(d, embs, cfgB)          # kilit yoksa çalışır, yazmaz
    resA, predsA = M.final_test(d, feats, chosenA)          # değerlendirir ve kilidi yazar
    resA["model"] = "A (geometrik özellik)"; resB["model"] = "B (CNN gömme)"
    res = pd.concat([resA, resB]); _save(res, "final_test_results.csv")
    (META / "final_test_predictions.json").write_text(json.dumps({"A": predsA, "B": predsB}, ensure_ascii=False), encoding="utf-8")
    return res


COMMANDS = dict(analysis=analysis, development_a=development_a, development_b=development_b, ablation=ablation, render=render, clinical=clinical, final_test=final_test)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    print(COMMANDS[sys.argv[1]]())
