"""Maskeler: basılı çizgiler, kod kutusu, XXX işaretleri, yazı alanı (ROI) ve el yazısı.

Her yapı ayrı maske olarak döner; el yazısı = karanlık pikseller − (çizgiler, kod kutusu, XXX, ROI dışı).
Çizgi silinirken harfin çizgiyi kestiği yerler "köprülenir" (üstte ve altta mürekkep varsa geri konur).
"""
from dataclasses import dataclass, field

import numpy as np
from scipy import ndimage as ndi

from .normalize import DARK_THRESHOLD, RULE_THRESHOLD, Preprocessed
from .paths import RULE_SPACING_MM

ROI_TOP_SPACINGS = 1.2     # ilk çizginin üstünde bir satır
ROI_BOTTOM_SPACINGS = 0.9  # son çizginin altında
ROI_SIDE = (0.04, 0.97)    # sol / sağ kenar payı (sayfa genişliği oranı)
MIN_SPECK_MM2 = 0.3        # bundan küçük bağlı bileşenler gürültü sayılır


@dataclass
class Rules:
    y: np.ndarray          # çizgi merkezleri (piksel)
    opened: np.ndarray     # uzun yatay çizgi pikselleri
    bands: list            # (r0, r1) genişletilmiş çizgi bantları
    spacing_px: float
    added: int = 0         # ızgaradan tamamlanan eksik çizgi sayısı


@dataclass
class Masks:
    dark: np.ndarray
    rules: Rules
    rule_mask: np.ndarray
    box: tuple             # (y0, y1, x0, x1) ya da None
    box_mask: np.ndarray
    overlay: np.ndarray
    roi: np.ndarray
    hw: np.ndarray
    flags: dict = field(default_factory=dict)


def _open_horizontal(mask, k):
    """Yatay açma (en az k piksel uzun koşular), van Herk ile O(N)."""
    m = mask.astype(np.uint8)
    return ndi.maximum_filter1d(ndi.minimum_filter1d(m, k, axis=1), k, axis=1) > 0


def regularize(y):
    """Basılı çizgiler düzenli aralıklıdır: iç boşlukları (eksik çizgi) ızgarayla tamamlar, ızgaraya uymayan sahte çizgiyi atar.

    Aralık = ardışık farkların medyanı (min değil: sahte yarım aralıklı çizgi aralığı bozmasın). Bulunan çizgilerin y'si
    korunur, yalnız eksik olanlar ızgaradan gelir. Baştaki/sondaki eksik çizgi tamamlanmaz. Döner: (y, eklenen, atılan)."""
    if len(y) < 4:
        return y, 0, 0
    sp = float(np.median(np.diff(y)))
    k = np.round((y - y[0]) / sp).astype(int)
    b, a = np.polyfit(k, y, 1)
    resid = np.abs(a + b * k - y)
    keep = np.ones(len(y), bool)
    for kk in np.unique(k):  # aynı ızgara noktasına düşen çizgilerden ızgaraya en yakın olan kalır
        idx = np.where(k == kk)[0]
        keep[idx] = False
        keep[idx[np.argmin(resid[idx])]] = True
    keep &= resid < 0.15 * sp
    if keep.sum() < 4:
        return y, 0, 0
    kk, yy = k[keep], y[keep]
    b, a = np.polyfit(kk, yy, 1)
    out = a + b * np.arange(kk.min(), kk.max() + 1)
    out[kk - kk.min()] = yy
    added, removed = len(out) - len(yy), int((~keep).sum())
    if added > max(3, 0.3 * len(yy)):  # çok fazla eksik: ızgara güvenilmez, tamamlama yapılmaz (rule_grid_irregular bayrağı kalır)
        return y, 0, 0
    return (out, added, removed) if added or removed else (y, 0, 0)


def find_rules(dark, min_len_frac=0.25, cov_thr=0.15, min_span_frac=0.5):
    """Basılı çizgiler: uzun yatay koşular. Bir bant yalnızca sayfa genişliğinin `min_span_frac`'ini kaplıyorsa çizgidir
    (sağ üstteki 50–70 mm'lik kod kutusu kenarları çizgi sayılmaz)."""
    H, W = dark.shape
    opened = _open_horizontal(dark, max(15, int(min_len_frac * W)))
    rows = np.where(opened.sum(1) / W > cov_thr)[0]
    groups = np.split(rows, np.where(np.diff(rows) > 2)[0] + 1) if len(rows) else []
    groups = [g for g in groups if len(g) and opened[g[0]:g[-1] + 1].any(0).mean() >= min_span_frac]
    y = np.array([float(np.mean(g)) for g in groups])
    bands = [(max(0, int(g[0]) - 2), min(H - 1, int(g[-1]) + 2)) for g in groups]
    y_full, added, removed = regularize(y)
    if added or removed:  # eksik çizgi bantlarını ızgaradan türet, sahte çizgileri at (kalınlık: ortalama)
        th = int(np.mean([b1 - b0 for b0, b1 in bands]) / 2)
        by_y = {round(float(v), 3): b for v, b in zip(y, bands)}
        bands = [by_y.get(round(float(v), 3), (max(0, int(round(v)) - th), min(H - 1, int(round(v)) + th))) for v in y_full]
        y = y_full
    sp = float(np.median(np.diff(y))) if len(y) > 1 else float("nan")
    return Rules(y, opened, bands, sp, added + removed)


def rule_mask_with_bridges(dark, rules):
    """Çizgi maskesi ve köprülenecek (harfin çizgiyi kestiği) pikseller."""
    rm = np.zeros_like(dark)
    for r0, r1 in rules.bands:
        if rules.added or rules.opened[r0:r1 + 1].any():  # çizgi bandının tamamı (kırık/basamaklı uç parçaları dahil); kesişen harfler köprülenir
            rm[r0:r1 + 1] = True
    bridge = np.zeros_like(dark)
    H = dark.shape[0]
    for r0, r1 in rules.bands:
        if r0 < 3 or r1 > H - 4:
            continue
        above = ndi.binary_dilation(dark[r0 - 2] & ~rm[r0 - 2], np.ones(5))
        below = ndi.binary_dilation(dark[r1 + 2] & ~rm[r1 + 2], np.ones(5))
        cols = above & below
        bridge[r0:r1 + 1] |= rm[r0:r1 + 1] & cols[None, :]
    return rm, bridge


def find_code_box(dark, rules, mm_per_px):
    """Sağ üst basılı dikdörtgen (kod kutusu): ilk çizgiden önceki bölgede büyük, içi boş çerçeve."""
    if len(rules.y) < 2:
        return None
    H, W = dark.shape
    top_rows = int(max(0, rules.y[0] - 0.3 * rules.spacing_px))
    x_off = W // 2
    lab, n = ndi.label(dark[:top_rows, x_off:], structure=np.ones((3, 3)))
    best = None
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if w * mm_per_px < 20 or h * mm_per_px < 6:
            continue
        fill = (lab[sl] == i).sum() / (h * w)
        if fill < 0.3 and (best is None or h * w > best[0]):
            best = (h * w, (sl[0].start, sl[0].stop, sl[1].start + x_off, sl[1].stop + x_off))
    return best[1] if best else None


def build_masks(pre: Preprocessed):
    dark = pre.gray < DARK_THRESHOLD
    H, W = dark.shape
    mm = pre.mm_per_px
    rules = find_rules(pre.gray < RULE_THRESHOLD)
    flags = dict(no_rules=len(rules.y) < 3, rules_filled=rules.added)  # rules_filled: ızgarayla tamamlanan + atılan çizgi sayısı
    d = np.diff(rules.y)
    flags['rule_spacing_off'] = bool(len(d) > 0 and abs(rules.spacing_px * pre.mm_per_px - RULE_SPACING_MM) > 0.8)  # beklenen 10,8 mm'den >0,8 mm sapma
    flags['rule_grid_irregular'] = bool(len(d) > 2 and np.abs(d / np.median(d) - 1).max() > 0.15)  # çizgi aralıkları düzensiz
    pad = max(1, int(round(1.0 / mm)))  # 1 mm
    if flags["no_rules"]:
        rule_mask, bridge = np.zeros_like(dark), np.zeros_like(dark)
        roi = np.zeros_like(dark); roi[int(0.1 * H):int(0.9 * H), int(ROI_SIDE[0] * W):int(ROI_SIDE[1] * W)] = True
    else:
        rule_mask, bridge = rule_mask_with_bridges(dark, rules)
        sp = rules.spacing_px
        roi = np.zeros_like(dark)
        roi[max(0, int(rules.y[0] - ROI_TOP_SPACINGS * sp)):min(H, int(rules.y[-1] + ROI_BOTTOM_SPACINGS * sp)),
            int(ROI_SIDE[0] * W):int(ROI_SIDE[1] * W)] = True
    box = None if flags["no_rules"] else find_code_box(dark, rules, mm)
    box_mask = np.zeros_like(dark)
    if box:
        y0, y1, x0, x1 = box
        box_mask[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = True
    flags["code_box_found"] = box is not None
    overlay = ndi.binary_dilation(pre.overlay, iterations=pad) if pre.overlay.any() else pre.overlay
    flags["overlay_masked_px"] = int((overlay & dark & roi).sum())
    flags["bridged_px"] = int((bridge & roi).sum())
    hw = ((dark & ~rule_mask) | bridge) & roi & ~box_mask & ~overlay
    # gürültü: çok küçük bileşenleri at
    min_px = max(3, int(MIN_SPECK_MM2 / mm ** 2))
    lab, n = ndi.label(hw, structure=np.ones((3, 3)))
    if n:
        sizes = ndi.sum(hw, lab, range(1, n + 1))
        small = np.isin(lab, 1 + np.where(sizes < min_px)[0])
        flags["speckle_px"] = int(small.sum()); hw = hw & ~small
    return Masks(dark, rules, rule_mask, box, box_mask, overlay, roi, hw, flags)


def pen_info(pre: Preprocessed, hw):
    """Kalem rengi özeti (kalite bayrağı): renkli mürekkep oranı ve mavi payı. Gri/ikili sayfada renk yok."""
    px = pre.rgb[hw].astype(int)
    if len(px) == 0:
        return dict(pen_colored_frac=0.0, pen_blue_share=float("nan"))
    sat = px.max(1) - px.min(1)
    colored = sat > 40
    blue = colored & (px[:, 2] > px[:, 0] + 30)
    return dict(pen_colored_frac=float(colored.mean()), pen_blue_share=float(blue.sum() / colored.sum()) if colored.any() else float("nan"))
