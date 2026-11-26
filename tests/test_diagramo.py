"""DiaGraMo: SVC okuma, vuruş ayırma, koordinat → PNG dönüşümü ve etiket yardımcıları (sentetik veri; gerçek dosya gerekmez)."""
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.handwriting.diagramo.io import COLUMNS, parse_name, read_svc, read_svc_bytes, task_kind
from src.handwriting.diagramo.labels import CATALOG, auc_vs_group, label_table
from src.handwriting.diagramo.render import TABLET_MM, render_strokes, render_svc, split_strokes
from src.handwriting.diagramo.samples import build_table, select_samples


def frame(runs, dt=0.005):
    """runs: [(pen, [(x, y), ...]), ...] ardışık kayıtlar; zaman dt aralıklı."""
    rows, t = [], 0.0
    for pen, pts in runs:
        for x, y in pts:
            rows.append((x, y, t, pen, 100.0, 50.0, 500.0 if pen else 0.0)); t += dt
    return pd.DataFrame(rows, columns=COLUMNS)


def line(x0, x1, y, n=50):
    return [(float(x), float(y)) for x in np.linspace(x0, x1, n)]


class TestIo(unittest.TestCase):
    def test_parse_name_and_kind(self):
        d = parse_name("BR10301_TSK3(TA)-dictation-3_1.svc")
        self.assertEqual((d["pid"], d["no"], d["task"], d["ver"], d["ext"]), ("BR10301", 3, "dictation-3", 1, "svc"))
        self.assertEqual(task_kind("dictation-4"), "writing"); self.assertEqual(task_kind("copy-3"), "writing")
        self.assertEqual(task_kind("RCFT-recall"), "rcft"); self.assertEqual(task_kind("big-spiral-fast"), "element")
        with self.assertRaises(ValueError):
            parse_name("readme.txt")

    def test_read_svc_header_and_columns(self):
        body = "1.5 2.5 0.000 1 100 50 300\n1.6 2.6 0.005 0 100 50 0\n"
        df = read_svc_bytes(("2\n" + body).encode())
        self.assertEqual(list(df.columns), COLUMNS)
        self.assertEqual((len(df), df.attrs["header_n"]), (2, 2))
        self.assertEqual(df.pen.tolist(), [1, 0])
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.svc"; p.write_bytes(("2\n" + body).encode())
            self.assertEqual(len(read_svc(p)), 2)


class TestSplit(unittest.TestCase):
    def test_pen_up_points_are_dropped_and_split(self):
        df = frame([(1, line(0, 10, 5)), (0, line(10, 20, 5)), (1, line(20, 30, 5))])
        s = split_strokes(df)
        self.assertEqual(len(s), 2)
        self.assertAlmostEqual(s[0][:, 0].max(), 10); self.assertAlmostEqual(s[1][:, 0].min(), 20)  # havadaki 10–20 mm çizilmez
        self.assertEqual(sum(len(x) for x in s), 100)

    def test_time_gap_and_jump_split_pen_down_runs(self):
        a, b = frame([(1, line(0, 10, 5))]), frame([(1, line(12, 20, 5))])
        b["t"] += a.t.max() + 1.0                                   # 1 s zaman boşluğu, pen hep 1
        self.assertEqual(len(split_strokes(pd.concat([a, b], ignore_index=True))), 2)
        c = frame([(1, line(0, 10, 5) + line(80, 90, 5))])           # 70 mm sıçrama, zaman sürekli
        self.assertEqual(len(split_strokes(c)), 2)
        self.assertEqual(len(split_strokes(c, max_jump_mm=1000)), 1)

    def test_no_pen_down(self):
        self.assertEqual(split_strokes(frame([(0, line(0, 10, 5))])), [])
        with self.assertRaises(ValueError):
            render_strokes([])


def dark_cols(img, row=None):
    a = np.asarray(img) < 128
    return a.any(0) if row is None else a[row]


class TestRender(unittest.TestCase):
    def test_pen_up_gap_is_not_connected(self):
        s = split_strokes(frame([(1, line(20, 30, 50)), (0, line(30, 40, 50)), (1, line(40, 50, 50))]))
        r = render_strokes(s, px_per_mm=5, margin_mm=5, y_up=False)
        cols = dark_cols(r.image)
        mid = int(round((35 - r.origin_mm[0]) * 5))                 # iki vuruş arası (35 mm)
        self.assertFalse(cols[mid - 2:mid + 3].any())               # boşluk beyaz
        self.assertTrue(cols[int(round((25 - r.origin_mm[0]) * 5))] and cols[int(round((45 - r.origin_mm[0]) * 5))])

    def test_physical_scale_and_aspect_ratio(self):
        s = [np.array(line(10, 110, 20)), np.array(line(10, 110, 70))]     # 100 mm x 50 mm kutu
        for ppm in (3.0, 6.0):
            r = render_strokes(s, px_per_mm=ppm, margin_mm=5, y_up=False)
            self.assertAlmostEqual(r.image.width / ppm, 100 + 10, delta=0.6)
            self.assertAlmostEqual(r.image.height / ppm, 50 + 10, delta=0.6)
        r = render_strokes(s, px_per_mm=6.0, margin_mm=5, y_up=False)
        xs = np.flatnonzero(dark_cols(r.image)); self.assertAlmostEqual((xs.max() - xs.min()) / 6.0, 100, delta=1.0)   # yazı 100 mm
        self.assertAlmostEqual(r.image.width / r.image.height, 110 / 60, delta=0.03)

    def test_fit_mode_keeps_aspect_and_scales_each_sample_independently(self):
        wide = [np.array(line(0, 200, 10)), np.array(line(0, 200, 60))]
        small = [np.array(line(0, 20, 5)), np.array(line(0, 20, 10))]
        a, b = render_strokes(wide, fit_px=1000, margin_mm=5, y_up=False), render_strokes(small, fit_px=1000, margin_mm=5, y_up=False)
        self.assertEqual(max(a.image.size), 1000); self.assertEqual(max(b.image.size), 1000)            # her örnek kendi ölçeğinde
        self.assertAlmostEqual(a.image.width / a.image.height, 210 / 60, delta=0.05)
        self.assertAlmostEqual(b.image.width / b.image.height, 30 / 15, delta=0.05)
        self.assertNotAlmostEqual(a.px_per_mm, b.px_per_mm, places=1)

    def test_y_axis_orientation(self):
        stroke = [np.array([(50.0, 10.0), (50.0, 100.0)])]                  # tablet: y=100 üstte (y yukarı)
        up = render_strokes(stroke, px_per_mm=4, margin_mm=5, y_up=True)
        rows = np.flatnonzero((np.asarray(up.image) < 128).any(1))
        self.assertAlmostEqual(up.bbox_mm[1], TABLET_MM[1] - 100, delta=1e-6)            # üst uç görüntüde küçük y
        down = render_strokes(stroke, px_per_mm=4, margin_mm=5, y_up=False)
        self.assertAlmostEqual(down.bbox_mm[1], 10, delta=1e-6)
        # yukarı akışlı yazı: ilk nokta (y=100'e doğru) ters çevrilince üstte kalır
        self.assertGreater(rows.max() - rows.min(), 85 * 4)

    def test_default_orientation_is_y_up(self):
        # varsayılan (y_up verilmeden): tablet y=100 (üstte) görüntüde üst kenara yakın olmalı; üretim (samples.py) varsayılana güvenir
        stroke = [np.array([(50.0, 10.0), (50.0, 100.0)])]
        r = render_strokes(stroke, px_per_mm=4, margin_mm=5)
        self.assertAlmostEqual(r.bbox_mm[1], TABLET_MM[1] - 100, delta=1e-6)
        # dikte benzeri: yazı aşağı ilerlerken tablet y'si azalır → görüntüde ilk satır üstte (ilk vuruşun satırı < son vuruşun satırı)
        first, last = np.array(line(20, 80, 150)), np.array(line(20, 80, 60))
        rr = render_strokes([first, last], px_per_mm=4, margin_mm=5)
        rows = np.flatnonzero((np.asarray(rr.image) < 128).any(1))
        self.assertLess(rows[:3].mean() , rows[-3:].mean())
        self.assertAlmostEqual(rr.bbox_mm[1], TABLET_MM[1] - 150, delta=1e-6)

    def test_tablet_canvas_and_fixed_line_width(self):
        s = [np.array(line(100, 200, 100))]
        r = render_strokes(s, px_per_mm=2, canvas="tablet", y_up=False, line_px=3)
        self.assertEqual(r.image.size, (round(TABLET_MM[0] * 2), round(TABLET_MM[1] * 2)))
        for ppm in (2.0, 5.0, 8.0):                                          # çizgi kalınlığı ölçekten bağımsız (piksel)
            im = render_strokes(s, px_per_mm=ppm, margin_mm=5, y_up=False, line_px=3).image
            col = (np.asarray(im)[:, im.width // 2] < 128).sum()
            self.assertIn(col, (3, 4), (ppm, col))

    def test_single_point_stroke_draws_dot_and_white_background(self):
        r = render_strokes([np.array([(10.0, 10.0)]), np.array(line(30, 40, 10))], px_per_mm=5, margin_mm=5, y_up=False)
        a = np.asarray(r.image)
        self.assertEqual(a.max(), 255); self.assertTrue((a[:, :3] == 255).all())            # beyaz arka plan
        self.assertTrue((a[:, : int(8 * 5)] < 128).any())                                      # nokta çizildi

    def test_render_svc_roundtrip_and_air_points_ignored(self):
        df = frame([(0, line(0, 300, 5)), (1, line(40, 80, 50)), (0, line(80, 200, 50))])      # uzun havada hareket çizilmemeli
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.svc"
            p.write_text(f"{len(df)}\n" + "\n".join(" ".join(f"{v:.6f}" for v in r) for r in df.itertuples(index=False)), encoding="utf-8")
            r = render_svc(p, px_per_mm=4, margin_mm=5, y_up=False)
        self.assertEqual(r.n_strokes, 1)
        self.assertAlmostEqual(r.image.width / 4, 40 + 10, delta=0.6)                           # yalnız 40 mm'lik yüzey hareketi


class TestSamplesAndLabels(unittest.TestCase):
    def fake(self):
        rows = []
        for i in range(60):
            for task, kind in [("dictation-3", "writing"), ("dictation-4", "writing"), ("copy-3", "writing"), ("copy-4", "writing"),
                               ("big-spiral-fast", "element"), ("saw-fast", "element"), ("combined-loops-fast", "element"), ("lower-loops-precise", "element")]:
                rows.append(dict(pid=f"P{i:03d}", task=task, kind=kind, path=f"P{i:03d}/x_{task}.svc", group=float(i % 2), hls_dictat_sum=5 + i % 20, hls_transcript_sum=6 + i % 19))
        return pd.DataFrame(rows)

    def test_select_samples(self):
        picks = select_samples(self.fake())
        self.assertEqual(len(picks), 16)
        pids = [r.pid for r, _ in picks]
        self.assertEqual(len(set(pids)), 16)                                                    # katılımcı tekrarı yok
        kinds = [r.kind for r, _ in picks]
        self.assertEqual((kinds.count("writing"), kinds.count("element")), (12, 4))
        self.assertEqual({(r.task, r.group) for r, w in picks[:8]}, {(t, g) for t in ["dictation-3", "dictation-4", "copy-3", "copy-4"] for g in (0.0, 1.0)})

    def test_auc_and_table(self):
        self.assertEqual(auc_vs_group([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], [0] * 6 + [1] * 6), 1.0)
        self.assertEqual(auc_vs_group([5] * 12, [0] * 6 + [1] * 6), 0.5)
        part = pd.DataFrame({"group": [0.0, 1.0] * 10, **{v[0]: np.arange(20) for v in CATALOG if v[0] != "group"}})
        part["group"] = [0.0, 1.0] * 10
        t = label_table(part)
        self.assertEqual(len(t), len(CATALOG)); self.assertTrue((t.eksik.dropna() == 0).all())

    def test_build_table_only_usable_participants(self):
        inv = self.fake()[["pid", "task", "kind", "path"]]
        part = pd.DataFrame({"id_participant": ["P000", "P001"], "group": [0.0, 1.0], "hls_transcript_sum": ["12", "x"]})
        t = build_table(inv, part)
        self.assertEqual(set(t.pid), {"P000", "P001"})
        self.assertTrue(pd.isna(t[t.pid == "P001"].hls_transcript_sum).all())                  # sayısal olmayan değer eksik olur


if __name__ == "__main__":
    unittest.main()
