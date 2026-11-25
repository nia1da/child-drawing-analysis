"""Commit denetimi: sentetik ihlaller yakalanıyor, temiz içerik geçiyor."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_no_student_data import scan_text  # noqa: E402


class TestScan(unittest.TestCase):
    def test_student_codes(self):
        for code in ["0K51AB12", "1H92CD05", "0K52HI0", "0k93ab12x"[:8], "1K93ZZ"]:
            self.assertTrue(scan_text("docs/x.md", f"öğrenci {code} sayfa 3"), code)

    def test_embedded_images_and_user_line(self):
        self.assertTrue(scan_text("n.ipynb", '"image/png": "iVBOR"'))
        self.assertTrue(scan_text("n.md", "![](data:image/png;base64,AAAA)"))
        self.assertTrue(scan_text("cover.txt", "Benutzer: someone"))

    def test_data_folder_path(self):
        self.assertTrue(scan_text("data/handwriting/fd_lex/manifests/pages.csv", "x"))

    def test_clean_text_passes(self):
        txt = "Harf boyutu 2,8 mm; 150 dpi; sha256 ac410b6f5e6cc578e0f7f78e9650c57e3be39a43bdcea7fda275e36007be98c1; 3. sınıf 8H"
        self.assertEqual(scan_text("docs/plan.md", txt), [])


if __name__ == "__main__":
    unittest.main()
