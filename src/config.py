"""Ortama göre (yerel / Colab) dosya yolları.

Ortam otomatik algılanır; gerekirse CIZIM_ENV=local|colab ile zorlanır.
Çıktılar (.pt dosyaları, deneyler.csv, tahminler) iki ortamda da Drive'daki bitirme klasörüne gider;
yerelde Google Drive for desktop üzerinden (yol CIZIM_DRIVE ile verilebilir, yoksa aranır).
Görseller ve metadata yerelde git'e girmeyen data/ altında durur.
"""
import glob
import os
import string
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DRIVE = "/content/drive/MyDrive/bitirme"
DRIVE_FOLDER = "bitirme"
MY_DRIVE_NAMES = ["My Drive", "Drive'ım"]  # Drive for desktop'ın dile göre klasör adı


def find_local_drive():
    """Yerel Drive'daki bitirme klasörü: CIZIM_DRIVE, yoksa Windows sürücü harfleri ve macOS CloudStorage aranır."""
    env = os.environ.get("CIZIM_DRIVE")
    if env:
        if not os.path.isdir(env):
            raise FileNotFoundError(f"CIZIM_DRIVE klasörü yok: {env}")
        return env
    roots = [f"{d}:/" for d in string.ascii_uppercase] if os.name == "nt" else \
        glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/"))
    for root in roots:
        for name in MY_DRIVE_NAMES:
            path = f"{root}{name}/{DRIVE_FOLDER}"
            if os.path.isdir(path):
                return path
    return None


def local_output():
    drive = find_local_drive()
    if drive is not None:
        return drive
    # Drive yoksa da çalışsın (testler, --quick), ama sonuçlar ortak deneyler.csv'ye gitmez
    fallback = f"{REPO}/data/ciktilar"
    warnings.warn(f"Yerel Drive'da '{DRIVE_FOLDER}' klasörü bulunamadı; çıktılar {fallback} altına gider. "
                  "Drive for desktop açık mı? Yol CIZIM_DRIVE ile verilebilir.", stacklevel=2)
    return fallback


def detect_environment():
    env = os.environ.get("CIZIM_ENV")
    if env:
        if env not in ("local", "colab"):
            raise ValueError(f"Bilinmeyen CIZIM_ENV: {env} (seçenekler: local, colab)")
        return env
    return "colab" if "COLAB_RELEASE_TAG" in os.environ else "local"


def environment_paths(env):
    if env == "colab":
        return {
            "root": "/content/kido/Dataset/Images",  # görseller Colab'ın yerel diskinde
            "zip": f"{DRIVE}/kido_dataset",  # her oturumda root'a açılır
            "metadata": f"{DRIVE}/kido_metadata.csv",
            "output": DRIVE,  # .pt dosyaları + deneyler.csv
        }
    return {
        "root": f"{REPO}/data/kido/Dataset/Images",
        "zip": f"{REPO}/data/kido_dataset",
        "metadata": f"{REPO}/data/kido_metadata.csv",
        "output": local_output(),  # Colab'la aynı Drive klasörü
    }


# Ortama göre eğitim varsayılanları. Yerelde (RTX 4060, 8 GB) 448px'te batch 32 belleğe sığmıyor;
# 16 x 2 accumulation ile etkin batch Colab'daki gibi 32 kalır.
TRAINING_DEFAULTS = {
    "local": {"batch_size": 16, "accum_steps": 2, "num_workers": 2},
    "colab": {"batch_size": 32, "accum_steps": 1, "num_workers": 2},
}

ENV = detect_environment()
PATHS = environment_paths(ENV)
DEFAULTS = TRAINING_DEFAULTS[ENV]
