"""SENTETİK örnek uzman raporu: `python -m src.handwriting.example_report [çıktı_klasörü] [--refresh]`.

Gerçek öğrenci/ölçüm yok. Yapay referans (100 sentetik sayfa) `yapay_referans.csv` olarak önbelleğe alınır. Çıktı: `ornek_rapor.md`,
`ornek_rapor.json`, `isaretli_bolgeler.png` (rapor görseli), `onceki_yazi.png`. Raporun biçimi ve dili içindir; sayıların bilimsel anlamı yoktur.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from .pipeline import analyze_page
from .report import MEASURES, build_report, render_text
from .synthetic import make_layout, render
from .viz import annotate_regions


def synthetic_reference(n=100, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        lay = make_layout(seed=1000 + i, xh_mm=float(np.clip(rng.normal(3.0, 0.45), 2.0, 4.5)), wobble_mm=float(rng.uniform(0.05, 0.35)),
                          slope_deg=float(rng.normal(0, 0.25)), used_lines=int(rng.integers(4, 14)), fill=float(rng.uniform(0.5, 0.95)),
                          left_mm=float(rng.uniform(18, 26)), baseline_gap_mm=float(rng.uniform(0.8, 1.6)), size_cv=float(rng.uniform(0.06, 0.2)))
        rgb, _, boxes, _ = render(lay, dpi=150, skew_deg=float(rng.normal(0, 0.3)))
        f = analyze_page(rgb, 150, boxes).features
        rows.append({k: f.get(k) for k in MEASURES})
    return pd.DataFrame(rows)


def main(out_dir="docs/el_yazisi_ornek_rapor", refresh=False):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    ref_path = out / "yapay_referans.csv"
    if refresh or not ref_path.exists():
        synthetic_reference().to_csv(ref_path, index=False, encoding="utf-8", lineterminator="\n")
    ref = pd.read_csv(ref_path, encoding="utf-8")

    prev_lay = make_layout(seed=11, xh_mm=3.4, wobble_mm=0.25, slope_deg=-0.2, used_lines=8, fill=0.8)
    cur_lay = make_layout(seed=12, xh_mm=4.1, wobble_mm=0.5, slope_deg=-0.5, used_lines=9, fill=0.9, skip_lines=(4,), left_mm=19.0)
    rgb_p, _, bx_p, _ = render(prev_lay, dpi=150, skew_deg=0.2)
    rgb_c, _, bx_c, _ = render(cur_lay, dpi=150, skew_deg=-0.3)
    res_prev, res = analyze_page(rgb_p, 150, bx_p), analyze_page(rgb_c, 150, bx_c)

    ctx = {"veri": "SENTETİK ÖRNEK, gerçek öğrenci değil", "referans": "YAPAY referans (100 sentetik sayfa)", "sınıf": "5. sınıf (örnek)",
           "görev": "Bericht (örnek)", "ölçüm zamanı": "MZP3 (örnek); önceki: MZP1"}
    # DEMO eşikleri: gerçek eşik, aynı öğrencinin sayfaları arası değişkenlikten gerçek veriyle kurulacak
    rep = build_report(res, reference=ref, previous=res_prev.features, change_threshold={"xheight_mm": 0.4, "baseline_wobble_mm_median": 0.15}, context=ctx)
    (out / "ornek_rapor.md").write_text(render_text(rep), encoding="utf-8", newline="\n")
    (out / "ornek_rapor.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8", newline="\n")
    annotate_regions(res, out / "isaretli_bolgeler.png", title="SENTETİK sayfa: işaretli bölgeler (şimdiki yazı, MZP3)", crop_mm=(25, 135))
    annotate_regions(res_prev, out / "onceki_yazi.png", title="SENTETİK sayfa: önceki yazı (MZP1)", crop_mm=(25, 135))
    return rep


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(*(args[:1]), refresh="--refresh" in sys.argv)
