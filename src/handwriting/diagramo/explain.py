"""Rapor için incelenebilecek bölgeler ve model tahminine katkı (occlusion) hesapları.

Bölgeler uzmanın *bakacağı yerlerdir*; bir hata ya da bozukluk işareti değildir. Katkı: bir özellik eğitim medyanına çekilince tahminin değişimi
(model bağımsız, tek özellikli müdahale); nedensel bir açıklama değil, modelin o özelliğe duyarlılığıdır.
"""
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from .geom import estimate_pitch, find_lines, line_measures, load_ink

COLORS = {"line_ok": (40, 170, 70), "line_wobble": (255, 140, 0), "blob": (220, 30, 30), "tall": (200, 0, 200), "stray": (0, 160, 220)}


def regions(ink, ppu=4.0, wobble_thr=0.10, max_each=6):
    """Satır bandı taban doğruları (dalgalanma/x-yüksekliği ≥ eşik ise işaretli), kalın (üst üste binen) bölgeler, çok uzun bileşenler, satır dışı bileşenler."""
    prof = ink.sum(1).astype(float)
    pitch = estimate_pitch(prof, ppu)
    peaks, bounds = find_lines(prof, pitch)
    lm = line_measures(ink, peaks, bounds, pitch, ppu)
    out = dict(pitch=pitch, lines=[], blobs=[], tall=[], stray=[])
    for r in lm.itertuples():
        if hasattr(r, "sl") and r.sl == r.sl:
            out["lines"].append(dict(line=int(r.line), x0=int(r.x0), x1=int(r.x1), sl=r.sl, ic=r.ic, wob=float(r.wobble / r.xh), flag=bool(r.wobble / r.xh >= wobble_thr)))
    edt = ndi.distance_transform_edt(ink)
    lab, n = ndi.label(edt >= 3.5, structure=np.ones((3, 3)))
    if n:
        area = ndi.sum(np.ones_like(lab), lab, range(1, n + 1))
        for i in np.argsort(-area)[:max_each]:
            if area[i] >= 12:
                sl = ndi.find_objects(lab)[i]; out["blobs"].append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
    lab2, n2 = ndi.label(ink, structure=np.ones((3, 3)))
    top = bounds[lm.line.min()] if len(lm) else 0
    bot = bounds[lm.line.max() + 1] if len(lm) else ink.shape[0]
    for i, sl in enumerate(ndi.find_objects(lab2)):
        h = sl[0].stop - sl[0].start
        cy = (sl[0].start + sl[0].stop) / 2
        box = (sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)
        if (lab2[sl] == i + 1).sum() < 8:
            continue
        if h > 1.2 * pitch:
            out["tall"].append(box)
        if len(lm) and not (top <= cy < bot):
            out["stray"].append(box)
    out["tall"], out["stray"] = out["tall"][:max_each], out["stray"][:max_each]
    return out


def annotate(path, out_path, ppu=4.0, pad_tb=6.0):
    """Görüntüyü bölgelerle işaretler ve yazı çevresine kırpar (yalnız gösterim için). Döner: bölge sözlüğü."""
    ink = load_ink(path)
    reg = regions(ink, ppu)
    im = Image.fromarray(np.where(ink, 20, 255).astype(np.uint8)).convert("RGB")
    d = ImageDraw.Draw(im)
    for ln in reg["lines"]:
        c = COLORS["line_wobble"] if ln["flag"] else COLORS["line_ok"]
        d.line([(ln["x0"], ln["ic"] + ln["sl"] * ln["x0"]), (ln["x1"], ln["ic"] + ln["sl"] * ln["x1"])], fill=c, width=3)
    for key in ("blobs", "tall", "stray"):
        for b in reg[key]:
            d.rectangle([b[0] - 3, b[1] - 3, b[2] + 3, b[3] + 3], outline=COLORS[{"blobs": "blob", "tall": "tall", "stray": "stray"}[key]], width=3)
    ys, xs = np.nonzero(ink)
    pad = int(pad_tb * ppu)
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad), min(im.width, xs.max() + pad), min(im.height, ys.max() + pad))
    im.crop(box).save(out_path, "PNG")
    return reg


def occlusion_contributions(predict, row, train, cols, top=3):
    """Her özellik için: o özellik eğitim medyanına çekildiğinde tahmin değişimi (pozitif = özellik tahmini yükseltiyor). Döner: [(özellik, katkı, değer, eğitim medyanı)]."""
    base = float(predict(row)[0])
    res = []
    for c in cols:
        r2 = row.copy(); med = float(train[c].median()); r2[c] = med
        res.append((c, base - float(predict(r2)[0]), float(row[c].iloc[0]), med))
    return sorted(res, key=lambda x: -abs(x[1]))[:top]
