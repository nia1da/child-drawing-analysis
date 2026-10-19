"""deneyler.csv'ye yazma: eski düzen önce yedeklenip taşınır, tanınmayan düzende hiçbir şey yazılmaz."""
import os
import tempfile
import unittest

import pandas as pd

from src.migrate_experiments import COLUMNS, append_record, check_results_file

# Sütunlar batch/accum_steps eklenmeden önceki (13 sütunlu) düzen
OLD_HEADER = ("tarih,deney,model,boyut,lr,smoothing,seed,augmentation,toplam_epoch,en_iyi_epoch,"
              "en_iyi_val_f1,dakika,not\n")
OLD_ROW = "2026-10-15 10:00,convnext_tiny_448_ep8_lr1e-4_ls0.1_s1,convnext_tiny,448,0.0001,0.1,1,temel,8,4,0.823,25.1,\n"


def new_record(name="convnext_tiny_448_ep8_lr1e-4_ls0.1_s7"):
    record = dict.fromkeys(COLUMNS)
    record.update({"deney": name, "model": "convnext_tiny", "boyut": 448, "batch": 16, "accum_steps": 2})
    return record


class ResultsFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.folder = self.tmp.name
        self.path = os.path.join(self.folder, "deneyler.csv")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, text):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_new_file(self):
        append_record(self.path, new_record())
        df = pd.read_csv(self.path)
        self.assertEqual(df.columns.tolist(), COLUMNS)
        self.assertEqual(len(df), 1)

    def test_current_layout_appends_without_backup(self):
        append_record(self.path, new_record("a"))
        append_record(self.path, new_record("b"))
        self.assertEqual(pd.read_csv(self.path).deney.tolist(), ["a", "b"])
        self.assertEqual(os.listdir(self.folder), ["deneyler.csv"])

    def test_old_layout_migrated_then_appended(self):
        self.write(OLD_HEADER + OLD_ROW)
        append_record(self.path, new_record())
        df = pd.read_csv(self.path)
        self.assertEqual(df.columns.tolist(), COLUMNS)
        self.assertEqual(len(df), 2)
        self.assertEqual((df.batch[0], df.accum_steps[0]), (32, 1))  # eski satır: varsayılanlar
        self.assertEqual((df.batch[1], df.accum_steps[1]), (16, 2))  # yeni satır
        backups = [f for f in os.listdir(self.folder) if f.startswith("deneyler_yedek_")]
        self.assertEqual(len(backups), 1)
        with open(os.path.join(self.folder, backups[0]), encoding="utf-8") as f:
            self.assertEqual(f.read(), OLD_HEADER + OLD_ROW)  # yedek orijinalin aynısı

    def test_first_layout_migrated(self):
        self.write("deney,en_iyi_val_f1,epoch,dakika\nresnet50_320px_lr0.0001_ls0.1_s42,0.79,4,12.0\n")
        append_record(self.path, new_record())
        df = pd.read_csv(self.path)
        self.assertEqual(df.columns.tolist(), COLUMNS)
        self.assertEqual(df.model.tolist(), ["resnet50", "convnext_tiny"])
        self.assertTrue(os.path.exists(os.path.join(self.folder, "deneyler_eski.csv")))

    def test_unknown_layout_writes_nothing(self):
        original = "deney,bilinmeyen_sutun\nx,1\n"
        self.write(original)
        with self.assertRaises(ValueError):
            check_results_file(self.path)  # eğitimden önceki kontrol
        with self.assertRaises(ValueError):
            append_record(self.path, new_record())
        with open(self.path, encoding="utf-8") as f:
            self.assertEqual(f.read(), original)
        self.assertEqual(os.listdir(self.folder), ["deneyler.csv"])  # yedek de yok

    def test_record_keys_must_match(self):
        record = new_record()
        del record["batch"]
        with self.assertRaises(ValueError):
            append_record(self.path, record)
        self.assertFalse(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
