"""Görev uyumu ve ayrışma için test metrikleri (plan: docs/plan_test_metrikleri.md).

Modele girmez: yalnız kayıtlı tahmin CSV'lerini (tahminler/{deney}_val.csv ve _test.csv) ve val normlarını okur.
Test tahminleri `python -m src.evaluation --experiment <deney> --split test` ile bir kez üretilir.

Birim öğrencidir (her öğrencinin bir mutlu, bir üzgün çizimi); bootstrap öğrencileri yeniden örnekler.
Birincil metrikler: genel AUC, d > 0 oranı, norm aktarımı. Gerisi betimleyici ve düzeltmesizdir.
Cinsiyet yalnız değerlendirme alt grubudur; skor, norm ya da rapor girdisi değildir.

Kullanım: python -m src.final_metrics [--experiment <deney>] [--n-boot 2000]
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import date

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from .config import PATHS
from .stats import DIFFERENCES, GROUPS, _macro_f1, interval, load_predictions, student_bootstrap
from .task_fit import LEVELS, MODEL_NORM_VERSION, REFERENCE, SPLIT, load_model_norms, logit, norm_group, pairs, with_task_fit

EXPECTED, TOLERANCE = 5.0, 5.0  # norm aktarımında uç payı beklentisi (%) ve izin verilen sapma (puan)
MIN_VERDICT = 100  # bundan küçük grupta norm aktarımı için hüküm verilmez
SMALL_GROUP = 30  # bundan az öğrenciyle GA "geniş" notu alır
SUBGROUPS = GROUPS + [(f"Sınıf {g}", {"sinif": g}) for g in range(1, 9)]
METRICS = ["auc", "macro_f1", "d_pos"]
TASK_NAMES = {"Happiness": "mutlu", "Sadness": "üzgün"}


def output_dir(base=PATHS["output"]):
    return f"{base}/test_metrikleri"


def load_test(experiment=REFERENCE, base=PATHS["output"]):
    path = f"{base}/tahminler/{experiment}_test.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} yok; önce bir kez: python -m src.evaluation --experiment {experiment} "
                                "--split test")
    return load_predictions(experiment, "test", base), path


def wide_table(pred):
    """Öğrenci başına bir satır: p_mutlu, p_uzgun, seviye, cinsiyet, sınıf (her öğrencinin tam iki çizimi şart)."""
    pairs(pred)  # öğrenci başına tam bir mutlu ve bir üzgün çizim değilse hata
    t = with_task_fit(pred)
    wide = t.pivot(index="ogrenci", columns="duygu", values="olasilik_uzgun")
    info = t.drop_duplicates("ogrenci").set_index("ogrenci")[["egitim", "cinsiyet", "sinif"]]
    out = info.join(wide.rename(columns={"Happiness": "p_mutlu", "Sadness": "p_uzgun"}))
    return out.reset_index()


def separation(p_sad, p_happy, score):
    return p_sad - p_happy if score == "d_olasilik" else logit(p_sad) - logit(p_happy)


def pct_in(group, x):
    """x'in group içindeki orta sıra yüzdeliği (norms.percentile ile aynı), vektörel."""
    v = np.sort(np.asarray(group, float))
    lo, hi = np.searchsorted(v, x, "left"), np.searchsorted(v, x, "right")
    return 100 * (lo + 0.5 * (hi - lo)) / len(v)


# --- İstatistikler: a = üzgün çizimlerin p'si, b = mutlu çizimlerin p'si (aynı öğrenci sırasıyla) ---------------------
def auc(a, b):
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return np.nan
    ranks = rankdata(np.concatenate([a, b]))
    return float((ranks[:n].sum() - n * (n + 1) / 2) / (n * m))


def macro_f1(a, b):
    if len(a) == 0:
        return np.nan
    counts = np.array([(b < 0.5).sum(), (b >= 0.5).sum(), (a < 0.5).sum(), (a >= 0.5).sum()], float)
    return float(_macro_f1(counts))


def share(x, test):
    """Seçilen öğeler içinde test'i sağlayanların yüzdesi; öğe yoksa nan."""
    return float(100 * test(x).mean()) if len(x) else np.nan


def norm_columns(w, norms):
    """Test öğrencilerinin val normlarındaki yüzdelikleri: pct_mutlu, pct_uzgun (görev uyumu) ve pct_d (ayrışma)."""
    score = norms.ayrisma_skoru.iloc[0]
    w = w.copy()
    w["d"] = separation(w.p_uzgun.values, w.p_mutlu.values, score)
    for col in ("pct_mutlu", "pct_uzgun", "pct_d"):
        w[col] = np.nan
    for level in LEVELS:
        m = (w.egitim == level).values
        w.loc[m, "pct_mutlu"] = pct_in(norm_group(norms, level, "Happiness"), 1 - w.p_mutlu.values[m])
        w.loc[m, "pct_uzgun"] = pct_in(norm_group(norms, level, "Sadness"), w.p_uzgun.values[m])
        w.loc[m, "pct_d"] = pct_in(norm_group(norms, level), w.d.values[m])
    return w


def transfer_cells(w):
    """Norm aktarımı hücreleri: (ölçüt, hücre, [(sütun, öğrenci maskesi), ...])."""
    level = {lv: (w.egitim == lv).values for lv in LEVELS}
    everyone = np.ones(len(w), bool)
    cells = []
    for lv in LEVELS:
        cells.append(("görev uyumu", f"{lv} | mutlu", [("pct_mutlu", level[lv])]))
        cells.append(("görev uyumu", f"{lv} | üzgün", [("pct_uzgun", level[lv])]))
    cells.append(("görev uyumu", "Genel", [("pct_mutlu", everyone), ("pct_uzgun", everyone)]))
    for lv in LEVELS:
        cells.append(("ayrışma", lv, [("pct_d", level[lv])]))
    cells.append(("ayrışma", "Genel", [("pct_d", everyone)]))
    return cells


def verdict(n, low, high):
    """Uç payı için hüküm: GA'nın tamamı beklenti + toleransın üstündeyse zayıf, tamamı altındaysa makul."""
    limit = EXPECTED + TOLERANCE
    if n < MIN_VERDICT:
        return f"hüküm yok (n<{MIN_VERDICT})"
    if low > limit:
        return "zayıf"
    return "makul" if high <= limit else "belirsiz"


def build_statistic(w, with_norms=True):
    """İdx -> {ad: değer}: genel ve alt grup metrikleri, hata yönü, alt %5, norm aktarımı payları."""
    masks = {}
    for name, filt in SUBGROUPS:
        m = np.ones(len(w), bool)
        for column, value in filt.items():
            m &= (w[column] == value).values
        masks[name] = m
    a_all, b_all = w.p_uzgun.values, w.p_mutlu.values
    cells = transfer_cells(w) if with_norms else []
    if with_norms:
        pct = {c: w[c].values for c in ("pct_mutlu", "pct_uzgun", "pct_d")}

    def statistic(idx):
        out = {}
        for name, m in masks.items():
            sel = idx[m[idx]]
            a, b = a_all[sel], b_all[sel]
            out[f"auc|{name}"] = auc(a, b)
            out[f"macro_f1|{name}"] = macro_f1(a, b)
            out[f"d_pos|{name}"] = share(a - b, lambda d: d > 0) if len(sel) else np.nan
            out[f"uyum_ort|{name}"] = float((np.mean(a) + np.mean(1 - b)) / 2) if len(sel) else np.nan
            out[f"mutlu_uzgun|{name}"] = share(b, lambda p: p >= 0.5)
            out[f"uzgun_mutlu|{name}"] = share(a, lambda p: p < 0.5)
            if with_norms:
                both = np.concatenate([pct["pct_mutlu"][sel], pct["pct_uzgun"][sel]])
                out[f"alt5|{name}"] = share(both, lambda x: x <= EXPECTED)
        for measure, cell, parts in cells:
            x = np.concatenate([pct[c][idx][m[idx]] for c, m in parts])
            x = x[~np.isnan(x)]
            out[f"alt|{measure}|{cell}"] = share(x, lambda v: v <= EXPECTED)
            out[f"ust|{measure}|{cell}"] = share(x, lambda v: v >= 100 - EXPECTED)
            out[f"alt50|{measure}|{cell}"] = share(x, lambda v: v < 50)
            out[f"n|{measure}|{cell}"] = float(len(x))
        return out

    return statistic


def run(pred, norms=None, n_boot=2000):
    w = wide_table(pred)
    if norms is not None:
        w = norm_columns(w, norms)
    point, reps = student_bootstrap(len(w), build_statistic(w, norms is not None), n_boot)
    return w, point, reps


def _ci(point, reps, key, digits=3):
    low, high = interval(reps, key)
    return round(point[key], digits), round(low, digits), round(high, digits)


def tables(w, point, reps):
    """Çıktı tabloları (DataFrame sözlüğü)."""
    out = {}
    rows = []
    for name, _ in SUBGROUPS:
        n = int(_mask(w, name).sum())
        row = {"grup": name, "n_ogrenci": n, "not": "GA geniş (n<%d)" % SMALL_GROUP if n < SMALL_GROUP else ""}
        for metric in METRICS + ["uyum_ort"]:
            v, lo, hi = _ci(point, reps, f"{metric}|{name}", 4 if metric != "d_pos" else 2)
            row.update({metric: v, f"{metric}_ga_alt": lo, f"{metric}_ga_ust": hi})
        rows.append(row)
    out["alt_gruplar"] = pd.DataFrame(rows)

    rows = []
    for name, _ in SUBGROUPS:
        row = {"grup": name}
        for key in ("mutlu_uzgun", "uzgun_mutlu"):
            v, lo, hi = _ci(point, reps, f"{key}|{name}", 1)
            row.update({f"{key}_yuzde": v, f"{key}_ga_alt": lo, f"{key}_ga_ust": hi})
        rows.append(row)
    out["hata_yonu"] = pd.DataFrame(rows)

    if "alt5|Genel" in point:
        out["alt_5"] = pd.DataFrame([{"grup": name, "alt5_yuzde": round(point[f"alt5|{name}"], 1)}
                                     for name, _ in SUBGROUPS])
        rows = []
        for measure, cell, _ in transfer_cells(w):
            n = int(point[f"n|{measure}|{cell}"])
            row = {"olcut": measure, "hucre": cell, "n": n}
            for key, label in (("alt", "alt_uc"), ("ust", "ust_uc")):
                v, lo, hi = _ci(point, reps, f"{key}|{measure}|{cell}", 1)
                row.update({f"{label}_yuzde": v, f"{label}_ga_alt": lo, f"{label}_ga_ust": hi,
                            f"{label}_hukum": verdict(n, lo, hi)})
            row["yuzdelik_50_alti_yuzde"] = round(point[f"alt50|{measure}|{cell}"], 1)
            row["yon"] = _direction(row)
            rows.append(row)
        out["norm_aktarimi"] = pd.DataFrame(rows)

    rows = []
    for a, b in DIFFERENCES:
        for metric in METRICS:
            diff = reps[f"{metric}|{a}"] - reps[f"{metric}|{b}"]
            low, high = np.nanquantile(diff, [0.025, 0.975])
            rows.append({"fark": f"{a} - {b}", "metrik": metric,
                         "deger": round(point[f"{metric}|{a}"] - point[f"{metric}|{b}"], 4),
                         "ga_alt": round(float(low), 4), "ga_ust": round(float(high), 4)})
    out["farklar"] = pd.DataFrame(rows)
    return out


def _mask(w, name):
    filt = dict(SUBGROUPS)[name]
    m = np.ones(len(w), bool)
    for column, value in filt.items():
        m &= (w[column] == value).values
    return pd.Series(m, index=w.index)


def _direction(row):
    notes = []
    if row["alt_uc_hukum"] == "zayıf":
        notes.append("alt uç beklenenden fazla: sistematik düşük skor")
    if row["ust_uc_hukum"] == "zayıf":
        notes.append("üst uç beklenenden fazla: sistematik yüksek skor")
    return "; ".join(notes)


def discrimination(val_pred, test_pred, n_boot=2000):
    """Val ve test: AUC, macro F1, d > 0 oranı (norm gerekmez); val–test AUC farkı yorumsuz."""
    rows = []
    for split, pred in (("val", val_pred), ("test", test_pred)):
        w = wide_table(pred)
        point, reps = student_bootstrap(len(w), build_statistic(w, False), n_boot)
        for metric in METRICS:
            v, lo, hi = _ci(point, reps, f"{metric}|Genel", 4)
            rows.append({"bolum": split, "metrik": metric, "deger": v, "ga_alt": lo, "ga_ust": hi,
                         "n_ogrenci": len(w)})
    table = pd.DataFrame(rows)
    pick = lambda split: float(table[(table.bolum == split) & (table.metrik == "auc")].deger.iloc[0])
    table.loc[len(table)] = {"bolum": "val - test", "metrik": "auc", "deger": round(pick("val") - pick("test"), 4),
                             "ga_alt": np.nan, "ga_ust": np.nan, "n_ogrenci": np.nan}
    return table


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main(experiment=REFERENCE, n_boot=2000, base=PATHS["output"]):
    test_pred, path = load_test(experiment, base)
    val_pred = load_predictions(experiment, SPLIT, base)
    norms = load_model_norms(f"{base}/normlar/model_normlari.csv", experiment)
    w, point, reps = run(test_pred, norms, n_boot)
    out = tables(w, point, reps)
    out["ayirt_edicilik"] = discrimination(val_pred, test_pred, n_boot)
    folder = output_dir(base)
    os.makedirs(folder, exist_ok=True)
    for name, table in out.items():
        table.to_csv(f"{folder}/{name}.csv", index=False, encoding="utf-8")
    summary = {"model": experiment, "norm_surum": MODEL_NORM_VERSION, "ayrisma_skoru": norms.ayrisma_skoru.iloc[0],
               "test_tahmin_sha256": file_hash(path), "tarih": date.today().isoformat(),
               "n_ogrenci": len(w), "n_cizim": len(test_pred), "n_boot": n_boot, "seed": 42}
    with open(f"{folder}/ozet.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return out, summary


if __name__ == "__main__":
    a = argparse.ArgumentParser(description="Görev uyumu ve ayrışma: test metrikleri (kayıtlı tahminlerden)")
    a.add_argument("--experiment", default=REFERENCE)
    a.add_argument("--n-boot", type=int, default=2000)
    args = a.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    tabs, info = main(args.experiment, args.n_boot)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    for name, table in tabs.items():
        print(f"\n== {name} ==\n{table.to_string(index=False)}")
    print(f"\nYazıldı: {output_dir()}")
