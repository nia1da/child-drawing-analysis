"""PDF'ten sayfa görüntüsü ve metin katmanı kutuları (PyMuPDF).

`render_page` saf bir fonksiyondur (sentetik PDF'lerle test edilir). Gerçek FD-LEX PDF'lerini okumak için `load_page` kullanılır:
yerel koruma ve kullanım izni dosyasını (`paths.require_permission`) kontrol eder. Sayfa dönüşü (/Rotate) `get_pixmap` ve kutu
dönüşümünde uygulanır; görüntüler diske yazılmaz.
"""
import re
from pathlib import Path

import numpy as np

from .paths import require_permission

CODE_RE = re.compile(r"^[0-9A-Za-z]{7,9}$")


def overlay_boxes(page, dpi):
    """Metin katmanından ölçüm dışı bırakılacak kutular (piksel, döndürülmüş sayfa koordinatında): XXX, telif satırı, öğrenci kodu.

    Metin katmanındaki başka kelimeler (örn. bir sayfadaki görünmez OCR katmanı) kasıtlı olarak maskelenmez: el yazısını silerdi.
    """
    import pymupdf
    words = page.get_text("words")  # (x0, y0, x1, y1, kelime, blok, satır, sıra)
    lines = {}
    for w in words:
        lines.setdefault((w[5], w[6]), []).append(w)
    keep = []
    for ws in lines.values():
        first = ws[0][4]
        if first.startswith("©"):                     # telif satırının hepsi
            keep += ws
        else:
            keep += [w for w in ws if w[4] == "XXX" or (len(ws) == 1 and CODE_RE.match(w[4]))]
    s = dpi / 72.0
    boxes = []
    for w in keep:
        r = pymupdf.Rect(w[:4])
        if page.rotation:  # metin koordinatları döndürülmemiş sayfada; render döndürülmüş
            r = r * page.rotation_matrix
        boxes.append((int(r.x0 * s) - 1, int(r.y0 * s) - 1, int(np.ceil(r.x1 * s)) + 1, int(np.ceil(r.y1 * s)) + 1))
    return boxes


def render_page(pdf_path, page_index, dpi=150):
    """Döner: (rgb uint8, overlay_boxes). Sayfa dönüşü uygulanmış, dpi = piksel/inç (A4 için 150 → 1240 x 1754)."""
    import pymupdf
    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc[page_index]
        pm = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB)
        rgb = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 3).copy()
        return rgb, overlay_boxes(page, dpi)
    finally:
        doc.close()


def load_page(pdf_name, page_no, dpi=150, root=None):
    """Gerçek FD-LEX sayfası (1 tabanlı sayfa no). İzin dosyası ve yerel koruma zorunlu."""
    base = require_permission(root)
    return render_page(Path(base) / "raw" / pdf_name, page_no - 1, dpi)
