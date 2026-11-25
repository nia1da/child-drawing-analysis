"""Geometrik özellikler (mm, derece, oran): bileşen boyutu, satır hizası, sayfa kullanımı.

Prototip tanımları (gerçek sayfalarda karşılaştırılıp güncellenecek, `docs/el_yazisi_prototip.md`):
- **x-yüksekliği**: "gövde bileşenleri" (satır medyan yüksekliğinin 0,6–1,4 katı; yükselen/inen harfler ve bitişik uzun
  bileşenler dışarıda) yüksekliğinin medyanı. Bitişik el yazısında bileşen ≠ harf: gerçek sayfada doğrulanmadı.
- **taban çizgisi**: gövde bileşenlerinin alt kenarı (cx, y1); satır başına Theil–Sen doğrusu. Çizgiye uzaklık = çizgi − taban
  (pozitif: taban çizginin üstünde). Eğim: derece, pozitif = sağa doğru aşağı.
- **hizalama değişkenliği**: satır içi (doğru etrafındaki kalıntıların MAD'ı) ve satırlar arası (çizgi uzaklığının SD'si).
"""
import numpy as np
from scipy.stats import theilslopes

from .masks import Masks
from .normalize import Preprocessed
from .segment import Segmentation

MIN_BODY_COMPS = 5


def _iqr_ratio(v):
    v = np.asarray(v, float)
    return float((np.percentile(v, 75) - np.percentile(v, 25)) / np.median(v)) if len(v) > 4 and np.median(v) > 0 else np.nan


def _body(line_comps):
    h = (line_comps.y1 - line_comps.y0).values
    med = np.median(h)
    return line_comps[(h >= 0.6 * med) & (h <= 1.4 * med)]


def extract_features(pre: Preprocessed, masks: Masks, seg: Segmentation):
    mm = pre.mm_per_px
    comps = seg.comps[seg.comps.line >= 0]
    H, W = masks.hw.shape
    f = dict(n_rules=int(len(masks.rules.y)), rule_spacing_mm=float(masks.rules.spacing_px * mm) if len(masks.rules.y) > 1 else np.nan)
    h_mm = (comps.y1 - comps.y0).values * mm
    f.update(n_components=int(len(comps)), comp_h_mm_median=float(np.median(h_mm)) if len(h_mm) else np.nan,
             comp_h_iqr_ratio=_iqr_ratio(h_mm), comp_w_mm_median=float(np.median((comps.x1 - comps.x0) * mm)) if len(comps) else np.nan)

    xh, xh_within, offs, slopes, wobbles = [], [], [], [], []
    for k in seg.used:
        lc = comps[comps.line == k]
        body = _body(lc) if len(lc) else lc
        if len(body) < MIN_BODY_COMPS:
            continue
        bh = (body.y1 - body.y0).values * mm
        xh.append(float(np.median(bh))); xh_within.append(_iqr_ratio(bh))
        cx, base = body.cx.values, body.y1.values.astype(float)
        sl, ic, _, _ = theilslopes(base, cx)
        resid = base - (ic + sl * cx)
        wobbles.append(float(1.4826 * np.median(np.abs(resid - np.median(resid)))) * mm)
        slopes.append(float(np.degrees(np.arctan(sl))))
        offs.append(float((masks.rules.y[k] - (ic + sl * cx.mean())) * mm))
    nz = lambda v, fn: float(fn(v)) if len(v) else np.nan
    f.update(xheight_mm=nz(xh, np.median), xheight_cv_lines=float(np.std(xh) / np.mean(xh)) if len(xh) > 1 else np.nan,
             xheight_iqr_ratio_within=nz([v for v in xh_within if v == v], np.median),
             baseline_offset_mm_median=nz(offs, np.median), baseline_offset_mm_sd=float(np.std(offs)) if len(offs) > 1 else np.nan,
             baseline_slope_deg_median=nz(slopes, np.median), baseline_slope_deg_sd=float(np.std(slopes)) if len(slopes) > 1 else np.nan,
             baseline_wobble_mm_median=nz(wobbles, np.median), lines_measured=len(xh))

    # sayfa kullanımı
    n_rules = len(masks.rules.y)
    f.update(used_lines=len(seg.used), used_frac=len(seg.used) / n_rules if n_rules else np.nan,
             first_used_line=seg.used[0] if seg.used else None, last_used_line=seg.used[-1] if seg.used else None)
    ys, xs = np.nonzero(masks.hw)
    if len(xs):
        f.update(left_margin_mm=float(xs.min() * mm), right_margin_mm=float((W - 1 - xs.max()) * mm),
                 ink_bbox_h_mm=float((ys.max() - ys.min() + 1) * mm), ink_bbox_w_mm=float((xs.max() - xs.min() + 1) * mm))
    area = masks.roi.sum()
    f["ink_density"] = float(masks.hw.sum() / area) if area else np.nan
    f["ink_mm2_per_used_line"] = float(masks.hw.sum() * mm ** 2 / len(seg.used)) if seg.used else np.nan
    width = (masks.roi.any(0)).sum()
    fills = [(lc.x1.max() - lc.x0.min()) / width for _, lc in comps.groupby("line")] if width else []
    f["mean_line_fill_frac"] = float(np.mean(fills)) if fills else np.nan
    f["overflow_last_line"] = bool(seg.used and n_rules and seg.used[-1] >= n_rules - 1)
    return f


def quality_flags(pre, masks, pen):
    q = dict(skew_deg=pre.skew_deg, dpi=pre.dpi, **pre.flags, **masks.flags, **pen)
    q["dark_outside_roi_px"] = int((masks.dark & ~masks.roi & ~masks.rule_mask).sum()) if masks.dark.any() else 0
    return q
