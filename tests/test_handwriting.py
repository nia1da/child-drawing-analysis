"""El yazısı prototipi: sentetik sayfalarla (gerçek veri yok, Colab'da da koşar) birim ve dayanıklılık testleri."""
import os
import unittest
from unittest import mock

import numpy as np
from scipy import ndimage as ndi

from src.handwriting import paths
from src.handwriting.masks import regularize
from src.handwriting.pipeline import analyze_page
from src.handwriting.synthetic import make_layout, render


def run(layout, dpi=150, **kw):
    rgb, truth, boxes, _ = render(layout, dpi=dpi, **kw)
    return analyze_page(rgb, dpi, boxes), truth


class TestPaths(unittest.TestCase):
    def test_colab_is_refused(self):
        with mock.patch.dict(os.environ, {"CIZIM_ENV": "colab"}):
            with self.assertRaises(RuntimeError):
                paths.fd_lex_dir()

    def test_colab_release_tag_is_refused(self):
        env = {k: v for k, v in os.environ.items() if k != "CIZIM_ENV"}
        env["COLAB_RELEASE_TAG"] = "x"
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(RuntimeError):
                paths.fd_lex_dir()

    def test_cloud_paths_are_refused(self):
        for bad in ["C:/Users/x/OneDrive/data", "H:/My Drive/bitirme/fd_lex", "/content/drive/MyDrive/bitirme/x",
                    "/content/drive/MyDrive/fd_lex", "D:/MyDrive/x", "/mnt/gdrive/x", "/content/drive/other/x"]:
            with self.assertRaises(RuntimeError, msg=bad):
                paths.check_data_dir(bad)

    def test_local_repo_path_is_accepted(self):
        with mock.patch.dict(os.environ, {"CIZIM_ENV": "local"}):
            self.assertTrue(str(paths.fd_lex_dir()).endswith("fd_lex"))


class TestPipelineOnSynthetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = make_layout(seed=1, slope_deg=0.3)
        cls.res, cls.hw_truth = run(cls.layout, skew_deg=0.4)
        cls.t = cls.layout.truth

    def test_scale_and_rules(self):
        f = self.res.features
        self.assertEqual(f["n_rules"], self.t["n_rules"])
        self.assertAlmostEqual(f["rule_spacing_mm"], self.t["spacing_mm"], delta=0.15)

    def test_skew_is_recovered(self):
        # pre.skew_deg düzeltme açısıdır: +0,4° eğik sayfa için -0,4° (işaret sınanır)
        self.assertAlmostEqual(self.res.pre.skew_deg, -0.4, delta=0.1)

    def test_lines_found(self):
        self.assertEqual(self.res.features["used_lines"], self.t["used_lines"])
        self.assertEqual(self.res.seg.used, self.t["used_idx"])

    def test_size_and_alignment_close_to_truth(self):
        f = self.res.features
        self.assertAlmostEqual(f["xheight_mm"], self.t["xh_ink_mm"], delta=0.10 * self.t["xh_ink_mm"])
        self.assertAlmostEqual(f["baseline_offset_mm_median"], self.t["baseline_offset_ink_mm"], delta=0.3)
        self.assertAlmostEqual(f["baseline_slope_deg_median"], self.t["slope_deg"], delta=0.15)
        self.assertAlmostEqual(f["left_margin_mm"], self.t["left_margin_mm"], delta=1.5)

    def test_printed_structures_are_removed(self):
        m = self.res.masks
        self.assertTrue(m.flags["code_box_found"])
        self.assertGreater(m.flags["overlay_masked_px"], 0)  # XXX gerçekten maskelendi (mask yokken karanlık pikseller vardı)
        self.assertGreater(int((m.dark & m.box_mask & m.roi).sum()), 0)  # kutu ROI içine giriyor, yani maskelenmesi gerekiyordu

    def test_no_stray_ink_outside_written_lines(self):
        m, seg = self.res.masks, self.res.seg
        below = int(m.rules.y[max(seg.used)] + 0.4 * m.rules.spacing_px)
        self.assertLess(int(m.hw[below:].sum()), 0.01 * int(m.hw.sum()))

    def test_handwriting_mask_agrees_with_truth(self):
        # düzeltilmiş sayfa = eğiksiz düzen: gerçek maske aynı düzenin eğiksiz render'ı
        truth = render(self.layout, dpi=150, skew_deg=0.0)[1]
        got = self.res.masks.hw
        ratio = got.sum() / truth.sum()
        self.assertTrue(0.85 < ratio < 1.25, ratio)  # ölçülen ≈ 1,09 (köprü şişmesi)
        leak = got & ~ndi.binary_dilation(truth, iterations=3)  # gerçek vuruşlardan 3 px uzak "el yazısı" = sızıntı (çizgi, kutu, XXX, telif)
        self.assertLess(int(leak.sum()), 0.01 * int(got.sum()))


class TestRobustness(unittest.TestCase):
    def setUp(self):
        self.layout = make_layout(seed=2, slope_deg=0.2)
        self.base, _ = run(self.layout, skew_deg=0.3)

    def close(self, other, tol_h=0.1, tol_off=0.25, tol_slope=0.15):
        a, b = self.base.features, other.features
        self.assertAlmostEqual(a["xheight_mm"], b["xheight_mm"], delta=tol_h * a["xheight_mm"])
        self.assertAlmostEqual(a["baseline_offset_mm_median"], b["baseline_offset_mm_median"], delta=tol_off)
        self.assertAlmostEqual(a["baseline_slope_deg_median"], b["baseline_slope_deg_median"], delta=tol_slope)
        self.assertEqual(a["used_lines"], b["used_lines"])

    def test_resolution_sensitivity(self):
        for dpi in (200, 300):
            res, _ = run(self.layout, dpi=dpi, skew_deg=0.3)
            self.assertEqual(res.pre.dpi, 150.0)  # ortak çalışma çözünürlüğüne indirildi
            self.close(res)

    def test_pen_colour(self):
        for pen in ("black", "pencil"):
            res, _ = run(self.layout, pen=pen, skew_deg=0.3)
            self.close(res, tol_h=0.12)

    def test_jpeg_noise_and_background(self):
        res, _ = run(self.layout, skew_deg=0.3, jpeg_quality=40, noise=8.0, gradient=20.0)
        self.close(res, tol_h=0.12)

    def test_low_resolution_is_flagged_not_upsampled(self):
        res, _ = run(self.layout, dpi=100, skew_deg=0.3)
        self.assertTrue(res.quality.get("low_resolution"))
        self.assertEqual(res.pre.dpi, 100.0)

    def test_skipped_line_and_page_use(self):
        lay = make_layout(seed=3, used_lines=10, skip_lines=(4,))
        res, _ = run(lay)
        self.assertEqual(res.seg.used, lay.truth["used_idx"])
        self.assertNotIn(4, res.seg.used)
        self.assertAlmostEqual(res.features["used_frac"], 9 / 23, places=2)

    def test_size_ordering_is_preserved(self):
        small = run(make_layout(seed=4, xh_mm=2.4))[0].features["xheight_mm"]
        large = run(make_layout(seed=4, xh_mm=4.2))[0].features["xheight_mm"]
        self.assertGreater(large, small * 1.4)

    def test_wobble_ordering_is_preserved(self):
        calm = run(make_layout(seed=5, wobble_mm=0.02))[0].features["baseline_wobble_mm_median"]
        shaky = run(make_layout(seed=5, wobble_mm=0.5))[0].features["baseline_wobble_mm_median"]
        self.assertGreater(shaky, 2 * calm)


class TestRulesAndBox(unittest.TestCase):
    def test_wide_code_box_is_not_taken_for_rules(self):
        for x0 in (144.0, 130.0):  # kutu 56 ve 70 mm
            lay = make_layout(seed=1, slope_deg=0.3)
            lay.box_mm = (x0, 22.0, 200.0, 36.0)
            res, _ = run(lay, skew_deg=0.3)
            self.assertEqual(res.features["n_rules"], 23, x0)
            self.assertTrue(res.quality["code_box_found"], x0)
            self.assertEqual(res.seg.used, lay.truth["used_idx"], x0)

    def test_missing_rule_is_filled_end_to_end(self):
        lay = make_layout(seed=1, slope_deg=0.3)
        rgb, _, boxes, _ = render(lay, dpi=150, skew_deg=0.0)
        base = analyze_page(rgb, 150, boxes)
        y = int(round(lay.rules_mm[14] * 150 / 25.4))
        rgb2 = rgb.copy(); rgb2[y - 4:y + 6, :] = 250  # 15. çizgiyi sil (yazının uzağında)
        res = analyze_page(rgb2, 150, boxes)
        self.assertEqual(res.features["n_rules"], 23)
        self.assertEqual(res.quality["rules_filled"], 1)
        self.assertEqual(res.seg.used, base.seg.used)
        self.assertAlmostEqual(res.features["baseline_offset_mm_median"], base.features["baseline_offset_mm_median"], delta=0.05)

    def test_irregular_spacing_flags(self):
        res, _ = run(make_layout(seed=1, spacing_mm=9.0))
        self.assertTrue(res.quality["rule_spacing_off"])
        self.assertFalse(run(make_layout(seed=1))[0].quality["rule_spacing_off"])

    def test_regularize_cases(self):
        full = 100 + 64.0 * np.arange(10)
        self.assertEqual(regularize(full)[1:], (0, 0))                                   # tam set: değişmez
        y, added, removed = regularize(np.delete(full, [3, 4]))                         # iç boşluk: tamamlanır
        self.assertEqual((len(y), added, removed), (10, 2, 0))
        y, added, removed = regularize(np.sort(np.append(full, 132.0)))                 # yarım aralıkta sahte çizgi: atılır
        self.assertEqual((len(y), added, removed), (10, 0, 1))
        y, added, removed = regularize(np.sort(np.append(full, full[5] + 3)))           # 3 px arayla bölünmüş çizgi: tek çizgi
        self.assertEqual((len(y), removed), (10, 1))
        y, added, removed = regularize(full[1:])                                         # baştaki eksik tamamlanmaz (bilinen sınır)
        self.assertEqual((len(y), added), (9, 0))
        np.testing.assert_allclose(regularize(np.delete(full, 4))[0][[0, 1, 4]], full[[0, 1, 4]], atol=0.5)
        # bulunan çizgilerin y'si korunur: ızgaradan ±2 px sapan ama uyan girdide çıktı girdiyle birebir aynı (eksik çizgi hariç)
        rng = np.random.default_rng(0)
        jit = np.delete(full + rng.uniform(-2, 2, len(full)), 4)
        out, added, removed = regularize(jit)
        self.assertEqual((len(out), added, removed), (10, 1, 0))
        np.testing.assert_array_equal(np.delete(out, 4), jit)
        # aşırı boşluk: tamamlama yapılmaz
        sparse = np.array([100.0, 100 + 64 * 5, 100 + 64 * 11, 100 + 64 * 16, 100 + 64 * 22])
        self.assertEqual(regularize(sparse)[1:], (0, 0))


class TestPageWithoutRules(unittest.TestCase):
    def test_blank_page_does_not_crash(self):
        rgb = np.full((1754, 1240, 3), 250, np.uint8)
        res = analyze_page(rgb, 150)
        self.assertTrue(res.quality["no_rules"])
        self.assertEqual(res.features["used_lines"], 0)


if __name__ == "__main__":
    unittest.main()
