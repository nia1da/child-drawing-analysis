"""Ortama göre (yerel / Colab) dosya yolları.

Ortam otomatik algılanır; gerekirse CIZIM_ENV=local|colab ile zorlanır.
Yerelde her şey git'e girmeyen data/ altında durur.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVE = "/content/drive/MyDrive/bitirme"

ENVIRONMENTS = {
    "local": {
        "root": f"{REPO}/data/kido/Dataset/Images",
        "zip": f"{REPO}/data/kido_dataset",
        "metadata": f"{REPO}/data/kido_metadata.csv",
        "output": f"{REPO}/data/ciktilar",  # .pt dosyaları + deneyler.csv
    },
    "colab": {
        "root": "/content/kido/Dataset/Images",  # görseller Colab'ın yerel diskinde
        "zip": f"{DRIVE}/kido_dataset",  # her oturumda root'a açılır
        "metadata": f"{DRIVE}/kido_metadata.csv",
        "output": DRIVE,
    },
}


def detect_environment():
    env = os.environ.get("CIZIM_ENV")
    if env:
        if env not in ENVIRONMENTS:
            raise ValueError(f"Bilinmeyen CIZIM_ENV: {env} (seçenekler: {list(ENVIRONMENTS)})")
        return env
    return "colab" if "COLAB_RELEASE_TAG" in os.environ else "local"


ENV = detect_environment()
PATHS = ENVIRONMENTS[ENV]
