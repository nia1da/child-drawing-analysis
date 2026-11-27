"""DiaGraMo: geometrik özellikler, istatistik yardımcıları, okul bazlı bölme, ordinal modeller, test kilidi (sentetik veri)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from src.handwriting.diagramo import analysis as A
from src.handwriting.diagramo import models as M
from src.handwriting.diagramo.dataset import make_school_split
from src.handwriting.diagramo.explain import occlusion_contributions
from src.handwriting.diagramo.geom import coord_lines, features_from_ink
from src.handwriting.diagramo.render import render_strokes

PPU = 4.0


def text_like(lines=4, xh=3.5, slope_deg=0.0, pitch=11.0, scribble=False, width=300.0, seed=0):
    """Yatay satırlar halinde 'harf' vuruşları (tablet koordinatı, y yukarı). Döner: vuruş listesi."""
    rng = np.random.default_rng(seed)
    tan = np.tan(np.radians(slope_deg))
    strokes = []
    for k in range(lines):
        base = 150 - k * pitch                                       # y yukarı: ilk satır üstte
        x = 30.0
        while x < 30 + width:
            h = xh * (1 + rng.normal(0, 0.05)); w = 2.5
            t = np.linspace(0, 2 * np.pi, 20)
            y0 = base + (x - 30) * tan * -1                           # eğim: sağa doğru aşağı = y azalır
            strokes.append(np.c_[x + w / 2 + w / 2 * np.cos(t), y0 + h / 2 + h / 2 * np.sin(t)])
            x += w + 1.2
            if rng.random() < 0.12: x += 4
    if scribble:
        cx, cy = 100.0, 150 - pitch
        for r in np.linspace(0.5, 5, 12):
            t = np.linspace(0, 2 * np.pi, 80)
            strokes.append(np.c_[cx + r * np.cos(t), cy + r * np.sin(t)])
    return strokes


def ink_of(strokes, line_px=3):
    return np.asarray(render_strokes(strokes, px_per_mm=PPU, canvas="tablet", line_px=line_px).image) < 128


class TestGeom(unittest.TestCase):
    def test_lines_pitch_and_size(self):
        f = features_from_ink(ink_of(text_like(lines=4)), PPU)
        self.assertTrue(f["ok"]); self.assertEqual(f["n_lines"], 4)
        self.assertAlmostEqual(f["pitch_tb"], 11.0, delta=1.0)
        self.assertAlmostEqual(f["xh_tb"], 3.5 + 0.75, delta=1.2)                         # çizgi kalınlığı kadar şişer
        self.assertLess(f["pitch_cv"], 0.1)

    def test_slope_is_recovered_with_sign(self):
        up = features_from_ink(ink_of(text_like(lines=3, slope_deg=0.0)), PPU)["slope_med_deg"]
        down = features_from_ink(ink_of(text_like(lines=3, slope_deg=1.0)), PPU)["slope_med_deg"]   # sağa doğru aşağı = pozitif
        self.assertGreater(down - up, 0.5)

    def test_size_scales_and_is_invariant_to_resolution(self):
        small = features_from_ink(ink_of(text_like(xh=3.0)), PPU)["xh_tb"]
        big = features_from_ink(ink_of(text_like(xh=6.0)), PPU)["xh_tb"]
        self.assertGreater(big, small * 1.5)
        a = features_from_ink(np.asarray(render_strokes(text_like(), px_per_mm=4.0, canvas="tablet", line_px=3).image) < 128, 4.0)["xh_tb"]
        b = features_from_ink(np.asarray(render_strokes(text_like(), px_per_mm=6.0, canvas="tablet", line_px=4).image) < 128, 6.0)["xh_tb"]
        self.assertAlmostEqual(a, b, delta=0.8)                                              # tb cinsinden çözünürlükten bağımsız

    def test_scribble_raises_thick_and_junction_features(self):
        clean = features_from_ink(ink_of(text_like()), PPU)
        dirty = features_from_ink(ink_of(text_like(scribble=True)), PPU)
        self.assertGreater(dirty["thick_frac"], clean["thick_frac"] * 2)
        self.assertGreater(dirty["largest_blob_tb2"], clean["largest_blob_tb2"])

    def test_empty_image(self):
        self.assertFalse(features_from_ink(np.zeros((100, 100), bool), PPU)["ok"])

    def test_coordinate_lines_agree_with_image_lines(self):
        st = text_like(lines=5)
        self.assertEqual(coord_lines(st)["coord_n_lines"], 5)
        self.assertEqual(features_from_ink(ink_of(st), PPU)["n_lines"], 5)


class TestStats(unittest.TestCase):
    def test_partial_and_within_group_remove_confounding(self):
        rng = np.random.default_rng(0)
        z = rng.normal(size=300); x = z + rng.normal(0, 0.3, 300); y = z + rng.normal(0, 0.3, 300)
        self.assertGreater(abs(A.stats.spearmanr(x, y)[0]), 0.8)
        self.assertLess(abs(A.partial_spearman(x, y, z[:, None])), 0.25)
        g = np.repeat(np.arange(30), 10); off = rng.normal(0, 3, 30)[g]
        x2, y2 = off + rng.normal(size=300), off + rng.normal(size=300)
        self.assertGreater(A.stats.spearmanr(x2, y2)[0], 0.7)
        self.assertLess(abs(A.within_group_spearman(x2, y2, g)), 0.25)

    def test_bh_and_cluster_ci(self):
        q = A.bh([0.001, 0.01, 0.02, 0.5, 0.9])
        self.assertTrue(np.all(np.diff(q) >= -1e-12) and np.all(q >= np.array([0.001, 0.01, 0.02, 0.5, 0.9]) - 1e-12))
        rng = np.random.default_rng(1); x = rng.normal(size=200); y = x + rng.normal(0, 0.5, 200)
        lo, hi = A.cluster_bootstrap_ci(x, y, np.repeat(np.arange(20), 10), reps=200)
        self.assertLess(lo, A.stats.spearmanr(x, y)[0]); self.assertGreater(hi, A.stats.spearmanr(x, y)[0])

    def test_select_features_keeps_signal_drops_noise_and_duplicates(self):
        rng = np.random.default_rng(2); n = 240
        s = rng.normal(size=n)
        df = pd.DataFrame({"family": ["dictation", "copy"] * (n // 2), "signal": s, "signal_dup": s * 2 + rng.normal(0, 0.01, n), "noise": rng.normal(size=n)})
        for t in A.TARGETS:
            df[t] = np.clip(np.rint(3 + s + rng.normal(0, 0.8, n)), 1, 5)
        sel = A.select_features(df, ["signal", "signal_dup", "noise"])
        for t in A.TARGETS:
            self.assertEqual(len([f for f in sel[t] if f.startswith("signal")]), 1)       # yedekli ikiz tek temsilciye iner
            self.assertNotIn("noise", sel[t])


class TestSplitAndModels(unittest.TestCase):
    def children(self):
        rng = np.random.default_rng(0)
        rows = [dict(pid=f"c{i}", school=f"s{i % 25}", **{"class": int(rng.integers(3, 5)), "group": float(rng.integers(0, 2))}) for i in range(300)]
        return pd.DataFrame(rows)

    def test_school_split_never_splits_a_school(self):
        sp, _ = make_school_split(self.children(), n_candidates=300)
        self.assertEqual(sp.groupby("school").bolum.nunique().max(), 1)
        self.assertEqual(set(sp.bolum), {"train", "val", "test"})
        share = sp.bolum.value_counts(normalize=True)
        self.assertAlmostEqual(share["train"], 0.70, delta=0.12)
        sp2, _ = make_school_split(self.children(), n_candidates=300)
        pd.testing.assert_series_equal(sp.bolum, sp2.bolum)                                # seed ile tekrarlanabilir

    def test_ordinal_logit_probabilities_and_ordering(self):
        rng = np.random.default_rng(0); X = rng.normal(size=(400, 3)); y = np.clip(np.rint(3 + 1.2 * X[:, 0] + rng.normal(0, 0.7, 400)), 1, 5).astype(int)
        m = M.OrdinalLogit(C=1.0).fit(X[:300], y[:300])
        P = m.proba(X[300:])
        np.testing.assert_allclose(P.sum(1), 1.0, atol=1e-6); self.assertTrue((P >= 0).all())
        self.assertGreater(M.metrics(y[300:], m.predict_cont(X[300:]))["spearman"], 0.6)

    def test_ordinal_proba_is_monotone_even_with_conflicting_thresholds(self):
        rng = np.random.default_rng(1); X = rng.normal(size=(200, 2)); y = rng.integers(1, 6, 200)      # sinyalsiz etiket: eşik modelleri çelişebilir
        P = M.OrdinalLogit(C=1.0).fit(X, y).proba(X)
        np.testing.assert_allclose(P.sum(1), 1.0, atol=1e-6); self.assertTrue((P >= -1e-12).all())

    def test_metrics(self):
        y = np.array([1, 2, 3, 4, 5, 3, 2])
        self.assertEqual(M.metrics(y, y.astype(float))["mae"], 0.0); self.assertAlmostEqual(M.metrics(y, y.astype(float))["qwk"], 1.0)
        self.assertAlmostEqual(M.metrics(y, np.full(len(y), 3.0))["qwk"], 0.0)
        self.assertAlmostEqual(M.metrics(np.array([1, 3, 5, 1]), np.array([2, 3, 4, 1]))["mae"], 0.5)

    def synthetic_table(self):
        rng = np.random.default_rng(3); n = 360
        d = pd.DataFrame({"school": [f"s{i % 18}" for i in range(n)], "is_copy": rng.integers(0, 2, n), "family": np.where(rng.integers(0, 2, n), "copy", "dictation"),
                          "f1": rng.normal(size=n), "f2": rng.normal(size=n), "f3": rng.normal(size=n), "image": [f"i{i}.png" for i in range(n)]})
        for t in A.TARGETS:
            d[t] = np.clip(np.rint(3 + d.f1 + rng.normal(0, 0.8, n)), 1, 5)
        sch = sorted(set(d.school)); part = {s: ("train" if i < 11 else "val" if i < 14 else "test") for i, s in enumerate(sch)}
        d["bolum"] = d.school.map(part)
        return d

    def test_model_beats_baseline_on_signal_and_test_lock(self):
        d = self.synthetic_table(); feats = ["f1", "f2", "f3"]
        tab = M.development_table(d, feats, configs=[c for c in M.CONFIGS if c.name in ("baseline_medyan", "OL_secilen_C0.3", "RF_tum")])
        ol = tab[(tab.config == "OL_secilen_C0.3") & (tab.hedef == "layout")].iloc[0]
        self.assertGreater(ol.cv_qwk, 0.4); self.assertGreater(ol.val_qwk, 0.4)
        base = tab[(tab.config == "baseline_medyan") & (tab.hedef == "layout")].iloc[0]
        self.assertLess(base.cv_qwk, 0.2)
        chosen = M.choose(tab); self.assertNotEqual(chosen["layout"], "baseline_medyan")
        with tempfile.TemporaryDirectory() as td, mock.patch.object(M, "LOCK", Path(td) / "lock.json"):
            res, preds = M.final_test(d, feats, chosen)
            self.assertEqual(set(res.hedef), set(A.TARGETS)); self.assertTrue((res.n == (d.bolum == "test").sum()).all())
            with self.assertRaises(RuntimeError):                                             # ikinci kullanım engellenir
                M.final_test(d, feats, chosen)
            self.assertEqual(json.loads((Path(td) / "lock.json").read_text(encoding="utf-8"))["kullanildi"], True)

    def test_occlusion_contributions_ranks_by_sensitivity(self):
        train = pd.DataFrame({"a": [0.0, 1.0, 2.0], "b": [5.0, 5.0, 5.0]})
        row = pd.DataFrame({"a": [10.0], "b": [9.0]})
        top = occlusion_contributions(lambda df: 2.0 * df["a"].values + 0.1 * df["b"].values, row, train, ["a", "b"], top=2)
        self.assertEqual(top[0][0], "a"); self.assertGreater(top[0][1], 10)                   # a: (10 - medyan 1) * 2
        self.assertLess(top[1][1], 1)


if __name__ == "__main__":
    unittest.main()
