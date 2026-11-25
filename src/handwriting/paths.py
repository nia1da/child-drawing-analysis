"""El yazısı modülü: yollar, sabitler ve FD-LEX veri koruması.

FD-LEX verisi (ve türevleri) kullanım izni netleşene kadar yalnız yerel diskte kalır:
Colab'da çalışmaz, Drive / OneDrive altındaki bir yola yazılmaz. Bu modül `src.config`'i
bilerek içe aktarmaz (o Drive yollarını çözer); ortam algısı burada ayrıca ve küçük tutulur.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FD_LEX = REPO / "data" / "handwriting" / "fd_lex"

WORK_DPI = 150          # çalışma çözünürlüğü (karar 2026-11-25); 200 ve 300 duyarlılık testi için
RULE_SPACING_MM = 10.8  # basılı çizgi aralığı (EDA, 288 sayfa; tüm sayfalarda doğrulanmadı)
HW_VERSION = "hw-0.1"   # ölçüm tanımı değişirse artırılır

# Yol parçalarında bu adlar geçerse veri yolu reddedilir (bulut senkronu / Drive)
FORBIDDEN_PARTS = ("onedrive", "google drive", "googledrive", "gdrive", "my drive", "mydrive", "drive'ım", "bitirme")


def is_colab():
    env = os.environ.get("CIZIM_ENV")
    if env:
        return env == "colab"
    return "COLAB_RELEASE_TAG" in os.environ


def require_local():
    if is_colab():
        raise RuntimeError("FD-LEX verisi Colab'da kullanılamaz (kullanım izni netleşmedi); yalnız yerel çalışır.")


def check_data_dir(path):
    """Yol bulut senkronu / Drive altındaysa hata verir; yoksa çözülmüş yolu döner."""
    p = Path(path).resolve()
    low = [part.lower() for part in p.parts]
    if "/content/drive" in p.as_posix().lower():  # Colab'da bağlanmış Drive
        raise RuntimeError(f"FD-LEX yolu Colab Drive'ında olamaz: {p}")
    for bad in FORBIDDEN_PARTS:
        if any(bad in part for part in low):
            raise RuntimeError(f"FD-LEX yolu bulut/Drive klasöründe olamaz ('{bad}' geçiyor): {p}")
    return p


def fd_lex_dir(path=None):
    """Yerel FD-LEX klasörü (koruma kontrolleriyle). Sentetik testler bu fonksiyonu çağırmaz."""
    require_local()
    return check_data_dir(path or FD_LEX)
