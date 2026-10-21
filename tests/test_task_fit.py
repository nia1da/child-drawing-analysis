"""Görev uyumu ve ayrışma: sentetik tahmin tablolarıyla (KIDO ve model gerekmez)."""
import os
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from src import task_fit as T
from src.measurements.metrics import MEASURES


def predictions(n_per_grade=40, seed=0, trend=0.0):
    """Her sınıfta n_per_grade öğrenci, her birinin bir mutlu ve bir üzgün çizimi.

    trend > 0: mutlu çizimlerde sınıf düştükçe "üzgün" olasılığı artar (küçük sınıflarda görev uyumu düşük).
    """
    rng = np.random.default_rng(seed)
    rows = []
    for grade in range(1, 9):
        level = "Primary" if grade <= 4 else "Secondary"
        for i in range(n_per_grade):
            student = f"101-{grade}A-{i}"
            shift = trend * (4 - grade) if level == "Primary" else 0.0
            p_happy = float(np.clip(rng.uniform(0.05, 0.6) + shift, 0.001, 0.999))
            p_sad = float(rng.uniform(0.4, 0.95))
            for task, letter, p in [("Happiness", "H", p_happy), ("Sadness", "S", p_sad)]:
                rows.append({"dosya": f"{student}-F-{letter}.jpg", "duygu": task, "cinsiyet": "Female",
                             "egitim": level, "ogrenci": student, "gercek": int(task == "Sadness"),
                             "olasilik_uzgun": p, "tahmin": int(p >= 0.5)})
    return pd.DataFrame(rows)


class TaskFitTest(unittest.TestCase):
    def test_task_fit_direction(self):
        t = T.with_task_fit(predictions())
        happy, sad = t[t.duygu == "Happiness"], t[t.duygu == "Sadness"]
        np.testing.assert_allclose(happy.gorev_uyumu, 1 - happy.olasilik_uzgun)
        np.testing.assert_allclose(sad.gorev_uyumu, sad.olasilik_uzgun)
        self.assertEqual(set(t.sinif), set(range(1, 9)))

    def test_pairs(self):
        pred = predictions(n_per_grade=5)
        pt = T.pairs(pred)
        self.assertEqual(len(pt), 40)
        row = pt.iloc[0]
        self.assertAlmostEqual(row.d_olasilik, row.p_uzgun - row.p_mutlu)
        self.assertAlmostEqual(row.d_logit, float(T.logit(row.p_uzgun) - T.logit(row.p_mutlu)))
        with self.assertRaises(ValueError):  # öğrencinin tek çizimi varsa
            T.pairs(pred.iloc[1:])
        broken = pred.copy()
        broken.loc[0, "dosya"] = broken.loc[0, "dosya"].replace("-1A-", "-2A-")  # iki çizimde farklı sınıf
        with self.assertRaises(ValueError):
            T.pairs(broken)

    def test_separation_score_switches_on_saturation(self):
        pt = pd.DataFrame({"p_mutlu": [0.05, 0.95, 0.3, 0.2], "p_uzgun": [0.08, 0.97, 0.8, 0.7]})
        self.assertEqual(T.saturation_share(pt), 0.5)
        self.assertEqual(T.separation_score(pt), "d_logit")
        pt = pd.DataFrame({"p_mutlu": [0.05, 0.3, 0.3, 0.2], "p_uzgun": [0.08, 0.8, 0.8, 0.7]})
        self.assertEqual(T.saturation_share(pt), 0.25)  # eşitte olasılık kalır
        self.assertEqual(T.separation_score(pt), "d_olasilik")

    def test_pool_percentiles_match_norms(self):
        from src.measurements.norms import percentile
        values = np.array([0.1, 0.2, 0.2, 0.5, 0.9])
        np.testing.assert_allclose(T.pool_percentiles(values), [percentile(values, x) for x in values])

    def test_no_trend_gives_level_norms(self):
        table, decision = T.norm_group_decision(predictions(seed=1))
        self.assertEqual(len(table), 6)
        self.assertEqual(decision, "seviye")

    def test_strong_trend_gives_grade_norms(self):
        table, decision = T.norm_group_decision(predictions(seed=1, trend=0.15))
        self.assertEqual(decision, "sinif")
        cell = table.set_index("hucre").loc["görev uyumu | Primary | Happiness"]
        self.assertTrue(cell.anlamli and cell.pratik)
        self.assertLess(cell.medyan_1, 50)  # 1. sınıfın görev uyumu havuzun altında

    def test_bonferroni_correction(self):
        # Düzeltmesiz anlamlı (p 0,03), sapma 12: 6 hücrede 0,05/6'yı geçmediği için belirgin değil
        trend = {1: 38.0, 2: 50.0, 3: 55.0, 4: 57.0}
        with mock.patch.object(T, "grade_trend", return_value=(0.03, trend)):
            table, decision = T.norm_group_decision(predictions())
        self.assertFalse(table.anlamli.any())
        self.assertEqual(decision, "seviye")
        with mock.patch.object(T, "grade_trend", return_value=(0.005, trend)):
            self.assertEqual(T.norm_group_decision(predictions())[1], "sinif")

    def test_needs_both_criteria(self):
        # Çok büyük örneklemde küçük bir eğilim anlamlı olur ama sapma 10 puanın altında kalır: belirgin değil
        table, decision = T.norm_group_decision(predictions(n_per_grade=1500, seed=2, trend=0.02))
        cell = table.set_index("hucre").loc["görev uyumu | Primary | Happiness"]
        self.assertTrue(cell.anlamli)
        self.assertFalse(cell.pratik)
        self.assertEqual(decision, "seviye")


class ModelNormsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pred = predictions()
        with mock.patch.object(T, "load_predictions", return_value=self.pred):
            self.norms = T.build_model_norms("deney_x", self.tmp.name)

    def test_rows_and_no_gender(self):
        self.assertEqual((self.norms.tur == "cizim").sum(), len(self.pred))
        self.assertEqual((self.norms.tur == "cift").sum(), self.pred.ogrenci.nunique())
        self.assertNotIn("cinsiyet", self.norms.columns)

    def test_groups_and_round_trip(self):
        path = T.norms_path(self.tmp.name)
        loaded = T.load_model_norms(path, "deney_x")
        self.assertEqual(len(T.norm_group(loaded, "Primary", "Happiness")), 4 * 40)
        self.assertEqual(len(T.norm_group(loaded, "Secondary")), 4 * 40)
        t = T.with_task_fit(self.pred)
        want = np.sort(t[(t.egitim == "Primary") & (t.duygu == "Sadness")].gorev_uyumu.values)
        np.testing.assert_allclose(np.sort(T.norm_group(loaded, "Primary", "Sadness")), want)

    def test_version_and_model_mismatch_raise(self):
        path = T.norms_path(self.tmp.name)
        with self.assertRaises(RuntimeError):
            T.load_model_norms(path, "baska_deney")
        with mock.patch.object(T, "MODEL_NORM_VERSION", 2), self.assertRaises(RuntimeError):
            T.load_model_norms(path, "deney_x")


class ReportModelTest(unittest.TestCase):
    """Rapora bağlama: model_olcumleri, sınırlama notları, çift raporu (model ve KIDO gerekmez)."""

    def setUp(self):
        from PIL import Image, ImageDraw
        from tests.test_measurements import synthetic_norms
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with mock.patch.object(T, "load_predictions", return_value=predictions()):
            self.model_norms = T.build_model_norms("deney_x", self.tmp.name)
        self.norms = synthetic_norms(200).assign(sinif=3)
        img = Image.new("RGB", (200, 150), "white")
        ImageDraw.Draw(img).rectangle([30, 30, 120, 100], outline="black", width=4)
        self.happy = os.path.join(self.tmp.name, "101-3B-1-F-H.jpg")
        self.sad = os.path.join(self.tmp.name, "101-3B-1-F-S.jpg")
        img.save(self.happy)
        img.save(self.sad)

    def report(self, p_sad, **kw):
        from src.report import build_report
        with mock.patch.object(T, "kido_split", return_value=None):
            return build_report(self.happy, norms=self.norms, model_norms=self.model_norms, p_sad=p_sad, **kw)

    def test_section_values_and_limitations(self):
        part = self.report(0.2)["model_olcumleri"]
        self.assertEqual(part["durum"], "tamam")
        fit = part["gorev_uyumu"]
        self.assertEqual((fit["gorev"], fit["deger"], fit["olasilik_uzgun"]), ("mutlu", 0.8, 0.2))
        group = part["karsilastirma_grubu"]
        self.assertEqual((group["seviye"], group["n"]), ("Primary", 160))
        self.assertEqual(part["sinirlamalar"], T.LIMITATIONS)
        self.assertNotIn("cinsiyet", str(part).lower().replace("cinsiyete göre", ""))

    def test_no_model_norms_keeps_old_report(self):
        from src.report import build_report
        self.assertNotIn("model_olcumleri", build_report(self.happy, norms=self.norms))

    def test_text_limitations_right_below_task_fit(self):
        from src.report import format_text
        lines = format_text(self.report(0.2)).splitlines()
        i = next(k for k, l in enumerate(lines) if l.startswith("Görev uyumu (mutlu)"))
        self.assertIn("yüzdelik dilim", lines[i])
        self.assertIn("Karşılaştırma grubu: ilkokul (1–4. sınıf) mutlu normu, n=160", lines[i + 1])
        self.assertEqual(lines[i + 2], "  Sınırlamalar:")
        self.assertEqual(sum(l.startswith("   - ") for l in lines[i + 3:]), len(T.LIMITATIONS))
        self.assertNotIn("⚠", "\n".join(lines[i:]).replace("⚠ verilmez", ""))

    def test_model_failure_does_not_break_report(self):
        from src.report import format_text
        with mock.patch.object(T, "score_image", side_effect=FileNotFoundError("x.pt")):
            r = self.report(None)
        self.assertEqual(r["model_olcumleri"]["durum"], "çalışmadı")
        self.assertEqual(len(r["olcumler"]), len(MEASURES))
        self.assertIn("Görev uyumu: çalışmadı", format_text(r))

    def test_context_notes_from_split(self):
        from src.report import build_report
        for split, word in [("train", "eğitim verisinde"), ("val", "grubunun içinde")]:
            with mock.patch.object(T, "kido_split", return_value=split):
                part = build_report(self.happy, norms=self.norms, model_norms=self.model_norms,
                                    p_sad=0.2)["model_olcumleri"]
            self.assertTrue(any(word in n for n in part["notlar"]), split)

    def test_pair_report_direction_and_percentile(self):
        from src.report import build_pair_report, format_pair_text
        good = build_pair_report(self.happy, self.sad, self.model_norms, p_happy=0.1, p_sad=0.9)["ayrisma"]
        self.assertEqual((good["d"], good["yon"], good["skor"]), (0.8, "uygun", "d_olasilik"))
        bad = build_pair_report(self.happy, self.sad, self.model_norms, p_happy=0.9, p_sad=0.1)
        self.assertEqual(bad["ayrisma"]["yon"], "ters")
        self.assertLess(bad["ayrisma"]["yuzdelik"], good["yuzdelik"])
        self.assertIn("tersi yönünde sıralıyor", format_pair_text(bad))
        self.assertEqual(good["sinirlamalar"], T.LIMITATIONS)

    def test_pair_notes_and_missing_norms(self):
        from src.report import build_pair_report, format_pair_text
        for splits, word in [(["train", "val"], "eğitim verisinde"), (["val", "val"], "grubunun içinde")]:
            with mock.patch.object(T, "kido_split", side_effect=splits):
                a = build_pair_report(self.happy, self.sad, self.model_norms, p_happy=0.1, p_sad=0.9)["ayrisma"]
            self.assertTrue(any(word in n for n in a["notlar"]), splits)
        pair = build_pair_report(self.happy, self.sad, None, p_happy=0.1, p_sad=0.9)
        self.assertEqual(pair["ayrisma"]["durum"], "çalışmadı")
        self.assertIn("çalışmadı", format_pair_text(pair))

    def test_pair_report_checks_student_and_order(self):
        from src.report import build_pair_report
        other = os.path.join(self.tmp.name, "101-3B-2-F-S.jpg")
        open(other, "wb").close()
        with self.assertRaises(ValueError):
            build_pair_report(self.happy, other, self.model_norms, p_happy=0.1, p_sad=0.9)
        with self.assertRaises(ValueError):
            build_pair_report(self.sad, self.happy, self.model_norms, p_happy=0.1, p_sad=0.9)


if __name__ == "__main__":
    unittest.main()
