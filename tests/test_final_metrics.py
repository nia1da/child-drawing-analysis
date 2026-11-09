"""Test metrikleri: sentetik tahminlerle (KIDO, model ve gerçek test tahmini gerekmez)."""
import os
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score

from src import evaluation, final_metrics as F, task_fit as T
from src.analysis import error_direction
from src.measurements.norms import percentile
from src.stats import confidence_intervals, interval, student_bootstrap
from tests.test_task_fit import predictions


def with_sex(pred, seed=1):
    rng = np.random.default_rng(seed)
    sex = {s: rng.choice(["Female", "Male"]) for s in pred.ogrenci.unique()}
    pred = pred.copy()
    pred["cinsiyet"] = pred.ogrenci.map(sex)
    return pred


class FinalMetricsTest(unittest.TestCase):
    def setUp(self):
        self.pred = with_sex(predictions(n_per_grade=40, seed=3))
        self.w = F.wide_table(self.pred)

    def test_auc_matches_sklearn_with_ties(self):
        pred = self.pred.copy()
        pred["olasilik_uzgun"] = pred.olasilik_uzgun.round(1)  # bağlar
        w = F.wide_table(pred)
        self.assertAlmostEqual(F.auc(w.p_uzgun.values, w.p_mutlu.values),
                               roc_auc_score(pred.gercek, pred.olasilik_uzgun))

    def test_macro_f1_and_error_direction_match_existing_code(self):
        a, b = self.w.p_uzgun.values, self.w.p_mutlu.values
        self.assertAlmostEqual(F.macro_f1(a, b), f1_score(self.pred.gercek, self.pred.tahmin, average="macro"))
        stat = F.build_statistic(self.w, with_norms=False)(np.arange(len(self.w)))
        old = error_direction(self.pred).set_index("grup")
        for name in old.index:
            self.assertAlmostEqual(stat[f"mutlu_uzgun|{name}"], old.loc[name, "mutlu_uzgun_yuzde"], delta=0.06)
            self.assertAlmostEqual(stat[f"uzgun_mutlu|{name}"], old.loc[name, "uzgun_mutlu_yuzde"], delta=0.06)

    def test_d_positive_share(self):
        a, b = np.array([0.9, 0.3, 0.6]), np.array([0.2, 0.8, 0.5])
        stat = F.build_statistic(pd.DataFrame({"p_uzgun": a, "p_mutlu": b, "egitim": "Primary",
                                               "cinsiyet": "Female", "sinif": 1}), with_norms=False)
        self.assertAlmostEqual(stat(np.arange(3))["d_pos|Genel"], 100 * 2 / 3)

    def test_vectorized_percentile_equals_norms_percentile(self):
        rng = np.random.default_rng(0)
        group = rng.integers(0, 20, 50) / 20  # bağlar
        x = rng.integers(0, 20, 30) / 20
        np.testing.assert_allclose(F.pct_in(group, x), [percentile(group, v) for v in x])

    def test_verdict_rule(self):
        self.assertEqual(F.verdict(300, 11.0, 15.0), "zayıf")
        self.assertEqual(F.verdict(300, 4.0, 9.0), "makul")
        self.assertEqual(F.verdict(300, 8.0, 12.0), "belirsiz")
        self.assertIn("hüküm yok", F.verdict(50, 11.0, 15.0))

    def test_bootstrap_matches_old_ci_for_macro_f1(self):
        old, _ = confidence_intervals(self.pred, n_boot=1000)
        point, reps = student_bootstrap(len(self.w), F.build_statistic(self.w, False), n_boot=1000)
        low, high = interval(reps, "macro_f1|Genel")
        row = old[old.grup == "Genel"].iloc[0]
        self.assertAlmostEqual(point["macro_f1|Genel"], row.macro_f1, places=3)
        self.assertAlmostEqual(low, row.ga_alt, delta=0.02)
        self.assertAlmostEqual(high, row.ga_ust, delta=0.02)

    def test_bootstrap_resamples_students_not_drawings(self):
        seen = []
        student_bootstrap(10, lambda idx: seen.append(idx) or {"x": 0.0}, n_boot=5)
        self.assertTrue(all(len(i) == 10 for i in seen))


class NormTransferTest(unittest.TestCase):
    def setUp(self):
        self.pred = with_sex(predictions(n_per_grade=60, seed=4))
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        with mock.patch.object(T, "load_predictions", return_value=self.pred):
            self.norms = T.build_model_norms("deney_x", self.tmp.name)

    def test_norm_equals_test_gives_expected_shares(self):
        # test = val ile aynı tablo: uç payları ≈ %5, 50 altı ≈ %50
        w = F.norm_columns(F.wide_table(self.pred), self.norms)
        stat = F.build_statistic(w)(np.arange(len(w)))
        self.assertAlmostEqual(stat["alt|görev uyumu|Genel"], 5.0, delta=1.5)
        self.assertAlmostEqual(stat["ust|görev uyumu|Genel"], 5.0, delta=1.5)
        self.assertAlmostEqual(stat["alt50|ayrışma|Genel"], 50.0, delta=2)

    def test_percentiles_match_report_function(self):
        w = F.norm_columns(F.wide_table(self.pred), self.norms)
        row = w[w.egitim == "Primary"].iloc[0]
        expect = percentile(T.norm_group(self.norms, "Primary", "Happiness"), 1 - row.p_mutlu)
        self.assertAlmostEqual(row.pct_mutlu, expect)

    def test_shifted_test_shows_weak_transfer(self):
        shifted = self.pred.copy()
        shifted["olasilik_uzgun"] = shifted.olasilik_uzgun * 0.5  # skorlar belirgin düşük
        w = F.norm_columns(F.wide_table(shifted), self.norms)
        point, reps = student_bootstrap(len(w), F.build_statistic(w), n_boot=200)
        low, high = interval(reps, "alt|görev uyumu|Genel")
        self.assertEqual(F.verdict(int(point["n|görev uyumu|Genel"]), low, high), "zayıf")

    def test_tables_have_no_significance_and_no_gender_in_norms(self):
        w, point, reps = F.run(self.pred, self.norms, n_boot=50)
        out = F.tables(w, point, reps)
        for table in out.values():
            self.assertNotIn("anlamli", table.columns)
        self.assertNotIn("cinsiyet", self.norms.columns)
        self.assertEqual(len(out["norm_aktarimi"]), 8)


class OutputsTest(unittest.TestCase):
    def test_missing_test_csv_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as d, self.assertRaisesRegex(FileNotFoundError, "src.evaluation"):
            F.load_test("yok", d)

    def test_main_writes_files_and_hash(self):
        pred = with_sex(predictions(n_per_grade=40, seed=5))
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(f"{d}/tahminler")
            pred.to_csv(f"{d}/tahminler/deney_x_test.csv", index=False)
            pred.to_csv(f"{d}/tahminler/deney_x_val.csv", index=False)
            with mock.patch.object(T, "load_predictions", return_value=pred):
                T.build_model_norms("deney_x", d)
            out, summary = F.main("deney_x", n_boot=30, base=d)
            for name in ("ayirt_edicilik", "alt_gruplar", "norm_aktarimi", "hata_yonu", "alt_5", "farklar"):
                self.assertTrue(os.path.exists(f"{d}/test_metrikleri/{name}.csv"), name)
            self.assertEqual(len(summary["test_tahmin_sha256"]), 64)
            self.assertEqual(summary["n_ogrenci"], pred.ogrenci.nunique())
            self.assertEqual(set(out["ayirt_edicilik"].bolum), {"val", "test", "val - test"})


class EvaluationGuardTest(unittest.TestCase):
    def test_existing_test_csv_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(f"{d}/tahminler")
            path = f"{d}/tahminler/convnext_tiny_320_x_test.csv"
            with open(path, "w", encoding="utf-8") as f:
                f.write("eski")
            df = pd.DataFrame({"bolum": ["test"]})
            with self.assertRaises(FileExistsError):
                evaluation.evaluate(df, "convnext_tiny_320_x", split="test", output_dir=d)
            with open(path, encoding="utf-8") as f:
                self.assertEqual(f.read(), "eski")

    def test_val_is_not_blocked_by_guard(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(f"{d}/tahminler")
            open(f"{d}/tahminler/convnext_tiny_320_x_val.csv", "w", encoding="utf-8").close()
            df = pd.DataFrame({"bolum": ["val"]})
            with self.assertRaises(FileNotFoundError):  # korumadan geçip .pt'yi arar
                evaluation.evaluate(df, "convnext_tiny_320_x", split="val", output_dir=d)


if __name__ == "__main__":
    unittest.main()
