import unittest

import pandas as pd

from src.splits import stratified_split


def sample_table(n_students=200, drawings=3):
    # Sentetik metadata: her öğrencinin birkaç çizimi, 4 eğitim+cinsiyet grubu; gerçek veri gerekmez
    rows = []
    for i in range(n_students):
        education, gender = ["Primary", "Secondary"][i % 2], ["Female", "Male"][(i // 2) % 2]
        for j in range(drawings):
            rows.append({"dosya": f"1-1-{i}-{j}.jpg", "split": "test" if i % 10 == 0 else "train",
                         "duygu": ["Happiness", "Sadness"][j % 2], "cinsiyet": gender,
                         "egitim": education, "ogrenci": f"1-1-{i}"})
    return pd.DataFrame(rows)


class StratifiedSplitTest(unittest.TestCase):
    def test_student_in_single_split(self):
        df = stratified_split(sample_table())
        self.assertTrue((df.bolum == "val").any())
        mixed = df.groupby("ogrenci").bolum.nunique()
        self.assertEqual(mixed[mixed > 1].index.tolist(), [])


if __name__ == "__main__":
    unittest.main()
