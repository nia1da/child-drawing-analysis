"""Görev uyumu ve mutlu–üzgün ayrışma: tanımlar ve val analizi (plan: docs/plan_gorev_uyumu.md, adım 2).

- Görev uyumu (çizim başına): mutlu görevinde 1 - p, üzgün görevinde p; p = modelin "üzgün" olasılığı.
- Ayrışma (öğrenci başına): d = s(üzgün çizim) - s(mutlu çizim); s olasılık ya da logit.
- Norm grubu kararı plandaki, val tahminlerinden önce yazılmış ölçütle: her hücrede (seviye x görev; ayrışmada seviye)
  sınıf düzeyleri arasında Kruskal–Wallis (p < ALPHA / hücre sayısı) ve bir sınıfın havuzdaki medyan yüzdeliğinin
  50'den en az MIN_SHIFT puan sapması. İkisi birden bir hücrede sağlanırsa "belirgin eğilim": sınıf x görev normu.

Norm dosyası {output}/normlar/model_normlari.csv: val'deki her çizim (tur=cizim, skor = görev uyumu) ve her öğrenci
çifti (tur=cift, skor = d) için bir satır; cinsiyet sütunu yok. Model ya da çıkarım dönüşümü değişirse
MODEL_NORM_VERSION artırılır, normlar yeniden üretilir.

Kullanım: python -m src.task_fit [--experiment <deney>] [--write-norms]
(val tahminleri: python -m src.evaluation --split val)
"""
import argparse
import os
import sys
from functools import lru_cache

import numpy as np
import pandas as pd
from scipy.stats import kruskal, rankdata

from .config import PATHS
from .data import grade_from_filename
from .measurements.norms import percentile
from .stats import load_predictions

REFERENCE = "convnext_tiny_320px_lr0.0001_ls0.1_s42"
SPLIT = "val"
LEVELS = ["Primary", "Secondary"]
TASKS = ["Happiness", "Sadness"]
ALPHA, MIN_SHIFT = 0.05, 10
# d için logit, val çiftlerinin bu oranından fazlasında iki skor da aynı uçtaysa (ikisi de < LOW ya da > HIGH)
SATURATION_SHARE, SATURATION_LOW, SATURATION_HIGH = 0.25, 0.1, 0.9
EPS = 1e-6  # logit için olasılık [EPS, 1 - EPS]'e kırpılır
MODEL_NORM_VERSION = 1  # model ya da çıkarım dönüşümü (320px, beyaz pad) değişirse artır


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


def norms_path(output_dir=PATHS["output"]):
    return f"{output_dir}/normlar/model_normlari.csv"


def build_model_norms(experiment=REFERENCE, output_dir=PATHS["output"]):
    """Val tahminlerinden norm tablosunu üretir ve yazar. Ayrışma skoru ölçüte göre seçilir (`separation_score`)."""
    pred = load_predictions(experiment, SPLIT)
    t = with_task_fit(pred)
    pt = pairs(pred)
    score = separation_score(pt)
    single = pd.DataFrame({"tur": "cizim", "dosya": t.dosya, "ogrenci": t.ogrenci, "sinif": t.sinif,
                           "egitim": t.egitim, "gorev": t.duygu, "skor": t.gorev_uyumu,
                           "olasilik_uzgun": t.olasilik_uzgun})
    paired = pd.DataFrame({"tur": "cift", "dosya": "", "ogrenci": pt.ogrenci, "sinif": pt.sinif,
                           "egitim": pt.egitim, "gorev": "", "skor": pt[score], "olasilik_uzgun": np.nan})
    norms = pd.concat([single, paired], ignore_index=True)
    norms["ayrisma_skoru"] = score
    norms["model"] = experiment
    norms["surum"] = MODEL_NORM_VERSION
    path = norms_path(output_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    norms.to_csv(path, index=False)
    return norms


def load_model_norms(path=None, experiment=REFERENCE):
    norms = pd.read_csv(path or norms_path(), keep_default_na=False, na_values=[""])
    if set(norms.surum.unique()) != {MODEL_NORM_VERSION} or set(norms.model.unique()) != {experiment}:
        raise RuntimeError(f"Model normları sürüm {set(norms.surum.unique())} / model {set(norms.model.unique())}, "
                           f"kod {MODEL_NORM_VERSION} / {experiment}: normları yeniden üret "
                           "(python -m src.task_fit --write-norms).")
    return norms


def norm_group(norms, level, task=None):
    """Karşılaştırma grubu: görev uyumu için (seviye, görev), ayrışma için (seviye). Skorlar dizi olarak."""
    if task is None:
        return norms[(norms.tur == "cift") & (norms.egitim == level)].skor.values
    return norms[(norms.tur == "cizim") & (norms.egitim == level) & (norms.gorev == task)].skor.values


# --- Rapor: tek görüntü için skor, yüzdelik ve ayrışma ---------------------------------------------------------------
LEVEL_NAMES = {"Primary": "ilkokul (1–4. sınıf)", "Secondary": "ortaokul (5–8. sınıf)"}
TASK_NAMES = {"Happiness": "mutlu", "Sadness": "üzgün"}
# Her raporda aynı, koşulsuz (plan: "Rapor dili ve sınırlamalar"); cinsiyete göre koşullu gösterilmez
LIMITATIONS = [
    "Görev uyumu, çizimin KIDO'daki aynı görev çizimlerine modelce benzerliğidir; çocuğun duygu durumunu "
    "göstermez.",
    "Üst dilimlerde skorlar birbirine çok yakın (50.–95. dilim arası 0,03–0,06 olasılık farkı); küçük yüzdelik "
    "farkları anlamlı okunmamalı.",
    "Model ilkokul erkek çocukların mutlu çizimlerini daha sık \"üzgün\" görevine benzetir (448px modelde test: "
    "%33,7); bu gruptaki çocuklarda düşük görev uyumu ve düşük ayrışma daha sık beklenir.",
    "Seyrek ya da az renkli çizimlerde görev uyumu düşebilir; doluluk ve renk sayısıyla birlikte okunmalı.",
    "Normlar KIDO (Şanlıurfa, 1–8. sınıf) val bölümünden; başka bir örneklemde dağılım farklı olabilir.",
    "Bu ölçümlerde ⚠ verilmez.",
]


def level_from_grade(grade):
    return "Primary" if int(grade) <= 4 else "Secondary"


def kido_split(name):
    """KIDO dosya adının bölümü (train/val/test); metadata yoksa ya da dosya orada değilse None."""
    try:
        meta = pd.read_csv(PATHS["metadata"], usecols=["dosya", "bolum"], encoding="utf-8")
    except (OSError, ValueError, KeyError):
        return None
    hit = meta.bolum[meta.dosya == name]
    return hit.iloc[0] if len(hit) else None


@lru_cache(maxsize=2)
def _load_model(experiment, output_dir):
    import torch
    from .evaluation import parse_experiment
    from .training import build_model, device
    name, size = parse_experiment(experiment)
    model = build_model(name, pretrained=False)
    model.load_state_dict(torch.load(f"{output_dir}/{experiment}.pt", map_location=device))
    return model.eval(), size


def score_image(path, experiment=REFERENCE, output_dir=PATHS["output"]):
    """Modelin "üzgün" olasılığı (p); değerlendirmedeki dönüşümle (beyaz pad ile kare). CPU'da da çalışır."""
    import torch
    from PIL import Image
    from .data import LABELS, build_transforms
    from .training import device
    model, size = _load_model(experiment, output_dir)
    _, eval_tf = build_transforms(size)
    x = eval_tf(Image.open(path)).unsqueeze(0).to(device)
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.float16, enabled=device == "cuda"):
        return float(model(x).float().softmax(1)[0, LABELS["Sadness"]])


def model_section(task, level, p_sad, norms, name=None, experiment=REFERENCE):
    """Rapor JSON'unun `model_olcumleri` bölümü (tek çizim). task: Happiness / Sadness."""
    fit = float(p_sad if task == "Sadness" else 1 - p_sad)
    group = norm_group(norms, level, task)
    pct = percentile(group, fit)
    notes = []
    split = kido_split(name) if name else None
    if split == "train":
        notes.append("Çizim modelin eğitim verisinde; skor iyimser olabilir.")
    elif split == SPLIT:
        notes.append("Çizim karşılaştırma grubunun içinde (KIDO val).")
    return {"durum": "tamam", "model": experiment, "norm_surum": MODEL_NORM_VERSION,
            "gorev_uyumu": {"gorev": TASK_NAMES[task], "deger": round(fit, 3), "olasilik_uzgun": round(float(p_sad), 4),
                            "yuzdelik": None if pct is None else round(pct, 1)},
            "karsilastirma_grubu": {"seviye": level, "ad": LEVEL_NAMES[level], "gorev": TASK_NAMES[task],
                                    "n": int(len(group)), "kaynak": "KIDO val"},
            "notlar": notes, "sinirlamalar": LIMITATIONS}


def failed_section(reason, experiment=REFERENCE):
    return {"durum": "çalışmadı", "neden": str(reason), "model": experiment, "notlar": [], "sinirlamalar": []}


def separation_section(p_happy, p_sad, level, norms, experiment=REFERENCE):
    """Aynı çocuğun iki çizimi: d = s(üzgün çizim) - s(mutlu çizim); skor türü normlardaki `ayrisma_skoru`."""
    score = norms.ayrisma_skoru.iloc[0]
    d = float(p_sad - p_happy) if score == "d_olasilik" else float(logit(p_sad) - logit(p_happy))
    group = norm_group(norms, level)
    pct = percentile(group, d)
    return {"durum": "tamam", "model": experiment, "norm_surum": MODEL_NORM_VERSION, "skor": score,
            "d": round(d, 3), "yon": "uygun" if d > 0 else "ters",
            "yuzdelik": None if pct is None else round(pct, 1),
            "karsilastirma_grubu": {"seviye": level, "ad": LEVEL_NAMES[level], "n": int(len(group)),
                                    "kaynak": "KIDO val"},
            "sinirlamalar": LIMITATIONS}


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
    a.add_argument("--write-norms", action="store_true", help="Val'den norm dosyasını (Drive normlar/) yaz")
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
    if args.write_norms:
        norms = build_model_norms(args.experiment)
        print(f"\nNorm dosyası yazıldı: {norms_path()} ({(norms.tur == 'cizim').sum()} çizim, "
              f"{(norms.tur == 'cift').sum()} çift)")
