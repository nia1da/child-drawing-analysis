"""Ortama göre (yerel / Colab) dosya yolları.

Ortam otomatik algılanır; gerekirse CIZIM_ORTAM=yerel|colab ile zorlanır.
Yerelde her şey git'e girmeyen data/ altında durur.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVE = "/content/drive/MyDrive/bitirme"

ORTAMLAR = {
    "yerel": {
        "kok": f"{REPO}/data/kido/Dataset/Images",
        "zip": f"{REPO}/data/kido_dataset",
        "metadata": f"{REPO}/data/kido_metadata.csv",
        "cikti": f"{REPO}/data/ciktilar",  # .pt dosyaları + deneyler.csv
    },
    "colab": {
        "kok": "/content/kido/Dataset/Images",  # görseller Colab'ın yerel diskinde
        "zip": f"{DRIVE}/kido_dataset",  # her oturumda kok'a açılır
        "metadata": f"{DRIVE}/kido_metadata.csv",
        "cikti": DRIVE,
    },
}


def ortam_bul():
    ortam = os.environ.get("CIZIM_ORTAM")
    if ortam:
        if ortam not in ORTAMLAR:
            raise ValueError(f"Bilinmeyen CIZIM_ORTAM: {ortam} (seçenekler: {list(ORTAMLAR)})")
        return ortam
    return "colab" if "COLAB_RELEASE_TAG" in os.environ else "yerel"


ORTAM = ortam_bul()
YOLLAR = ORTAMLAR[ORTAM]
