"""Yazı satırı segmentasyonu: basılı çizgiler satır bantlarını verir, her bağlı bileşen ağırlık merkeziyle bir satıra atanır.

Satır k = k. çizginin üstündeki yazı (taban çizgisi çizgiye yakın). Merkez tabanlı atama, çizgiyi aşan inen
harflerin alttaki satıra karışmasını önler. Bitişik yazıda bir bileşen birden çok harf olabilir (bilinen sınırlama).
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from .masks import Masks

BAND_BELOW = 0.25  # bant, çizginin 0,25 satır aralığı altına kadar uzar


@dataclass
class Segmentation:
    comps: pd.DataFrame     # y0,y1,x0,x1,area,cy,cx,line (line = -1: bantlara düşmeyen)
    edges: np.ndarray       # satır bandı sınırları (piksel), len = çizgi sayısı + 1
    used: list              # ink içeren satır indeksleri
    labels: np.ndarray


def segment_lines(masks: Masks, min_comp_px=6, min_line_px=60):
    hw, rules = masks.hw, masks.rules
    lab, n = ndi.label(hw, structure=np.ones((3, 3)))
    rows = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        sub = lab[sl] == i
        area = int(sub.sum())
        if area < min_comp_px:
            continue
        ys, xs = np.nonzero(sub)
        rows.append(dict(id=i, y0=sl[0].start, y1=sl[0].stop, x0=sl[1].start, x1=sl[1].stop, area=area,
                         cy=float(ys.mean() + sl[0].start), cx=float(xs.mean() + sl[1].start)))
    comps = pd.DataFrame(rows, columns=["id", "y0", "y1", "x0", "x1", "area", "cy", "cx"])
    if len(rules.y) < 3 or comps.empty:
        comps["line"] = -1
        return Segmentation(comps, np.array([]), [], lab)
    sp = rules.spacing_px
    edges = np.concatenate([[rules.y[0] - sp + BAND_BELOW * sp], rules.y + BAND_BELOW * sp])
    k = np.searchsorted(edges, comps.cy.values) - 1
    comps["line"] = np.where((k >= 0) & (k < len(rules.y)), k, -1)
    ink = comps[comps.line >= 0].groupby("line").area.sum()
    used = sorted(int(k) for k, v in ink.items() if v >= min_line_px)  # çok az mürekkepli bant satır sayılmaz
    comps.loc[~comps.line.isin(used), "line"] = -1
    return Segmentation(comps, edges, used, lab)
