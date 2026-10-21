"""Görev uyumu ve ayrışma: sentetik tahmin tablolarıyla (KIDO ve model gerekmez)."""
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from src import task_fit as T


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


if __name__ == "__main__":
    unittest.main()
