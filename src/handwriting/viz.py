"""Görselleştirme: karşılaştırmalı panel (orijinal, önişlenmiş, maskeler, satırlar, ölçümler) ve rapor için işaretli bölgeler.

Yalnız bellekte çizer; `path` verilirse PNG yazar. Gerçek FD-LEX sayfalarıyla kullanılırsa çıktı yerel kalmalı,
commit'e girmemeli (commit denetimi `data/handwriting/` yolunu, görüntü dosyalarını ve gömülü görüntüleri yakalar).
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage as ndi

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


def _baselines(ax, r, color="red", lw=1.2, wobble_colors=False):
    for _, ln in r.lines.dropna(subset=["base_slope_px"]).iterrows():
        xs = np.array([ln.x0_px, ln.x1_px])
        c = color
        if wobble_colors:
            c = "orange" if ln.wobble_mm > 0.3 else "limegreen"
        ax.plot(xs, ln.base_icpt_px + ln.base_slope_px * xs, color=c, lw=lw)


def _crop(axes, r, crop_mm):
    if crop_mm:
        y0, y1 = (int(v / r.pre.mm_per_px) for v in crop_mm)
        for a in axes:
            a.set_ylim(y1, y0)


def plot_result(r: Result, path=None, title="", crop_mm=None, original=None):
    """Panel: [orijinal] | önişlenmiş | maskeler | satırlar ve taban çizgileri | özellik tablosu. `original`: önişlemeden önceki rgb."""
    n_img = 4 if original is not None else 3
    fig, ax = plt.subplots(1, n_img + 1, figsize=(5.2 * n_img + 4, 6 if crop_mm else 9), gridspec_kw=dict(width_ratios=[1] * n_img + [0.8]))
    k = 0
    if original is not None:
        ax[0].imshow(original); ax[0].set_title("orijinal (render)"); k = 1
    ax[k].imshow(r.pre.rgb); ax[k].set_title(f"önişlenmiş (dik, {r.pre.dpi:.0f} dpi)")
    ax[k + 1].imshow(mask_overlay(r)); ax[k + 1].set_title("mavi: çizgi · turuncu: kod kutusu · kırmızı: metin katmanı · yeşil: el yazısı")
    ax[k + 2].imshow(np.where(r.masks.hw, 0.0, 1.0), cmap="gray", vmin=0, vmax=1)
    cmap = plt.get_cmap("tab10")
    for _, c in r.seg.comps[r.seg.comps.line >= 0].iterrows():
        ax[k + 2].add_patch(plt.Rectangle((c.x0, c.y0), c.x1 - c.x0, c.y1 - c.y0, fill=False, ec=cmap(int(c.line) % 10), lw=0.5))
    _baselines(ax[k + 2], r)
    for ln in r.seg.used:
        ax[k + 2].plot([0, r.masks.hw.shape[1]], [r.masks.rules.y[ln]] * 2, color="blue", lw=0.4, alpha=0.6)
    ax[k + 2].set_title("satırlar (renk), taban çizgisi (kırmızı), çizgi (mavi)")
    if original is not None and crop_mm is None:
        pass
    _crop(ax[:n_img], r, crop_mm)
    for a in ax[:n_img]:
        a.axis("off")
    ax[n_img].axis("off")
    rows = [f"{key}: {r.features[key]:.3g}" if isinstance(r.features.get(key), (int, float, np.floating)) and r.features.get(key) == r.features.get(key)
            else f"{key}: {r.features.get(key)}" for key in SHOW]
    q = [f"{key}: {v:.3g}" if isinstance(v, float) else f"{key}: {v}" for key, v in r.quality.items()]
    ax[n_img].text(0, 1, "ÖZELLİKLER\n" + "\n".join(rows) + "\n\nKALİTE\n" + "\n".join(q), va="top", family="monospace", fontsize=9)
    fig.suptitle(title); fig.tight_layout()
    if path:
        fig.savefig(path, dpi=80)
        plt.close(fig)
    return fig


def outlier_components(r: Result, z=2.5, max_n=12):
    """Satırının gövde yüksekliği medyanından sağlam z-skorla (MAD) belirgin sapan bileşenler: uzmanın bakacağı bölgeler."""
    comps = r.seg.comps[r.seg.comps.line >= 0].copy()
    comps["h"] = comps.y1 - comps.y0
    out = []
    for _, g in comps.groupby("line"):
        med = g.h.median(); mad = max(1.4826 * (g.h - med).abs().median(), 1.0)
        out.append(g[(g.h - med).abs() / mad > z])
    if not out:
        return comps.iloc[0:0]
    o = comps.loc[np.concatenate([x.index for x in out])]
    return o.assign(dev=(o.h - o.groupby("line").h.transform("median")).abs()).sort_values("dev", ascending=False).head(max_n)


def annotate_regions(r: Result, path=None, title="", crop_mm=None):
    """Rapor görseli: taban çizgileri (dalgalanmaya göre renk), boyut bakımından sapan bileşenler, sol kenar boşluğu, atlanan satırlar,
    ölçüm dışı bırakılan alanlar. İşaretler 'uzmanın bakacağı yer'dir, bir değerlendirme değildir."""
    mm = r.pre.mm_per_px
    fig, ax = plt.subplots(1, 1, figsize=(11, 6 if crop_mm else 13))
    ax.imshow(r.pre.rgb)
    # ölçüm dışı alanlar
    for mask, label, c in [(r.masks.box_mask, "ölçüm dışı: kod kutusu", "orange"), (r.masks.overlay, "ölçüm dışı: metin katmanı (XXX, telif)", "red")]:
        lab, n = ndi.label(mask)
        for i, sl in enumerate(ndi.find_objects(lab)):  # her ayrı bölge ayrı çerçeve (birleşik kutu yanıltır)
            ax.add_patch(plt.Rectangle((sl[1].start, sl[0].start), sl[1].stop - sl[1].start, sl[0].stop - sl[0].start, fill=False, ec=c, ls="--", lw=1.0))
            if i == 0:
                ax.text(sl[1].start, sl[0].start - 4, label, color=c, fontsize=7)
    _baselines(ax, r, lw=1.6, wobble_colors=True)
    for _, c in outlier_components(r).iterrows():
        ax.add_patch(plt.Rectangle((c.x0 - 2, c.y0 - 2), c.x1 - c.x0 + 4, c.y1 - c.y0 + 4, fill=False, ec="magenta", lw=1.2))
    # sol kenar boşluğu
    ys, xs = np.nonzero(r.masks.hw)
    if len(xs):
        ax.axvline(xs.min(), color="deepskyblue", lw=1.0, ls=":")
        ax.text(xs.min() + 3, r.masks.rules.y[r.seg.used[-1]] + 0.8 * r.masks.rules.spacing_px, f"sol boşluk {xs.min() * mm:.1f} mm", color="deepskyblue", fontsize=8)
    # atlanan satırlar
    if r.seg.used:
        for k in range(r.seg.used[0], r.seg.used[-1] + 1):
            if k not in r.seg.used:
                y = r.masks.rules.y[k]
                ax.text(r.masks.hw.shape[1] * 0.4, y - 0.4 * r.masks.rules.spacing_px, "boş satır", color="gray", fontsize=8)
    ax.text(0.01, 0.995, "yeşil: taban çizgisi dalgalanması ≤ 0,3 mm · turuncu: > 0,3 mm · mor: satırının gövde boyutundan belirgin sapan bileşen",
            transform=ax.transAxes, fontsize=7, va="top", color="black", bbox=dict(fc="white", alpha=0.7, lw=0))
    _crop([ax], r, crop_mm)
    ax.axis("off")
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=85)
        plt.close(fig)
    return fig
