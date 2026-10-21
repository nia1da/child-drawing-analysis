"""Bir çizim için betimleyici rapor: ölçümler ve akran yüzdelikleri (JSON + metin).

Rapor betimleyicidir: çizimi ölçer ve aynı sınıf düzeyinde, aynı görevi (mutlu/üzgün) çizen KIDO train
çizimleriyle karşılaştırır. Tanı ya da yorum dili içermez; yorum uzmana aittir.

Kullanım: python -m src.report <görüntü yolu> [--grade 3 --task mutlu] [--out <klasör>]
          python -m src.report <mutlu çizim> <üzgün çizim>   (aynı çocuk: ayrışma da hesaplanır)
KIDO dosya adlarında sınıf ve görev addan okunur. Çıktı: {out}/<ad>.json ve <ad>.txt; metin ekrana da basılır.
İki görüntüde ayrıca {out}/<öğrenci>_cift.json ve .txt (ayrışma). Model tabanlı bölüm (görev uyumu, ayrışma):
docs/olcumler.md; model ya da norm dosyası yoksa bölüm "çalışmadı" olur, ölçüm raporu yine çıkar.
JSON bütün ölçümleri içerir; metin rapor sadece TEXT_MEASURES'ı (bu sırayla) gösterir.
Karşılaştırma grubu MIN_GROUP'tan küçükse ⚠ verilmez, yerine "karşılaştırma grubu küçük" notu düşer.
Doluluk MIN_FILL'in altındaysa SMALL_DRAWING_MEASURES'a ⚠ verilmez; metinde bu satırlar "*" ile işaretlenir.
Küme kuralı ve tablosu: python -m src.report --small-drawing-table (docs/olcumler.md).
"""
import argparse
import json
import math
import os
import sys

import pandas as pd

from . import task_fit
from .config import PATHS
from .data import grade_from_filename, task_from_filename
from .measurements.mask import FAINT_FLAG
from .measurements.metrics import (INTEGER_MEASURES, MEASURE_INFO, MEASUREMENT_VERSION, SMALL_DRAWING_CANDIDATES,
                                   measure)
from .measurements.norms import NORM_SPLIT, load_norms, norm_group, percentile, tail_shares

TASK_NAMES = {"Happiness": "mutlu", "Sadness": "üzgün"}
TASK_ARGS = {"mutlu": "Happiness", "uzgun": "Sadness"}
LOW, HIGH = 5, 95  # akranların %5'inden azı bu kadar düşük / yüksekse ⚠
MIN_GROUP = 100  # bundan küçük karşılaştırma grubunda %5'lik kuyruk birkaç çizime dayanır: ⚠ verilmez
# Doluluk bunun altındaysa (≈ 5350 piksel; train'in en düşük %1,2'si, 93 çizim) SMALL_DRAWING_MEASURES'a ⚠ verilmez.
# Belirgin bir kırılma yok, eşik bir uzlaşım.
MIN_FILL = 0.03
# Küme kuralı: adaylardan (metrics.SMALL_DRAWING_CANDIDATES), doluluk < MIN_FILL olan train çizimlerinde %5-95 dışı
# oranı (⚠ kuralıyla) doluluk > LARGE_FILL olanlardakinin en az SMALL_FACTOR katı olanlar. Bir kez hesaplanıp
# sabitlendi (2026-10-21, sürüm 3 normları); renk entropisi kurala göre dışarıda (%7,5 / %7,1).
LARGE_FILL, SMALL_FACTOR = 0.1, 2
SMALL_DRAWING_MEASURES = {"renk_sayisi", "ortalama_doygunluk", "koyu_ton_orani", "sicak_ton_payi", "renklilik_cizim",
                          "boyama_orani", "kenar_yogunlugu_cizim", "cizgi_kalinligi"}
# Metin raporda görünen ölçümler ve sırası (JSON'da hepsi var); ad farklıysa ikinci eleman
TEXT_MEASURES = {
    "doluluk_orani": None,
    "renk_sayisi": None,
    "renklilik_cizim": "Renklilik",
    "koyu_ton_orani": None,
    "kenar_yogunlugu_cizim": "Detay (kenar yoğunluğu)",
}
FAINT_MESSAGE = "soluk renk kullanımı: ölçümler eksik olabilir"
SMALL_DRAWING_MESSAGE = "çizim çok küçük, bu ölçümler güvenilir değil"
NOTE = "Bu rapor çizimi betimler ve akranlarıyla karşılaştırır; tanı ya da yorum içermez. Yorum uzmana aittir."


def outside(values, x):
    # "alt": akranların %5'inden azı x kadar düşük ya da daha düşük; "ust": %5'inden azı x kadar yüksek ya da daha yüksek
    at_or_below, at_or_above = tail_shares(values, x)
    if at_or_below is None:
        return None
    return "alt" if at_or_below < LOW else "ust" if at_or_above < 100 - HIGH else None


def round_down(x, digits):
    # Eşiğin altındaki doluluk yuvarlanınca eşiğe çıkmasın (0,02996 -> 0,0299; "0,030 ama küçük" görünmesin)
    # round(…, 6): kayan nokta 0.0029 * 10**4'ü 28.999…'a düşürmesin
    return math.floor(round(x * 10 ** digits, 6)) / 10 ** digits


def small_drawing_table(norms, candidates=SMALL_DRAWING_CANDIDATES):
    """Her ölçüm için küçük (doluluk < MIN_FILL) ve büyük (> LARGE_FILL) train çizimlerinde ⚠ oranı (%) ve karar.

    Her çizim kendi sınıf x görev grubunda, rapordaki outside() kuralıyla değerlendirilir. Karar sadece adaylarda.
    """
    rows = []
    for key in MEASURE_INFO:
        flags = {}
        for _, g in norms.groupby(["sinif", "duygu"]):
            values = g[key].dropna()
            flags.update({i: outside(values, x) is not None for i, x in values.items()})
        flags = pd.Series(flags, dtype=float).reindex(norms.index)
        small, large = flags[norms.doluluk_orani < MIN_FILL], flags[norms.doluluk_orani > LARGE_FILL]
        s, l = 100 * small.mean(), 100 * large.mean()
        rows.append({"olcum": key, "kucuk_n": int(small.count()), "kucuk_oran": round(s, 1),
                     "buyuk_n": int(large.count()), "buyuk_oran": round(l, 1),
                     "karar": ("kümede" if s >= SMALL_FACTOR * l else "dışarıda") if key in candidates else "aday değil"})
    return pd.DataFrame(rows)


def build_report(path, grade=None, emotion=None, norms=None, model_norms=None, p_sad=None):
    """Ortak JSON formatındaki rapor sözlüğü. grade/emotion verilmezse KIDO dosya adından okunur.

    model_norms verilirse `model_olcumleri` bölümü eklenir (p_sad verilmezse model çalıştırılır; hata olursa
    bölüm "çalışmadı" olur, ölçümler etkilenmez)."""
    name = os.path.basename(path)
    grade = grade if grade is not None else grade_from_filename(name)
    emotion = emotion or task_from_filename(name)
    norms = load_norms() if norms is None else norms
    group = norm_group(norms, grade, emotion)
    if group.empty:
        raise ValueError(f"Norm grubu boş: {grade}. sınıf, {emotion}")
    values = measure(path)
    small = len(group) < MIN_GROUP
    tiny = values["doluluk_orani"] < MIN_FILL
    affected = sorted(SMALL_DRAWING_MEASURES) if tiny else []
    measures = []
    for key, (kind, label) in MEASURE_INFO.items():
        x = values[key]
        p = percentile(group[key], x)
        value = x if x is None or key in INTEGER_MEASURES else (
            round_down(x, 4) if tiny and key == "doluluk_orani" else round(x, 4))
        measures.append({"kimlik": key, "grup": kind, "ad": label, "deger": value,
                         "yuzdelik": None if p is None else round(p, 1),
                         "aralik_disi": None if small or key in affected else outside(group[key], x)})
    quality = [{"kimlik": "soluk_renk", "deger": round(values["soluk_renk_orani"], 5), "esik": FAINT_FLAG,
                "bayrak": bool(values["soluk_renk_bayragi"]),
                "mesaj": FAINT_MESSAGE if values["soluk_renk_bayragi"] else None, "etkilenen": []},
               {"kimlik": "kucuk_cizim", "deger": float(values["doluluk_orani"]), "esik": MIN_FILL,
                "bayrak": bool(tiny), "mesaj": SMALL_DRAWING_MESSAGE if tiny else None, "etkilenen": affected}]
    report = {
        "modul": "cizim",
        "surum": MEASUREMENT_VERSION,
        "kaynak": {"dosya": name},
        "karsilastirma_grubu": {"sinif": int(grade), "gorev": TASK_NAMES[emotion], "n": int(len(group)),
                                "kaynak": f"KIDO {NORM_SPLIT}", "kucuk": small},
        "normda_mi": bool((group.dosya == name).any()),
        "olcumler": measures,
        "kalite": quality,
    }
    if model_norms is not None:
        report["model_olcumleri"] = model_part(path, grade, emotion, model_norms, p_sad)
    report["not"] = NOTE
    return report


def model_part(path, grade, emotion, model_norms, p_sad=None):
    try:
        if p_sad is None:
            p_sad = task_fit.score_image(path)
        return task_fit.model_section(emotion, task_fit.level_from_grade(grade), p_sad, model_norms,
                                      os.path.basename(path))
    except Exception as e:  # torch ya da .pt yoksa, norm grubu boşsa: ölçüm raporu yine çıksın
        return task_fit.failed_section(f"{type(e).__name__}: {e}")


def build_pair_report(happy_path, sad_path, model_norms, p_happy=None, p_sad=None):
    """Aynı çocuğun mutlu ve üzgün çizimi: ayrışma. Sınıf KIDO dosya adlarından (aynı olmalı)."""
    names = [os.path.basename(happy_path), os.path.basename(sad_path)]
    students = {"-".join(n.split("-")[:3]) for n in names}
    grades = {grade_from_filename(n) for n in names}
    if len(students) != 1 or len(grades) != 1:
        raise ValueError(f"İki çizim aynı çocuğa ait olmalı (öğrenci {sorted(students)}, sınıf {sorted(grades)})")
    if task_from_filename(names[0]) != "Happiness" or task_from_filename(names[1]) != "Sadness":
        raise ValueError("Sırayla bir mutlu, bir üzgün çizim ver")
    try:
        if model_norms is None:
            raise RuntimeError("model normları yok")
        p_happy = task_fit.score_image(happy_path) if p_happy is None else p_happy
        p_sad = task_fit.score_image(sad_path) if p_sad is None else p_sad
        sep = task_fit.separation_section(p_happy, p_sad, task_fit.level_from_grade(grades.pop()), model_norms, names)
    except Exception as e:
        sep = task_fit.failed_section(f"{type(e).__name__}: {e}")
    return {"modul": "cizim_cift", "kaynak": {"dosyalar": names}, "ayrisma": sep, "not": NOTE}


def _number(x, key, down=False):
    if x is None:
        return "—"
    if key in INTEGER_MEASURES:
        return str(x)
    if key.startswith("renklilik"):
        return f"{x:.1f}".replace(".", ",")
    return f"{round_down(x, 3) if down else x:.3f}".replace(".", ",")


def percentile_text(p, who):
    if p is None:
        return "çizim bulunamadı, karşılaştırılamadı"
    if p < 1:
        return f"{who} 1. yüzdelik diliminin altında"
    if p > 99:
        return f"{who} 99. yüzdelik diliminin üstünde"
    return f"{who} {round(p)}. yüzdelik diliminde"


def model_lines(part):
    """Görev uyumu satırı ve hemen altında sınırlama notları."""
    if part["durum"] != "tamam":
        return [f"Görev uyumu: çalışmadı ({part['neden']})"]
    g, fit = part["karsilastirma_grubu"], part["gorev_uyumu"]
    lines = [f"Görev uyumu ({fit['gorev']}): modelin bu çizimi KIDO'daki \"{fit['gorev']}\" görevi çizimlerine "
             f"benzetme derecesi, {percentile_text(fit['yuzdelik'], 'karşılaştırma grubunun')}.",
             f"  Karşılaştırma grubu: {g['ad']} {g['gorev']} normu, n={g['n']} ({g['kaynak']})"]
    lines += [f"  Not: {n}" for n in part["notlar"]]
    return lines + limitation_lines(part)


def limitation_lines(part):
    return ["  Sınırlamalar:"] + [f"   - {t}" for t in part["sinirlamalar"]]


def format_text(report):
    g = report["karsilastirma_grubu"]
    lines = [f"Çizim ölçümleri: {report['kaynak']['dosya']}",
             f"Karşılaştırma grubu: {g['sinif']}. sınıf, \"{g['gorev']}\" görevi ({g['kaynak']}, {g['n']} çizim)",
             ""]
    by_key = {m["kimlik"]: m for m in report["olcumler"]}
    shown = [{**by_key[k], "ad": label or by_key[k]["ad"]} for k, label in TEXT_MEASURES.items()]
    width = max(len(m["ad"]) for m in shown)
    tiny = next(q for q in report["kalite"] if q["kimlik"] == "kucuk_cizim")
    starred = set(tiny["etkilenen"])
    for m in shown:
        value = _number(m["deger"], m["kimlik"], down=tiny["bayrak"] and m["kimlik"] == "doluluk_orani")
        where = percentile_text(m["yuzdelik"], "akranlarının")
        mark = "  ⚠" if m["aralik_disi"] else "  *" if m["kimlik"] in starred else ""
        lines.append(f"  {m['ad']:<{width}}  {value:>6}   {where}{mark}")
    notes = []
    if g["kucuk"]:
        notes.append(f"Not: karşılaştırma grubu küçük (n={g['n']}); aralık dışı işareti verilmedi.")
    elif any(m["aralik_disi"] for m in shown):
        notes.append(f"⚠ Karşılaştırma grubunun %{LOW}'inden azı bu kadar düşük ya da yüksek bir değere sahip "
                     f"(%{LOW}–{HIGH} aralığının dışında).")
    if tiny["bayrak"]:
        notes.append(f"* {tiny['mesaj']}." if any(m["kimlik"] in starred for m in shown)
                     else "Kalite: çizim çok küçük; JSON'daki bazı oransal ölçümler güvenilir değil.")
    notes += [f"Kalite: {q['mesaj']}." for q in report["kalite"] if q["bayrak"] and q is not tiny]
    if report["normda_mi"]:
        notes.append("Not: bu çizim karşılaştırma grubunun içinde (KIDO train).")
    lines += ([""] + notes if notes else [])
    if "model_olcumleri" in report:
        lines += [""] + model_lines(report["model_olcumleri"])
    lines += ["", report["not"]]
    return "\n".join(lines)


def format_pair_text(pair):
    a = pair["ayrisma"]
    head = f"Mutlu–üzgün ayrışma: {' + '.join(pair['kaynak']['dosyalar'])}"
    if a["durum"] != "tamam":
        return "\n".join([head, f"  çalışmadı ({a['neden']})", "", pair["not"]])
    g = a["karsilastirma_grubu"]
    d = f"{a['d']:.3f}".replace(".", ",")
    kind = "logit" if a["skor"] == "d_logit" else "olasılık"
    lines = [head,
             f"  Ayrışma d = {d} ({kind} farkı: üzgün çizim − mutlu çizim), "
             f"{percentile_text(a['yuzdelik'], 'karşılaştırma grubunun')}.",
             f"  Karşılaştırma grubu: {g['ad']} normu, n={g['n']} ({g['kaynak']})"]
    if a["yon"] == "ters":
        lines.append("  Model iki çizimi görevlerinin tersi yönünde sıralıyor.")
    lines += [f"  Not: {n}" for n in a["notlar"]]
    return "\n".join(lines + limitation_lines(a) + ["", pair["not"]])


def save(report, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(report["kaynak"]["dosya"])[0]
    with open(f"{out_dir}/{stem}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(f"{out_dir}/{stem}.txt", "w", encoding="utf-8") as f:
        f.write(format_text(report) + "\n")
    return f"{out_dir}/{stem}.json", f"{out_dir}/{stem}.txt"


def save_pair(pair, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stem = "-".join(pair["kaynak"]["dosyalar"][0].split("-")[:3]) + "_cift"
    with open(f"{out_dir}/{stem}.json", "w", encoding="utf-8") as f:
        json.dump(pair, f, ensure_ascii=False, indent=2)
    with open(f"{out_dir}/{stem}.txt", "w", encoding="utf-8") as f:
        f.write(format_pair_text(pair) + "\n")
    return f"{out_dir}/{stem}.json", f"{out_dir}/{stem}.txt"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Çizim için betimleyici rapor")
    p.add_argument("paths", nargs="*", help="görüntü yolu; iki yol: mutlu çizim, üzgün çizim (aynı çocuk)")
    p.add_argument("--grade", type=int, choices=range(1, 9), help="sınıf düzeyi (KIDO dosya adında yoksa)")
    p.add_argument("--task", choices=list(TASK_ARGS), help="görev (KIDO dosya adında yoksa)")
    p.add_argument("--out", default=f"{PATHS['output']}/raporlar")
    p.add_argument("--small-drawing-table", action="store_true",
                   help="küçük çizim kümesinin tablosunu train normlarından hesapla (rapor üretmez)")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # ⚠ Windows konsolunun cp1254'ünde yok
    if a.small_drawing_table:
        table = small_drawing_table(load_norms())
        print(table.to_string(index=False))
        rule = set(table.olcum[table.karar == "kümede"])
        print("\nSMALL_DRAWING_MEASURES kuralla " + ("aynı." if rule == SMALL_DRAWING_MEASURES
                                                       else f"FARKLI, kural: {sorted(rule)}"))
        sys.exit()
    if not 1 <= len(a.paths) <= 2:
        p.error("bir ya da iki görüntü yolu gerekli")
    try:
        model_norms = task_fit.load_model_norms()
    except (OSError, RuntimeError) as e:
        model_norms = None
        print(f"Uyarı: model normları yüklenemedi, görev uyumu ve ayrışma yok ({e})")
    if len(a.paths) == 2:
        if a.grade or a.task:
            p.error("iki görüntüde --grade / --task kullanılmaz (KIDO dosya adlarından okunur)")
    for path in a.paths:
        r = build_report(path, a.grade, TASK_ARGS.get(a.task), model_norms=model_norms)
        paths = save(r, a.out)
        print(format_text(r))
        print(f"\nKaydedildi: {paths[0]}, {paths[1]}\n")
    if len(a.paths) == 2:
        pair = build_pair_report(a.paths[0], a.paths[1], model_norms)
        paths = save_pair(pair, a.out)
        print(format_pair_text(pair))
        print(f"\nKaydedildi: {paths[0]}, {paths[1]}")
