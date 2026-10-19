"""Çizim ölçümleri (ilk dilim): doluluk oranı, farklı renk sayısı, koyu ton oranı. Tanımlar: docs/olcumler.md.

Parametreler KIDO'da kontrol edildi (2026-10-19):
- Renk sayısı: doygun pikseller (S > SAT_S, V > SAT_V; koyu piksellerde ton güvenilmez) 12 ton bölmesine
  (30°, kırmızı 0° çevresinde ortalı) ayrılır. Bir bölme, doygun piksellerin en az HUE_MIN_SHARE'i ve en az
  HUE_MIN_PIXELS piksel içeriyorsa sayılır. Siyah, gri, beyaz (renksiz) sayılmaz; kahverengi turuncu/kırmızı
  bölmesine düşer. Örnek: çok renkli 101-2E-182 -> 7, kırmızı kalp 211-7B-5298 -> 1, karakalem -> 0.
- Koyu ton: çizim piksellerinden V < DARK_TONE_V olanların oranı. Siyah kalem/boya V ≈ 0-60, kurşun kalem
  grisi V ≈ 130-200: siyah kalemle çizilmiş 214-5G-159 -> 0.65, yoğun kurşun kalem gölgeleme 107-4D-943 -> 0.15.
"""
import numpy as np

from .mask import drawing_mask, faint_color_ratio, FAINT_FLAG, load_drawing, to_hsv

MEASUREMENT_VERSION = 1  # maske ya da ölçüm tanımı değişirse artır; normlar yeniden hesaplanmalı
SAT_S, SAT_V = 60, 60  # doygun piksel: renk sayısı için
HUE_BINS = 12
HUE_MIN_SHARE, HUE_MIN_PIXELS = 0.03, 50
DARK_TONE_V = 80

# Ölçüm kimliği -> görünen ad (rapor ve normlar bu sırayı kullanır)
MEASURES = {
    "doluluk_orani": "Doluluk oranı",
    "renk_sayisi": "Farklı renk sayısı",
    "koyu_ton_orani": "Koyu ton oranı",
}


def fill_ratio(mask):
    return float(mask.mean())


def hue_bins(hsv, mask):
    """Doygun çizim piksellerinin 12 ton bölmesindeki sayıları (bölme 0 = kırmızı, 0° ± 15°)."""
    h, s, v = (hsv[..., i][mask].astype(int) for i in range(3))
    saturated = (s > SAT_S) & (v > SAT_V)
    degrees = h[saturated] * 360 / 256  # PIL tonu 0-255
    bins = ((degrees + 360 / HUE_BINS / 2) // (360 / HUE_BINS)).astype(int) % HUE_BINS
    return np.bincount(bins, minlength=HUE_BINS)


def color_count(hsv, mask):
    counts = hue_bins(hsv, mask)
    total = counts.sum()
    if total == 0:
        return 0
    return int(((counts >= HUE_MIN_SHARE * total) & (counts >= HUE_MIN_PIXELS)).sum())


def dark_tone_ratio(hsv, mask):
    # Çizim yoksa tanımsız (None)
    if not mask.any():
        return None
    return float((hsv[..., 2][mask] < DARK_TONE_V).mean())


def measure_image(img):
    """Kırpılmış RGB görüntü (load_drawing) -> ölçümler ve kalite bilgisi."""
    hsv = to_hsv(img)
    mask = drawing_mask(hsv)
    faint = faint_color_ratio(hsv, mask)
    return {
        "doluluk_orani": fill_ratio(mask),
        "renk_sayisi": color_count(hsv, mask),
        "koyu_ton_orani": dark_tone_ratio(hsv, mask),
        "soluk_renk_orani": faint,
        "soluk_renk_bayragi": faint >= FAINT_FLAG,
    }


def measure(path):
    return measure_image(load_drawing(path))
