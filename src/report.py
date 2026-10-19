"""Bir çizim için betimleyici rapor: ölçümler ve akran yüzdelikleri (JSON + metin).

Rapor betimleyicidir: çizimi ölçer ve aynı sınıf düzeyinde, aynı görevi (mutlu/üzgün) çizen KIDO train
çizimleriyle karşılaştırır. Tanı ya da yorum dili içermez; yorum uzmana aittir.

Kullanım: python -m src.report <görüntü yolu> [--grade 3 --task mutlu] [--out <klasör>]
KIDO dosya adlarında sınıf ve görev addan okunur. Çıktı: {out}/<ad>.json ve <ad>.txt; metin ekrana da basılır.
"""
import argparse
import json
import os
import sys

from .config import PATHS
from .data import grade_from_filename, task_from_filename
from .measurements.mask import FAINT_FLAG
from .measurements.metrics import MEASURES, MEASUREMENT_VERSION, measure
from .measurements.norms import NORM_SPLIT, load_norms, norm_group, percentile, tail_shares

TASK_NAMES = {"Happiness": "mutlu", "Sadness": "üzgün"}
TASK_ARGS = {"mutlu": "Happiness", "uzgun": "Sadness"}
LOW, HIGH = 5, 95  # akranların %5'inden azı bu kadar düşük / yüksekse ⚠
FAINT_MESSAGE = "soluk renk kullanımı: ölçümler eksik olabilir"
NOTE = "Bu rapor çizimi betimler ve akranlarıyla karşılaştırır; tanı ya da yorum içermez. Yorum uzmana aittir."


def outside(values, x):
    # "alt": akranların %5'inden azı x kadar düşük ya da daha düşük; "ust": %5'inden azı x kadar yüksek ya da daha yüksek
    at_or_below, at_or_above = tail_shares(values, x)
    if at_or_below is None:
        return None
    return "alt" if at_or_below < LOW else "ust" if at_or_above < 100 - HIGH else None


def build_report(path, grade=None, emotion=None, norms=None):
    """Ortak JSON formatındaki rapor sözlüğü. grade/emotion verilmezse KIDO dosya adından okunur."""
    name = os.path.basename(path)
    grade = grade if grade is not None else grade_from_filename(name)
    emotion = emotion or task_from_filename(name)
    norms = load_norms() if norms is None else norms
    group = norm_group(norms, grade, emotion)
    if group.empty:
        raise ValueError(f"Norm grubu boş: {grade}. sınıf, {emotion}")
    values = measure(path)
    measures = []
    for key, label in MEASURES.items():
        p = percentile(group[key], values[key])
        value = values[key] if values[key] is None or key == "renk_sayisi" else round(values[key], 4)
        measures.append({"kimlik": key, "ad": label, "deger": value,
                         "yuzdelik": None if p is None else round(p, 1),
                         "aralik_disi": outside(group[key], values[key])})
    quality = [{"kimlik": "soluk_renk", "deger": round(values["soluk_renk_orani"], 5), "esik": FAINT_FLAG,
                "bayrak": bool(values["soluk_renk_bayragi"]),
                "mesaj": FAINT_MESSAGE if values["soluk_renk_bayragi"] else None}]
    return {
        "modul": "cizim",
        "surum": MEASUREMENT_VERSION,
        "kaynak": {"dosya": name},
        "karsilastirma_grubu": {"sinif": int(grade), "gorev": TASK_NAMES[emotion], "n": int(len(group)),
                                "kaynak": f"KIDO {NORM_SPLIT}"},
        "normda_mi": bool((group.dosya == name).any()),
        "olcumler": measures,
        "kalite": quality,
        "not": NOTE,
    }


def _number(x, key):
    if x is None:
        return "—"
    return str(x) if key == "renk_sayisi" else f"{x:.3f}".replace(".", ",")


def format_text(report):
    g = report["karsilastirma_grubu"]
    lines = [f"Çizim ölçümleri: {report['kaynak']['dosya']}",
             f"Karşılaştırma grubu: {g['sinif']}. sınıf, \"{g['gorev']}\" görevi ({g['kaynak']}, {g['n']} çizim)",
             ""]
    width = max(len(m["ad"]) for m in report["olcumler"])
    for m in report["olcumler"]:
        value = _number(m["deger"], m["kimlik"])
        p = m["yuzdelik"]
        if p is None:
            where = "çizim bulunamadı, karşılaştırılamadı"
        elif p < 1:
            where = "akranlarının 1. yüzdelik diliminin altında"
        elif p > 99:
            where = "akranlarının 99. yüzdelik diliminin üstünde"
        else:
            where = f"akranlarının {round(p)}. yüzdelik diliminde"
        mark = "  ⚠" if m["aralik_disi"] else ""
        lines.append(f"  {m['ad']:<{width}}  {value:>6}   {where}{mark}")
    notes = []
    if any(m["aralik_disi"] for m in report["olcumler"]):
        notes.append(f"⚠ Karşılaştırma grubunun %{LOW}'inden azı bu kadar düşük ya da yüksek bir değere sahip "
                     f"(%{LOW}–{HIGH} aralığının dışında).")
    notes += [f"Kalite: {q['mesaj']}." for q in report["kalite"] if q["bayrak"]]
    if report["normda_mi"]:
        notes.append("Not: bu çizim karşılaştırma grubunun içinde (KIDO train).")
    lines += ([""] + notes if notes else []) + ["", report["not"]]
    return "\n".join(lines)


def save(report, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(report["kaynak"]["dosya"])[0]
    with open(f"{out_dir}/{stem}.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    with open(f"{out_dir}/{stem}.txt", "w", encoding="utf-8") as f:
        f.write(format_text(report) + "\n")
    return f"{out_dir}/{stem}.json", f"{out_dir}/{stem}.txt"


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Çizim için betimleyici rapor")
    p.add_argument("path", help="görüntü yolu")
    p.add_argument("--grade", type=int, choices=range(1, 9), help="sınıf düzeyi (KIDO dosya adında yoksa)")
    p.add_argument("--task", choices=list(TASK_ARGS), help="görev (KIDO dosya adında yoksa)")
    p.add_argument("--out", default=f"{PATHS['output']}/raporlar")
    a = p.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # ⚠ Windows konsolunun cp1254'ünde yok
    r = build_report(a.path, a.grade, TASK_ARGS.get(a.task))
    paths = save(r, a.out)
    print(format_text(r))
    print(f"\nKaydedildi: {paths[0]}, {paths[1]}")
