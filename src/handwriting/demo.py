"""Sentetik sayfalarda prototipi görselleştirir: `python -m src.handwriting.demo [çıktı_klasörü]`.

Gerçek veri kullanmaz. Çıktı PNG'leri yalnız sentetik sayfalardır (commit'e girebilir).
"""
import sys
from pathlib import Path

from .pipeline import analyze_page
from .synthetic import make_layout, render
from .viz import plot_result

SCENARIOS = {
    "kolay": dict(layout=dict(seed=1, slope_deg=0.3), render=dict(dpi=150, skew_deg=0.4)),
    "zor": dict(layout=dict(seed=7, xh_mm=2.4, slope_deg=-0.6, wobble_mm=0.4, skip_lines=(3,), used_lines=9, fill=0.95),
                render=dict(dpi=200, pen="pencil", skew_deg=-0.5, jpeg_quality=40, noise=8.0, gradient=20.0)),
}


def main(out_dir="docs/el_yazisi_prototip"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, s in SCENARIOS.items():
        layout = make_layout(**s["layout"])
        rgb, _, boxes, info = render(layout, **s["render"])
        res = analyze_page(rgb, info["dpi"], boxes)
        plot_result(res, out / f"sentetik_{name}.png", title=f"sentetik sayfa: {name} (gerçek veri değil) | gerçek x-yüksekliği (mürekkep) "
                    f"{layout.truth['xh_ink_mm']:.2f} mm, çizgi uzaklığı {layout.truth['baseline_offset_ink_mm']:.2f} mm, eğim {layout.truth['slope_deg']}°",
                    crop_mm=(20, 125))
        print(name, {k: round(v, 3) for k, v in res.features.items() if isinstance(v, float)})


if __name__ == "__main__":
    main(*sys.argv[1:2])
