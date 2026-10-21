"""Maske, ölçümler, normlar ve rapor için sentetik görüntülerle testler (KIDO gerekmez)."""
import os
import tempfile
import unittest

import numpy as np
import pandas as pd
from PIL import Image

from src.measurements import mask as M
from src.measurements import metrics as X
from src.measurements.metrics import MEASURES, MEASUREMENT_VERSION, color_count, dark_tone_ratio, measure_image
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


def measured(arr):
    return measure_image(cropped(arr))


class CompositionTest(unittest.TestCase):
    def test_center_of_mass_and_box(self):
        arr = page()
        arr[54:104, 104:204] = 0  # kırpılmış sayfada satır 50-99, sütun 100-199
        v = measured(arr)
        self.assertAlmostEqual(v["agirlik_merkezi_x"], 150 / (W - 2 * M.CROP), places=3)
        self.assertAlmostEqual(v["agirlik_merkezi_y"], 75 / (H - 2 * M.CROP), places=3)
        self.assertAlmostEqual(v["kapsayan_kutu_orani"], 100 * 50 / ((W - 2 * M.CROP) * (H - 2 * M.CROP)), places=4)

    def test_empty_page(self):
        v = measured(page())
        self.assertIsNone(v["agirlik_merkezi_x"])
        self.assertEqual((v["kapsayan_kutu_orani"], v["bilesen_sayisi"], v["cizgi_uzunlugu"]), (0, 0, 0))

    def test_region_fill_top_left_only(self):
        mask = np.zeros((90, 120), bool)
        mask[:30, :40] = True
        self.assertEqual(X.region_fill(mask), [1.0] + [0.0] * 8)
        self.assertEqual(len(X.REGIONS), X.GRID ** 2)


class ColorTest(unittest.TestCase):
    def test_entropy_and_warm_share(self):
        arr = page()
        arr[50:150, 50:150] = (220, 30, 30)  # kırmızı (sıcak)
        arr[50:150, 250:350] = (30, 60, 220)  # mavi (soğuk), aynı alan
        v = measured(arr)
        self.assertAlmostEqual(v["renk_entropisi"], 1.0, places=2)  # iki eşit renk: 1 bit
        self.assertAlmostEqual(v["sicak_ton_payi"], 0.5, delta=0.02)
        self.assertGreater(v["ortalama_doygunluk"], 0.8)

    def test_single_color_and_pencil(self):
        red = page()
        red[50:150, 50:150] = (220, 30, 30)
        self.assertEqual(measured(red)["renk_entropisi"], 0.0)
        self.assertEqual(measured(red)["sicak_ton_payi"], 1.0)
        pencil = page()
        pencil[100:110, 50:450] = 150
        v = measured(pencil)
        self.assertIsNone(v["sicak_ton_payi"])  # sıcak da soğuk da yok
        self.assertLess(v["ortalama_doygunluk"], 0.05)

    def test_colorfulness(self):
        self.assertAlmostEqual(X.colorfulness(cropped(page())), 0.0)
        self.assertAlmostEqual(X.colorfulness(cropped(page((128, 128, 128)))), 0.0)
        small, large = page(), page()
        small[100:150, 100:150] = (220, 30, 30)
        large[50:300, 50:450] = (220, 30, 30)
        self.assertGreater(X.colorfulness(cropped(large)), X.colorfulness(cropped(small)))
        self.assertGreater(X.colorfulness(cropped(small)), 10)

    def test_drawing_colorfulness_independent_of_size(self):
        # Çizim piksellerinde: aynı renk, küçük ya da büyük alan, aynı değer; siyah 0; çizim yoksa tanımsız
        small, large, black = page(), page(), page()
        small[100:150, 100:150] = (220, 30, 30)
        large[50:300, 50:450] = (220, 30, 30)
        black[100:150, 100:150] = 0
        v_small, v_large = measured(small)["renklilik_cizim"], measured(large)["renklilik_cizim"]
        self.assertGreater(v_small, 50)
        self.assertAlmostEqual(v_small, v_large, delta=0.1 * v_large)
        self.assertAlmostEqual(measured(black)["renklilik_cizim"], 0.0, delta=1)
        self.assertIsNone(measured(page())["renklilik_cizim"])

    def test_painted_ratio_outline_vs_filled(self):
        outline, filled = page(), page()
        outline[100:250, 100:350] = (30, 60, 220)
        outline[103:247, 103:347] = 255  # 3 piksellik kontur, içi boş
        filled[100:250, 100:350] = (30, 60, 220)
        self.assertLess(measured(outline)["boyama_orani"], 0.05)
        self.assertGreater(measured(filled)["boyama_orani"], 0.95)


class StructureTest(unittest.TestCase):
    def test_line_length_and_thickness(self):
        arr = page()
        arr[180:183, 50:450] = 0  # 400 piksel uzunluğunda, 3 piksel kalınlığında çizgi
        v = measured(arr)
        self.assertAlmostEqual(v["cizgi_uzunlugu"], 400, delta=10)
        self.assertAlmostEqual(v["cizgi_kalinligi"], 3, delta=0.5)

    def test_component_count_ignores_small_parts(self):
        arr = page()
        for x in (50, 200, 350):
            arr[100:130, x:x + 30] = 0
        arr[300:304, 100:104] = 0  # 16 piksel: maskede kalır ama MIN_PART'tan küçük
        self.assertEqual(measured(arr)["bilesen_sayisi"], 3)

    def test_edge_density(self):
        self.assertEqual(measured(page())["kenar_yogunlugu"], 0.0)
        self.assertIsNone(measured(page())["kenar_yogunlugu_cizim"])
        arr = page()
        arr[100:200, 100:300] = 0
        v = measured(arr)
        perimeter = 2 * (100 + 200)
        # Canny keskin geçişi yer yer 2 piksel işaretler: çevre ile iki katı arasında
        page_area = (W - 2 * M.CROP) * (H - 2 * M.CROP)
        self.assertTrue(perimeter / page_area <= v["kenar_yogunlugu"] <= 2 * perimeter / page_area)
        self.assertTrue(perimeter / (100 * 200) <= v["kenar_yogunlugu_cizim"] <= 2 * perimeter / (100 * 200))

    def test_drawing_edge_density_higher_for_lines_than_fills(self):
        # Aynı alan: ince çizgilerden oluşan şekil, düz dolgudan çok daha fazla kenar/çizim pikseli
        lines, fill = page(), page()
        for y in range(100, 300, 10):
            lines[y:y + 3, 100:400] = 0
        fill[100:160, 100:400] = 0
        self.assertGreater(measured(lines)["kenar_yogunlugu_cizim"], 5 * measured(fill)["kenar_yogunlugu_cizim"])

    def test_all_measures_present_in_order(self):
        arr = page()
        arr[100:200, 100:300] = (220, 30, 30)
        self.assertEqual([k for k in measured(arr) if k in MEASURES], list(MEASURES))


class NormsTest(unittest.TestCase):
    def test_percentile_mid_rank(self):
        self.assertEqual(percentile([1, 2, 3, 4], 2.5), 50.0)
        self.assertEqual(percentile([0, 0, 1, 1], 0), 25.0)  # eşitlerin yarısı altta
        self.assertIsNone(percentile([1, 2], None))

    def test_tail_shares(self):
        values = [0] * 10 + list(range(1, 91))  # %10'u 0
        low, high = tail_shares(values, 0)
        self.assertEqual((low, high), (10.0, 100.0))


def synthetic_norms(n, seed=0):
    rng = np.random.default_rng(seed)
    norms = pd.DataFrame({k: rng.uniform(0, 1, n) for k in MEASURES})
    norms["doluluk_orani"] = rng.uniform(0.2, 0.4, n)
    norms["renk_sayisi"] = rng.integers(3, 7, n)
    norms["koyu_ton_orani"] = rng.uniform(0.0, 0.1, n)
    norms["renklilik"] = rng.uniform(20, 60, n)
    norms["renklilik_cizim"] = rng.uniform(40, 120, n)
    norms["kenar_yogunlugu_cizim"] = rng.uniform(0.05, 0.4, n)
    return norms.assign(dosya=[f"x-{i}.jpg" for i in range(n)], sinif=3, duygu="Happiness",
                        surum=MEASUREMENT_VERSION)


class ReportTest(unittest.TestCase):
    def report(self, norms, arr=None):
        from src.report import build_report
        if arr is None:
            arr = page()
            arr[:, : W // 2] = 0  # doluluk 0.5 ve tamamı koyu: grubun üstünde; renk sayısı ve renklilik 0: altında
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "101-3B-1-F-H.jpg")
            Image.fromarray(arr).save(path, quality=95)
            return build_report(path, norms=norms)

    def test_report_structure_and_flags(self):
        from src.report import format_text, save
        n = 200
        r = self.report(synthetic_norms(n))
        self.assertEqual([m["kimlik"] for m in r["olcumler"]], list(MEASURES))  # JSON'da hepsi
        flags = {m["kimlik"]: m["aralik_disi"] for m in r["olcumler"]}
        expected = {"doluluk_orani": "ust", "renk_sayisi": "alt", "koyu_ton_orani": "ust", "renklilik": "alt",
                    "renklilik_cizim": "alt", "kenar_yogunlugu_cizim": "alt"}
        self.assertEqual({k: flags[k] for k in expected}, expected)
        self.assertEqual(r["karsilastirma_grubu"],
                         {"sinif": 3, "gorev": "mutlu", "n": n, "kaynak": "KIDO train", "kucuk": False})
        text = format_text(r)
        self.assertIn("⚠", text)
        for word in ["tanı koy", "risk", "bozukluk", "depresyon"]:
            self.assertNotIn(word, text.lower())
        with tempfile.TemporaryDirectory() as d:
            json_path, txt_path = save(r, os.path.join(d, "out"))
            self.assertTrue(os.path.exists(json_path) and os.path.exists(txt_path))

    def test_text_shows_five_measures_in_order(self):
        from src.report import format_text
        text = format_text(self.report(synthetic_norms(200)))
        names = ["Doluluk oranı", "Farklı renk sayısı", "Renklilik", "Koyu ton oranı", "Detay (kenar yoğunluğu)"]
        positions = [text.find(f"  {name} ") for name in names]
        self.assertTrue(all(p >= 0 for p in positions), positions)
        self.assertEqual(positions, sorted(positions))
        for hidden in ["Ağırlık merkezi", "Boyama oranı", "Bağlı bileşen", "Renk entropisi", "Bölge doluluğu",
                       "sayfa"]:
            self.assertNotIn(hidden, text)
        r = self.report(synthetic_norms(200))
        shown = {m["kimlik"]: m for m in r["olcumler"]}
        self.assertIn(f"{shown['renklilik_cizim']['deger']:.1f}".replace(".", ","), text)

    def test_small_group_note_instead_of_flags(self):
        from src.report import MIN_GROUP, format_text
        r = self.report(synthetic_norms(MIN_GROUP - 1))
        self.assertTrue(r["karsilastirma_grubu"]["kucuk"])
        self.assertTrue(all(m["aralik_disi"] is None for m in r["olcumler"]))
        self.assertTrue(all(m["yuzdelik"] is not None for m in r["olcumler"] if m["deger"] is not None))
        text = format_text(r)
        self.assertNotIn("⚠", text)
        self.assertIn(f"karşılaştırma grubu küçük (n={MIN_GROUP - 1})", text)

    def test_tiny_drawing_no_flags_on_per_drawing_measures(self):
        from src.measurements.metrics import PER_DRAWING_MEASURES
        from src.report import MIN_FILL, SMALL_DRAWING_MESSAGE, format_text
        arr = page()
        for y in range(120, 220, 25):
            arr[y:y + 2, 150:350] = 0  # ince siyah çizgiler: doluluk ≈ 0,009, koyu ton 1, renklilik 0
        r = self.report(synthetic_norms(200), arr)
        by_key = {m["kimlik"]: m for m in r["olcumler"]}
        self.assertLess(by_key["doluluk_orani"]["deger"], MIN_FILL)
        self.assertEqual(by_key["doluluk_orani"]["aralik_disi"], "alt")  # doluluk kendisi oransal değil: ⚠ kalır
        for k in PER_DRAWING_MEASURES:
            self.assertIsNone(by_key[k]["aralik_disi"], k)
        self.assertIsNotNone(by_key["renklilik_cizim"]["yuzdelik"])  # yüzdelik gösterilir
        quality = {q["kimlik"]: q for q in r["kalite"]}
        self.assertTrue(quality["kucuk_cizim"]["bayrak"])
        text = format_text(r)
        self.assertIn(SMALL_DRAWING_MESSAGE, text)
        flagged = [line for line in text.splitlines() if line.endswith("⚠")]
        self.assertTrue(all(line.strip().startswith(("Doluluk", "Farklı renk")) for line in flagged), flagged)

    def test_normal_drawing_has_no_small_drawing_note(self):
        from src.report import SMALL_DRAWING_MESSAGE, format_text
        r = self.report(synthetic_norms(200))
        self.assertFalse({q["kimlik"]: q for q in r["kalite"]}["kucuk_cizim"]["bayrak"])
        self.assertNotIn(SMALL_DRAWING_MESSAGE, format_text(r))


if __name__ == "__main__":
    unittest.main()
