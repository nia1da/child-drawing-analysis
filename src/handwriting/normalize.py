"""Görüntü ve ölçek normalizasyonu: çalışma çözünürlüğü, arka plan düzeltme, eğiklik düzeltme.

Fiziksel ölçek sayfa boyutundan gelir (görüntü A4 sayfaya yerleşik, `dpi` = piksel / inç). 150 dpi altındaki
görüntüler büyütülmez: `low_resolution` bayrağıyla yerel çözünürlükte işlenir ve normlara girmez.
"""
from dataclasses import dataclass, field

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from .paths import WORK_DPI

DARK_THRESHOLD = 170  # arka planı 255'e düzeltilmiş gri düzeyinde "karanlık" eşiği
RULE_THRESHOLD = 200  # soluk/ince basılı çizgiler için daha izin verici eşik (yalnız çizgi bulmada)


@dataclass
class Preprocessed:
    rgb: np.ndarray        # dik, eğiklik düzeltilmiş, çalışma çözünürlüğünde
    gray: np.ndarray       # arka planı düzeltilmiş gri (0–255, float32)
    overlay: np.ndarray    # metin katmanı kutuları (XXX, telif satırı) maskesi (bool), aynı geometri
    dpi: float
    skew_deg: float
    flags: dict = field(default_factory=dict)

    @property
    def mm_per_px(self):
        return 25.4 / self.dpi


def flatten_background(gray):
    """Aydınlatma/arka plan eğimini giderir: yerel beyaz düzeyine bölüp 255'e ölçekler."""
    size = max(15, int(round(gray.shape[1] / 60)) | 1)
    bg = ndi.maximum_filter(ndi.gaussian_filter(gray, 1.5), size=size)
    bg = ndi.gaussian_filter(bg, size / 2)
    return np.clip(gray / np.maximum(bg, 1) * 255, 0, 255).astype(np.float32)


def estimate_skew_deg(dark, search=3.0):
    """Satır/çizgi eğikliği: yatay izdüşüm varyansını en büyükleyen açı (kaba 0,25° + ince 0,05°)."""
    sm = dark[::2, ::2].astype(np.float32)
    score = lambda a: ndi.rotate(sm, a, reshape=False, order=0).sum(1).var()
    coarse = np.arange(-search, search + 1e-6, 0.25)
    best = max(coarse, key=score)
    fine = np.arange(best - 0.25, best + 0.2501, 0.05)
    return float(max(fine, key=score))


def _rotate(a, angle, order, cval):
    if a.ndim == 3:
        return np.stack([ndi.rotate(a[..., k], angle, reshape=False, order=order, cval=cval) for k in range(a.shape[2])], 2)
    return ndi.rotate(a, angle, reshape=False, order=order, cval=cval)


def preprocess(rgb, dpi, overlay_boxes=None, work_dpi=WORK_DPI):
    """rgb: (H,W,3) uint8, dpi: görüntü çözünürlüğü, overlay_boxes: [(x0,y0,x1,y1)] piksel (orijinal görüntü)."""
    flags = {}
    dpi_out = float(dpi)
    if dpi > work_dpi * 1.02:
        dpi_out = float(work_dpi)
    elif dpi < work_dpi * 0.95:
        flags["low_resolution"] = True
    h, w = rgb.shape[:2]
    overlay = np.zeros((h, w), np.uint8)
    for x0, y0, x1, y1 in overlay_boxes or []:  # PyMuPDF kutuları float olabilir
        x0, y0, x1, y1 = (int(round(v)) for v in (x0, y0, x1, y1))
        overlay[max(0, y0):y1, max(0, x0):x1] = 255
    scale = dpi_out / dpi
    if abs(scale - 1) > 0.02:
        size = (int(round(w * scale)), int(round(h * scale)))
        rgb = np.asarray(Image.fromarray(rgb).resize(size, Image.BOX))
        overlay = np.asarray(Image.fromarray(overlay).resize(size, Image.BOX))
    overlay = overlay > 0
    gray = flatten_background(rgb.astype(np.float32).mean(2))
    skew = estimate_skew_deg(gray < DARK_THRESHOLD)
    if abs(skew) > 0.02:
        rgb = _rotate(rgb, skew, 1, 255).astype(np.uint8)
        gray = _rotate(gray, skew, 1, 255).astype(np.float32)
        overlay = _rotate(overlay.astype(np.uint8), skew, 0, 0) > 0
    return Preprocessed(rgb, gray, overlay, dpi_out, skew, flags)
