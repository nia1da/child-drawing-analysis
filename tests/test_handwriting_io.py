"""El yazısı: izin geçidi, PDF okuma (sentetik PDF), bölme, pilot seçimi/çalıştırma, rapor ve işaretli bölgeler. Gerçek veri yok."""
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from src.handwriting import paths
from src.handwriting.pdf_io import load_page, render_page
from src.handwriting.pilot import failure_checks, run_pilot, select_pilot
from src.handwriting.pipeline import analyze_page
from src.handwriting.report import MEASURES, build_report, percentile_rank, render_text
from src.handwriting.splits import dpi_balance, make_splits, make_splits_with_rule, write_splits
from src.handwriting.synthetic import make_layout, make_pdf, render
from src.handwriting.viz import annotate_regions, outlier_components


def good_page(seed=1, **kw):
    lay = make_layout(seed=seed, slope_deg=0.3, **kw)
    rgb, _, boxes, _ = render(lay, dpi=150, skew_deg=0.3)
    return lay, analyze_page(rgb, 150, boxes)


class TestPermissionGate(unittest.TestCase):
    def test_gate(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(PermissionError):
                paths.require_permission(d)                      # dosya yok
            (Path(d) / "permission.json").write_text(json.dumps({"approved": False}), encoding="utf-8")
            with self.assertRaises(PermissionError):
                paths.require_permission(d)                      # onaylı değil
            with self.assertRaises(PermissionError):
                load_page("x.pdf", 1, root=d)                    # okuma kodu da geçide bağlı
            (Path(d) / "permission.json").write_text(json.dumps({"approved": True}), encoding="utf-8")
            self.assertEqual(paths.require_permission(d), Path(d).resolve())


class TestPdfIo(unittest.TestCase):
    def test_overlay_boxes_follow_page_rotation(self):
        lay = make_layout(seed=1, slope_deg=0.3)
        with tempfile.TemporaryDirectory() as d:
            dark = {}
            for rot in (0, 90, 180, 270):
                make_pdf(Path(d) / f"p{rot}.pdf", lay, rotation=rot, skew_deg=0.3)
                rgb, boxes = render_page(Path(d) / f"p{rot}.pdf", 0, 150)
                self.assertEqual(len(boxes), 5)  # telif satırı 4 kelime + XXX
                g = rgb.mean(2)
                dark[rot] = np.mean([(g[max(0, y0):y1, max(0, x0):x1] < 100).mean() for x0, y0, x1, y1 in boxes])
                self.assertEqual(rgb.shape[:2], (1241, 1754) if rot in (90, 270) else (1754, 1241))
            # kutular her dönüşte aynı yazı pikselleri üzerinde (yanlış dönüşte ≈ 0 olurdu)
            for rot in (90, 180, 270):
                self.assertGreater(dark[rot], 0.03)
                self.assertAlmostEqual(dark[rot], dark[0], delta=0.02)

    def test_pipeline_from_pdf(self):
        lay = make_layout(seed=1, slope_deg=0.3)
        with tempfile.TemporaryDirectory() as d:
            make_pdf(Path(d) / "p.pdf", lay, skew_deg=0.3)
            rgb, boxes = render_page(Path(d) / "p.pdf", 0, 150)
        res = analyze_page(rgb, 150, boxes)
        self.assertEqual(res.seg.used, lay.truth["used_idx"])
        self.assertAlmostEqual(res.features["xheight_mm"], lay.truth["xh_ink_mm"], delta=0.15 * lay.truth["xh_ink_mm"])
        self.assertGreater(res.quality["overlay_masked_px"], 0)


def fake_manifest(n_students=120, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_students):
        code = f"S{i:04d}"
        cls = "KLASSE_5" if i % 2 == 0 else "KLASSE_9"
        dpi = float(rng.choice([150, 200, 300], p=[0.2, 0.3, 0.5])); cs = str(rng.choice(["DeviceRGB", "ICCBased", "DeviceGray"], p=[0.5, 0.3, 0.2]))
        for k, gz in enumerate(["Ber_MZP1", "Arg_MZP1", "Ber_MZP2", "Arg_MZP2", "Ber_MZP3", "Arg_MZP3"]):
            rows.append(dict(pdf=f"s{i}_{k}.pdf", seite=1, code=code, Klassenstufe=cls, Schulform="GYMNASIUM" if i % 3 else "IGS",
                             Gruppe="KONTROLLGRUPPE" if i % 4 < 2 else "INTERVENTIONSGRUPPE", Geschlecht="WEIBLICH" if i % 5 < 3 else "MAENNLICH",
                             dpi_eff=dpi, cs=cs, img_sha1=f"{i}-{k}", gorev_zaman_varsayim=gz))
    return pd.DataFrame(rows)


class TestSplits(unittest.TestCase):
    def setUp(self):
        from src.handwriting.splits import student_table
        self.pages = fake_manifest()
        self.students = student_table(self.pages)

    def test_student_level_and_proportions(self):
        sp = make_splits(self.students)
        self.assertEqual(sp["code"].nunique(), len(sp))                   # her öğrenci tek bölümde
        self.assertEqual(set(sp["bolum"]), {"train", "val", "test"})
        share = sp["bolum"].value_counts(normalize=True)
        self.assertAlmostEqual(share["train"], 0.70, delta=0.05)
        self.assertAlmostEqual(share["val"], 0.15, delta=0.05)

    def test_deterministic_and_seed_dependent(self):
        a, b, c = make_splits(self.students, 42), make_splits(self.students, 42), make_splits(self.students, 43)
        pd.testing.assert_series_equal(a["bolum"], b["bolum"])
        self.assertFalse(a["bolum"].equals(c["bolum"]))

    def test_dpi_balance_detects_imbalance_and_rule_reports(self):
        sp = make_splits(self.students)
        biased = sp.assign(dpi_major=np.where(sp["bolum"] == "train", "~300", "~150"))
        self.assertGreater(dpi_balance(biased)[1], 0.5)
        out, rep = make_splits_with_rule(self.students)
        self.assertIn("final_gap", rep)
        self.assertEqual(out["bolum"].isna().sum(), 0)

    def test_write_splits_only_codes_and_hash(self):
        sp = make_splits(self.students)
        with tempfile.TemporaryDirectory() as d:
            path, sha = write_splits(sp, d)
            df = pd.read_csv(path)
        self.assertEqual(list(df.columns), ["code", "bolum"])
        self.assertEqual(len(sha), 64)


class TestPilot(unittest.TestCase):
    def test_selection(self):
        from src.handwriting.splits import student_table
        pages = fake_manifest(160)
        pages.loc[pages.code == "S0004", "img_sha1"] = "dup"                  # tekrar eden sayfa -> dışlanmalı
        pages = pages[~((pages.code == "S0006") & (pages.gorev_zaman_varsayim == "Arg_MZP2"))]  # 5 sayfa -> dışlanmalı
        splits = make_splits(student_table(pages))[["code", "bolum"]]
        key, sel = select_pilot(pages, splits, n=20)
        self.assertEqual(len(key), 20)
        self.assertTrue(set(key["code"]) <= set(splits[splits.bolum == "train"].code))   # yalnız train
        self.assertFalse({"S0004", "S0006"} & set(key["code"]))
        self.assertEqual(sorted(sel.groupby("pilot_id").size().unique()), [2])
        self.assertEqual(set(sel["gorev_zaman_varsayim"]), {"Ber_MZP1", "Arg_MZP3"})
        self.assertGreaterEqual(key["hucre"].nunique(), 10)                   # hücrelere yayılmış (tek hücreye yığılma yok)
        self.assertEqual(len(set(key["pilot_id"])), 20)

    def test_failure_checks(self):
        _, good = good_page()
        self.assertEqual(failure_checks(good), [])
        blank = analyze_page(np.full((1754, 1240, 3), 250, np.uint8), 150)
        self.assertIn("cizgi_yok", failure_checks(blank))

    def test_run_pilot_end_to_end_requires_permission_and_never_writes_codes_to_figures(self):
        from src.handwriting.splits import student_table
        pages = fake_manifest(40)
        splits = make_splits(student_table(pages))[["code", "bolum"]]
        key, sel = select_pilot(pages, splits, n=2)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / "raw").mkdir(); (root / "manifests").mkdir()
            for r in sel.itertuples():                                         # yalnız seçilen sayfalar için sentetik PDF
                make_pdf(root / "raw" / r.pdf, make_layout(seed=hash(r.code) % 1000), skew_deg=0.2)
            pages.to_csv(root / "manifests" / "pages.csv", index=False, encoding="utf-8")
            splits.to_csv(root / "splits.csv", index=False, encoding="utf-8")
            with self.assertRaises(PermissionError):
                run_pilot(root=root, n=2)
            (root / "permission.json").write_text(json.dumps({"approved": True}), encoding="utf-8")
            with self.assertRaises(RuntimeError):                              # çıktı klasörü bulut/Drive yolunda olamaz
                run_pilot(root=root, n=2, out_dir="H:/My Drive/bitirme/pilot")
            (root / "permission.json").write_text(json.dumps({"approved": True}), encoding="utf-8")
            out = run_pilot(root=root, n=2)
            self.assertEqual(len(list(out.glob("p0*.png"))), 4)
            summary = pd.read_csv(out / "ozet.csv")
            self.assertNotIn("code", summary.columns)                          # özet kodsuz
            self.assertTrue((out / "pilot_key.csv").exists())


class TestReport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lay, cls.res = good_page()
        rng = np.random.default_rng(0)
        cls.ref = pd.DataFrame({k: cls.res.features[k] * rng.normal(1, 0.1, 150) if np.isfinite(cls.res.features.get(k, np.nan)) else np.nan
                                for k in MEASURES})

    def test_percentile_rank(self):
        self.assertAlmostEqual(percentile_rank(5, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]), 45.0)
        self.assertAlmostEqual(percentile_rank(3, [3, 3, 3, 3]), 50.0)

    def test_report_with_reference_change_and_notes(self):
        prev = dict(self.res.features, xheight_mm=self.res.features["xheight_mm"] + 0.8)
        rep = build_report(self.res, reference=self.ref, previous=prev, change_threshold={"xheight_mm": 0.4}, context={"grup": "örnek"})
        by = {m["ad"]: m for m in rep["olcumler"]}
        self.assertTrue(rep["referans"]["yeterli"])
        self.assertTrue(0 <= by["xheight_mm"]["yuzdelik"] <= 100)
        ch = {c["ad"]: c for c in rep["degisim"]}
        self.assertEqual(ch["xheight_mm"]["yorum"], "güvenilir değişim eşiğini aşıyor")
        self.assertEqual(ch["left_margin_mm"]["yorum"], "eşik tanımsız: fark yorumlanmaz")  # eşik yoksa yorum yok
        self.assertEqual(rep["kalite"]["guvenilirlik"], "yüksek")

    def test_small_reference_gives_no_extreme_flags(self):
        low = self.ref * 0.5  # sayfa referansın en üst ucunda: yeterince büyük grupta uç işareti doğardı
        big = build_report(self.res, reference=low)
        self.assertTrue(any(m.get("uc") for m in big["olcumler"]))
        small = build_report(self.res, reference=low.head(50))
        self.assertFalse(any(m.get("uc") for m in small["olcumler"]))  # < MIN_GROUP: uç işareti yok
        self.assertFalse(small["referans"]["yeterli"])
        self.assertIn("grup küçük", small["referans"]["not_"])

    def test_no_reference_means_no_percentile(self):
        rep = build_report(self.res)
        self.assertTrue(all(m.get("yuzdelik") is None for m in rep["olcumler"]))
        self.assertIn("yüzdelik yok", render_text(rep))

    def test_extreme_flag_and_wording(self):
        shifted = self.ref.copy(); shifted["xheight_mm"] = self.res.features["xheight_mm"] * 0.5   # sayfa referansın en üst ucunda
        rep = build_report(self.res, reference=shifted)
        self.assertTrue({m["ad"]: m for m in rep["olcumler"]}["xheight_mm"]["uc"])
        text = render_text(rep).lower()
        for banned in ["anormal", "bozukluk", "disgrafi", "geri kalmış"]:
            self.assertNotIn(banned, text)
        self.assertIn("sınırı", text)

    def test_reliability_low_on_blank_page(self):
        blank = analyze_page(np.full((1754, 1240, 3), 250, np.uint8), 150)
        self.assertEqual(build_report(blank)["kalite"]["guvenilirlik"], "düşük")


class TestAnnotate(unittest.TestCase):
    def test_outlier_component_is_found_and_figure_written(self):
        lay = make_layout(seed=1)
        t = np.linspace(0, 2 * np.pi, 40)                                     # 3 kat büyük bir "harf"
        lay.strokes.append((np.c_[60 + 5 * np.cos(t), lay.rules_mm[2] - 1.2 - 4 + 5 * np.sin(t)], 0.45))
        rgb, _, boxes, _ = render(lay, dpi=150)
        res = analyze_page(rgb, 150, boxes)
        out = outlier_components(res)
        self.assertTrue(((out.x0 * res.pre.mm_per_px < 66) & (out.x1 * res.pre.mm_per_px > 54) & (out.line == 2)).any())
        with tempfile.TemporaryDirectory() as d:
            annotate_regions(res, Path(d) / "a.png", crop_mm=(25, 135))
            self.assertGreater((Path(d) / "a.png").stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
