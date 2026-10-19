"""Maske, ölçümler, normlar ve rapor için sentetik görüntülerle testler (KIDO gerekmez)."""
import os
import tempfile
import unittest

import numpy as np
import pandas as pd
from PIL import Image

from src.measurements import mask as M
from src.measurements.metrics import MEASUREMENT_VERSION, color_count, dark_tone_ratio, measure_image
from src.measurements.norms import percentile, tail_shares

W, H = 512, 362  # KIDO görüntü boyutu


def page(color=(255, 255, 255)):
    return np.full((H, W, 3), color, np.uint8)


def cropped(arr):
    # load_drawing gibi: kenarlardan CROP piksel kırpılmış RGB görüntü
    return M.crop_border(Image.fromarray(arr))


def mask_of(arr):
    return M.drawing_mask(M.to_hsv(cropped(arr)))


class MaskTest(unittest.TestCase):
    def test_blank_page_is_empty(self):
        self.assertEqual(mask_of(page()).sum(), 0)

    def test_half_black_fill_is_half(self):
        arr = page()
        arr[:, : W // 2] = 0
        self.assertAlmostEqual(mask_of(arr).mean(), 0.5, delta=0.02)

    def test_faint_gray_ghost_is_not_drawing(self):
        # Silinmiş kalem / arka yüz izi: V ≈ 238, renksiz, bağımsız
        arr = page()
        arr[100:200, 100:300] = 238
        self.assertEqual(mask_of(arr).sum(), 0)

    def test_pencil_line_is_drawing(self):
        arr = page()
        arr[180:182, 50:450] = 150  # 2 piksel kalınlığında gri kalem çizgisi
        self.assertGreater(mask_of(arr).sum(), 700)

    def test_hysteresis_keeps_faint_color_attached_to_stroke(self):
        # Koyu çizginin devamı soluk sarı (S ≈ 25: kesin eşiğin altı, gevşek eşiğin üstü)
        arr = page()
        arr[180:184, 50:200] = 60
        arr[180:184, 200:400] = (255, 250, 230)
        isolated = page()
        isolated[180:184, 200:400] = (255, 250, 230)
        self.assertGreater(mask_of(arr)[176:180, 200 - M.CROP:400 - M.CROP].mean(), 0.9)
        self.assertEqual(mask_of(isolated).sum(), 0)  # bağlı olmadığında girmez

    def test_small_specks_removed(self):
        arr = page()
        arr[100, 100] = arr[200, 300] = 0
        self.assertEqual(mask_of(arr).sum(), 0)

    def test_scan_edge_line_removed(self):
        arr = page()
        arr[:, 6:8] = 40  # kırpmadan sonra da kalan dikey tarama çizgisi
        self.assertEqual(mask_of(arr).sum(), 0)

    def test_painted_region_touching_edge_kept(self):
        arr = page()
        arr[:, :200] = (30, 120, 220)  # kenara değen mavi boyama
        self.assertGreater(mask_of(arr).mean(), 0.35)


class FaintFlagTest(unittest.TestCase):
    def test_pale_cyan_clusters_flagged(self):
        arr = page()
        for x in range(60, 460, 40):  # soluk camgöbeği yağmur çizgileri (S ≈ 16)
            arr[60:120, x:x + 3] = (240, 255, 255)
        img = cropped(arr)
        hsv = M.to_hsv(img)
        self.assertGreaterEqual(M.faint_color_ratio(hsv, M.drawing_mask(hsv)), M.FAINT_FLAG)
        self.assertTrue(measure_image(img)["soluk_renk_bayragi"])

    def test_clean_page_not_flagged(self):
        arr = page()
        arr[150:200, 150:300] = 0
        self.assertFalse(measure_image(cropped(arr))["soluk_renk_bayragi"])


class MetricsTest(unittest.TestCase):
    def test_three_hues_three_colors(self):
        arr = page()
        arr[50:150, 50:150] = (220, 30, 30)  # kırmızı
        arr[50:150, 200:300] = (30, 180, 30)  # yeşil
        arr[50:150, 350:450] = (30, 60, 220)  # mavi
        arr[200:300, 50:450] = 0  # siyah ve gri renk sayılmaz
        arr[310:330, 50:450] = 128
        img = cropped(arr)
        hsv = M.to_hsv(img)
        self.assertEqual(color_count(hsv, M.drawing_mask(hsv)), 3)

    def test_pencil_only_zero_colors(self):
        arr = page()
        arr[100:110, 50:450] = 150
        self.assertEqual(measure_image(cropped(arr))["renk_sayisi"], 0)

    def test_dark_tone_ratio(self):
        arr = page()
        arr[50:150, 50:250] = 0  # 200 x 100 siyah
        arr[200:300, 50:250] = (220, 30, 30)  # aynı alanda kırmızı
        img = cropped(arr)
        hsv = M.to_hsv(img)
        self.assertAlmostEqual(dark_tone_ratio(hsv, M.drawing_mask(hsv)), 0.5, delta=0.02)

    def test_dark_tone_undefined_without_drawing(self):
        self.assertIsNone(measure_image(cropped(page()))["koyu_ton_orani"])


class NormsTest(unittest.TestCase):
    def test_percentile_mid_rank(self):
        self.assertEqual(percentile([1, 2, 3, 4], 2.5), 50.0)
        self.assertEqual(percentile([0, 0, 1, 1], 0), 25.0)  # eşitlerin yarısı altta
        self.assertIsNone(percentile([1, 2], None))

    def test_tail_shares(self):
        values = [0] * 10 + list(range(1, 91))  # %10'u 0
        low, high = tail_shares(values, 0)
        self.assertEqual((low, high), (10.0, 100.0))


class ReportTest(unittest.TestCase):
    def test_report_structure_and_flags(self):
        from src.report import build_report, format_text, save
        rng = np.random.default_rng(0)
        n = 200
        norms = pd.DataFrame({"dosya": [f"x-{i}.jpg" for i in range(n)], "sinif": 3, "duygu": "Happiness",
                              "doluluk_orani": rng.uniform(0.2, 0.4, n), "renk_sayisi": rng.integers(3, 7, n),
                              "koyu_ton_orani": rng.uniform(0.0, 0.1, n), "surum": MEASUREMENT_VERSION})
        arr = page()
        arr[:, : W // 2] = 0  # doluluk 0.5 ve tamamı koyu: ikisi de grubun üstünde, renk 0: altında
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "101-3B-1-F-H.jpg")
            Image.fromarray(arr).save(path, quality=95)
            r = build_report(path, norms=norms)
            flags = {m["kimlik"]: m["aralik_disi"] for m in r["olcumler"]}
            self.assertEqual(flags, {"doluluk_orani": "ust", "renk_sayisi": "alt", "koyu_ton_orani": "ust"})
            self.assertEqual(r["karsilastirma_grubu"], {"sinif": 3, "gorev": "mutlu", "n": n, "kaynak": "KIDO train"})
            text = format_text(r)
            self.assertIn("⚠", text)
            for word in ["tanı koy", "risk", "bozukluk", "depresyon"]:
                self.assertNotIn(word, text.lower())
            json_path, txt_path = save(r, os.path.join(d, "out"))
            self.assertTrue(os.path.exists(json_path) and os.path.exists(txt_path))


if __name__ == "__main__":
    unittest.main()
