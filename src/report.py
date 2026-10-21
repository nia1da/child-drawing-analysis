"""Bir çizim için betimleyici rapor: ölçümler ve akran yüzdelikleri (JSON + metin).

Rapor betimleyicidir: çizimi ölçer ve aynı sınıf düzeyinde, aynı görevi (mutlu/üzgün) çizen KIDO train
çizimleriyle karşılaştırır. Tanı ya da yorum dili içermez; yorum uzmana aittir.

Kullanım: python -m src.report <görüntü yolu> [--grade 3 --task mutlu] [--out <klasör>]
KIDO dosya adlarında sınıf ve görev addan okunur. Çıktı: {out}/<ad>.json ve <ad>.txt; metin ekrana da basılır.
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
    return {
        "modul": "cizim",
        "surum": MEASUREMENT_VERSION,
        "kaynak": {"dosya": name},
        "karsilastirma_grubu": {"sinif": int(grade), "gorev": TASK_NAMES[emotion], "n": int(len(group)),
                                "kaynak": f"KIDO {NORM_SPLIT}", "kucuk": small},
        "normda_mi": bool((group.dosya == name).any()),
        "olcumler": measures,
        "kalite": quality,
        "not": NOTE,
    }


def _number(x, key, down=False):
    if x is None:
        return "—"
    if key in INTEGER_MEASURES:
        return str(x)
    if key.startswith("renklilik"):
        return f"{x:.1f}".replace(".", ",")
    return f"{round_down(x, 3) if down else x:.3f}".replace(".", ",")


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
        p = m["yuzdelik"]
        if p is None:
            where = "çizim bulunamadı, karşılaştırılamadı"
        elif p < 1:
            where = "akranlarının 1. yüzdelik diliminin altında"
        elif p > 99:
            where = "akranlarının 99. yüzdelik diliminin üstünde"
        else:
            where = f"akranlarının {round(p)}. yüzdelik diliminde"
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
    p.add_argument("path", nargs="?", help="görüntü yolu")
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
    if a.path is None:
        p.error("görüntü yolu gerekli")
    r = build_report(a.path, a.grade, TASK_ARGS.get(a.task))
    paths = save(r, a.out)
    print(format_text(r))
    print(f"\nKaydedildi: {paths[0]}, {paths[1]}")
