"""Sonuçların görselleştirilmesi (prototip değerlendirmesi için): maskeler, satırlar, taban çizgileri, özet tablo.

Yalnız bellekte çizer; `path` verilirse PNG yazar. Gerçek FD-LEX sayfalarıyla kullanılırsa çıktı yerel kalmalı,
commit'e girmemeli (commit denetimi `data/handwriting/` yolunu ve gömülü görüntüleri yakalar).
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import theilslopes

from .pipeline import Result

SHOW = ["n_rules", "rule_spacing_mm", "xheight_mm", "comp_h_mm_median", "comp_h_iqr_ratio", "baseline_offset_mm_median",
        "baseline_offset_mm_sd", "baseline_slope_deg_median", "baseline_wobble_mm_median", "used_lines", "used_frac",
        "left_margin_mm", "right_margin_mm", "ink_density", "mean_line_fill_frac"]


def mask_overlay(r: Result):
    m, base = r.masks, np.asarray(r.pre.gray, np.float32)
    img = np.stack([base] * 3, 2) / 255 * 0.55 + 0.45
    colors = [(m.rule_mask, (0.3, 0.5, 1.0)), (m.box_mask, (1.0, 0.6, 0.1)), (m.overlay & m.dark, (1.0, 0.2, 0.2)),
              (m.hw, (0.1, 0.7, 0.2))]
    for mask, c in colors:
        img[mask] = c
    roi = ~m.roi
    img[roi & ~m.dark] *= 0.9
    return np.clip(img, 0, 1)


def plot_result(r: Result, path=None, title="", crop_mm=None):
    """Dört panel: önişlenmiş sayfa, maskeler, satır/taban çizgisi, özellik tablosu."""
    mm = r.pre.mm_per_px
    fig, ax = plt.subplots(1, 4, figsize=(20, 6 if crop_mm else 9), gridspec_kw=dict(width_ratios=[1, 1, 1, 0.8]))
    ax[0].imshow(r.pre.rgb); ax[0].set_title("önişlenmiş (dik, 150 dpi)")
    ax[1].imshow(mask_overlay(r)); ax[1].set_title("mavi: çizgi · turuncu: kod kutusu · kırmızı: XXX · yeşil: el yazısı")
    ax[2].imshow(np.where(r.masks.hw, 0.0, 1.0), cmap="gray", vmin=0, vmax=1)
    cmap = plt.get_cmap("tab10")
    for _, c in r.seg.comps[r.seg.comps.line >= 0].iterrows():
        ax[2].add_patch(plt.Rectangle((c.x0, c.y0), c.x1 - c.x0, c.y1 - c.y0, fill=False, ec=cmap(int(c.line) % 10), lw=0.5))
    for k in r.seg.used:
        lc = r.seg.comps[r.seg.comps.line == k]
        h = (lc.y1 - lc.y0).values; med = np.median(h)
        body = lc[(h >= 0.6 * med) & (h <= 1.4 * med)]
        if len(body) >= 5:
            sl, ic, _, _ = theilslopes(body.y1.values.astype(float), body.cx.values)
            xs = np.array([body.cx.min(), body.cx.max()])
            ax[2].plot(xs, ic + sl * xs, color="red", lw=1.2)
        ax[2].plot([0, r.masks.hw.shape[1]], [r.masks.rules.y[k]] * 2, color="blue", lw=0.4, alpha=0.6)
    ax[2].set_title("satırlar (renk), taban çizgisi (kırmızı), çizgi (mavi)")
    if crop_mm:
        y0, y1 = (int(v / mm) for v in crop_mm)
        for a in ax[:3]:
            a.set_ylim(y1, y0)
    for a in ax[:3]:
        a.axis("off")
    ax[3].axis("off")
    rows = [f"{k}: {r.features[k]:.3g}" if isinstance(r.features.get(k), (int, float, np.floating)) and r.features.get(k) == r.features.get(k)
            else f"{k}: {r.features.get(k)}" for k in SHOW]
    q = [f"{k}: {v:.3g}" if isinstance(v, float) else f"{k}: {v}" for k, v in r.quality.items()]
    ax[3].text(0, 1, "ÖZELLİKLER\n" + "\n".join(rows) + "\n\nKALİTE\n" + "\n".join(q), va="top", family="monospace", fontsize=9)
    fig.suptitle(title); fig.tight_layout()
    if path:
        fig.savefig(path, dpi=80)
        plt.close(fig)
    return fig
