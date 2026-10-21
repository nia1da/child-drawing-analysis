"""Çizim ölçümleri: kompozisyon, renk, çizgi ve yapı. Tanımlar: docs/olcumler.md.

Bütün ölçümler kırpılmış sayfa (load_drawing) ve çizim maskesi (drawing_mask) üzerinden.
Parametreler KIDO'da kontrol edildi (2026-10-19):
- Renk sayısı: doygun pikseller (S > SAT_S, V > SAT_V; koyu piksellerde ton güvenilmez) 12 ton bölmesine
  (30°, kırmızı 0° çevresinde ortalı) ayrılır. Bir bölme, doygun piksellerin en az HUE_MIN_SHARE'i ve en az
  HUE_MIN_PIXELS piksel içeriyorsa sayılır. Siyah, gri, beyaz (renksiz) sayılmaz; kahverengi turuncu/kırmızı
  bölmesine düşer. Örnek: çok renkli 101-2E-182 -> 7, kırmızı kalp 211-7B-5298 -> 1, karakalem -> 0.
  Renk entropisi ve sıcak ton payı aynı bölmelerden.
- Koyu ton: çizim piksellerinden V < DARK_TONE_V olanların oranı. Siyah kalem/boya V ≈ 0-60, kurşun kalem
  grisi V ≈ 130-200: siyah kalemle çizilmiş 214-5G-159 -> 0.65, yoğun kurşun kalem gölgeleme 107-4D-943 -> 0.15.
- Boyama: maskeden PAINT_SIZE pikselden ince çizgiler morfolojik açmayla atılır, kalan kalın bölgeler "boyalı"
  sayılır; oranın paydası maskenin delikleri doldurulmuş hali (kontur içleri dahil).
- Kenar yoğunluğu: gri tonlu sayfada Canny (sigma CANNY_SIGMA); sadece maskenin EDGE_HALO piksel çevresindeki
  kenarlar sayılır, kağıt dokusu ve tarama izleri dışarıda kalsın.
- Renklilik ve kenar yoğunluğu iki şekilde: çizim piksellerine göre (_cizim, metin raporda) ve sayfaya göre
  (tablodaki tanım). Sayfaya göre olanlar dolulukla güçlü ilişkili (train, Spearman 0,76 / 0,87; sürüm 2).
"""
import numpy as np
from scipy import ndimage
from skimage.feature import canny
from skimage.morphology import skeletonize

from .mask import EIGHT, drawing_mask, faint_color_ratio, FAINT_FLAG, load_drawing, to_hsv

MEASUREMENT_VERSION = 3  # maske ya da ölçüm tanımı değişirse artır; normlar yeniden hesaplanmalı
SAT_S, SAT_V = 60, 60  # doygun piksel: renk ölçümleri için
HUE_BINS = 12
HUE_MIN_SHARE, HUE_MIN_PIXELS = 0.03, 50
WARM_BINS, COLD_BINS = (0, 1, 2), (4, 5, 6, 7, 8)  # kırmızı-turuncu-sarı (345°-75°), yeşil-camgöbeği-mavi (105°-255°)
DARK_TONE_V = 80
GRID = 3  # bölge dağılımı: sayfa 3 x 3
REGIONS = ["ust_sol", "ust_orta", "ust_sag", "orta_sol", "merkez", "orta_sag", "alt_sol", "alt_orta", "alt_sag"]
REGION_NAMES = ["üst sol", "üst orta", "üst sağ", "orta sol", "merkez", "orta sağ", "alt sol", "alt orta", "alt sağ"]
PAINT_SIZE = 7  # bundan ince (piksel) çizgiler boyama sayılmaz
CANNY_SIGMA, EDGE_HALO = 1.0, 2
MIN_PART = 30  # bileşen sayısında sayılan en küçük parça (piksel)

# Ölçüm kimliği -> (grup, görünen ad). JSON ve normlar bu sırayı kullanır (docs/olcumler.md tablosu).
MEASURE_INFO = {
    "doluluk_orani": ("Kompozisyon", "Doluluk oranı"),
    "agirlik_merkezi_x": ("Kompozisyon", "Ağırlık merkezi (x)"),
    "agirlik_merkezi_y": ("Kompozisyon", "Ağırlık merkezi (y)"),
    "kapsayan_kutu_orani": ("Kompozisyon", "Kapsayan kutu oranı"),
    **{f"doluluk_{k}": ("Kompozisyon", f"Bölge doluluğu ({n})") for k, n in zip(REGIONS, REGION_NAMES)},
    "renk_sayisi": ("Renk", "Farklı renk sayısı"),
    "renk_entropisi": ("Renk", "Renk entropisi"),
    "ortalama_doygunluk": ("Renk", "Ortalama doygunluk"),
    "koyu_ton_orani": ("Renk", "Koyu ton oranı"),
    "sicak_ton_payi": ("Renk", "Sıcak ton payı"),
    "renklilik_cizim": ("Renk", "Renklilik (Hasler–Süsstrunk, çizim pikselleri)"),
    "renklilik": ("Renk", "Renklilik (Hasler–Süsstrunk, sayfa)"),
    "boyama_orani": ("Renk", "Boyama oranı"),
    "kenar_yogunlugu_cizim": ("Çizgi ve yapı", "Kenar yoğunluğu (çizim pikseli başına)"),
    "kenar_yogunlugu": ("Çizgi ve yapı", "Kenar yoğunluğu (sayfa)"),
    "cizgi_uzunlugu": ("Çizgi ve yapı", "Toplam çizgi uzunluğu"),
    "cizgi_kalinligi": ("Çizgi ve yapı", "Ortalama çizgi kalınlığı"),
    "bilesen_sayisi": ("Çizgi ve yapı", "Bağlı bileşen sayısı"),
}
MEASURES = {k: label for k, (_, label) in MEASURE_INFO.items()}
INTEGER_MEASURES = {"renk_sayisi", "cizgi_uzunlugu", "bilesen_sayisi"}


# Kompozisyon

def fill_ratio(mask):
    return float(mask.mean())


def center_of_mass(mask):
    """Çizim piksellerinin ortalama konumu, sayfaya göre 0-1 (x: soldan, y: yukarıdan). Çizim yoksa (None, None)."""
    if not mask.any():
        return None, None
    ys, xs = np.nonzero(mask)
    h, w = mask.shape
    return float((xs.mean() + 0.5) / w), float((ys.mean() + 0.5) / h)


def bounding_box_ratio(mask):
    # Çizimi çevreleyen en küçük dikdörtgenin sayfaya oranı; çizim yoksa 0
    if not mask.any():
        return 0.0
    ys, xs = np.nonzero(mask)
    return float((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1) / mask.size)


def region_fill(mask, grid=GRID):
    """Sayfa grid x grid bölgeye bölünür (satır satır, üst soldan): her bölgenin doluluğu."""
    h, w = mask.shape
    rows, cols = np.linspace(0, h, grid + 1).astype(int), np.linspace(0, w, grid + 1).astype(int)
    return [float(mask[rows[i]:rows[i + 1], cols[j]:cols[j + 1]].mean()) for i in range(grid) for j in range(grid)]


# Renk

def hue_bins(hsv, mask):
    """Doygun çizim piksellerinin 12 ton bölmesindeki sayıları (bölme 0 = kırmızı, 0° ± 15°)."""
    h, s, v = (hsv[..., i][mask].astype(int) for i in range(3))
    saturated = (s > SAT_S) & (v > SAT_V)
    degrees = h[saturated] * 360 / 256  # PIL tonu 0-255
    bins = ((degrees + 360 / HUE_BINS / 2) // (360 / HUE_BINS)).astype(int) % HUE_BINS
    return np.bincount(bins, minlength=HUE_BINS)


def counted_bins(counts):
    # Renk sayısına giren bölmeler: doygun piksellerin en az %3'ü ve en az 50 piksel
    total = counts.sum()
    if total == 0:
        return np.zeros_like(counts, bool)
    return (counts >= HUE_MIN_SHARE * total) & (counts >= HUE_MIN_PIXELS)


def color_count(hsv, mask):
    return int(counted_bins(hue_bins(hsv, mask)).sum())


def color_entropy(counts):
    """Sayılan ton bölmelerinin dağılımının entropisi (bit). Tek renk ya da renksiz: 0; k eşit renk: log2(k)."""
    kept = counts[counted_bins(counts)].astype(float)
    if len(kept) < 2:
        return 0.0
    p = kept / kept.sum()
    return float(-(p * np.log2(p)).sum())


def warm_share(counts):
    """Sıcak tonların (kırmızı-sarı) sıcak + soğuk (mavi-yeşil) tonlara payı, 0-1. İkisi az ise None.

    Tablodaki "sıcak/soğuk oranı" pay olarak: soğuk ton hiç yokken oran sonsuz olurdu.
    """
    warm, cold = counts[list(WARM_BINS)].sum(), counts[list(COLD_BINS)].sum()
    if warm + cold < HUE_MIN_PIXELS:
        return None
    return float(warm / (warm + cold))


def mean_saturation(hsv, mask):
    # Çizim piksellerinin ortalama S'si, 0-1; çizim yoksa None
    if not mask.any():
        return None
    return float(hsv[..., 1][mask].mean() / 255)


def dark_tone_ratio(hsv, mask):
    # Çizim yoksa tanımsız (None)
    if not mask.any():
        return None
    return float((hsv[..., 2][mask] < DARK_TONE_V).mean())


def colorfulness(img, mask=None):
    """Hasler ve Süsstrunk (2003) renklilik ölçütü: σ_rgyb + 0,3 μ_rgyb.

    mask verilirse sadece çizim pikselleri üzerinde (çizim yoksa None): kağıt hesaba girmez, değer rengin
    canlılığını ölçer, çizimin büyüklüğünü değil. mask yoksa bütün sayfa (yayımlanan tanım): beyaz kağıt 0'a
    yakın; değer hem canlılığı hem renkli alanın büyüklüğünü yansıtır.
    """
    rgb = np.asarray(img, float)
    if mask is not None:
        if not mask.any():
            return None
        rgb = rgb[mask]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    rg, yb = r - g, 0.5 * (r + g) - b
    return float(np.hypot(rg.std(), yb.std()) + 0.3 * np.hypot(rg.mean(), yb.mean()))


def painted_mask(mask, size=PAINT_SIZE):
    # size pikselden ince çizgiler atılır; kalan kalın bölgeler boyanmış alan
    return ndimage.binary_opening(mask, structure=np.ones((size, size), bool))


def painted_ratio(mask):
    """Boyanmış alanın, konturların kapladığı alana (maske + kontur içleri) oranı. Çizim yoksa None.

    Sadece kontur: ≈ 0; içi boyanmış şekiller: 1'e yakın.
    """
    enclosed = ndimage.binary_fill_holes(mask)
    if not enclosed.any():
        return None
    return float(painted_mask(mask).sum() / enclosed.sum())


# Çizgi ve yapı

def edge_pixels(img, mask):
    """Canny kenar pikselleri; sadece maskenin yakınındakiler (kağıt dokusu, tarama izleri sayılmaz)."""
    gray = np.asarray(img.convert("L"), float) / 255
    near = ndimage.binary_dilation(mask, iterations=EDGE_HALO)
    return canny(gray, sigma=CANNY_SIGMA) & near


def edge_density(edges, mask):
    """(çizim pikseli başına, sayfaya göre) kenar yoğunluğu. Çizim yoksa (None, 0)."""
    if not mask.any():
        return None, 0.0
    return float(edges.sum() / mask.sum()), float(edges.mean())


def line_measures(mask):
    """İskelet uzunluğu (piksel) ve iskelet boyunca ortalama kalınlık (piksel, 2d - 1; d = kenara uzaklık)."""
    skeleton = skeletonize(mask)
    length = int(skeleton.sum())
    if length == 0:
        return 0, None
    distance = ndimage.distance_transform_edt(mask)
    return length, float((2 * distance[skeleton] - 1).mean())


def component_count(mask, min_size=MIN_PART):
    labels, n = ndimage.label(mask, structure=EIGHT)
    if n == 0:
        return 0
    return int((np.bincount(labels.ravel())[1:] >= min_size).sum())


def measure_image(img):
    """Kırpılmış RGB görüntü (load_drawing) -> ölçümler ve kalite bilgisi."""
    hsv = to_hsv(img)
    mask = drawing_mask(hsv)
    counts = hue_bins(hsv, mask)
    cx, cy = center_of_mass(mask)
    length, thickness = line_measures(mask)
    faint = faint_color_ratio(hsv, mask)
    edges_per_pixel, edges_per_page = edge_density(edge_pixels(img, mask) if mask.any() else None, mask)
    values = {
        "doluluk_orani": fill_ratio(mask),
        "agirlik_merkezi_x": cx,
        "agirlik_merkezi_y": cy,
        "kapsayan_kutu_orani": bounding_box_ratio(mask),
        **{f"doluluk_{k}": v for k, v in zip(REGIONS, region_fill(mask))},
        "renk_sayisi": int(counted_bins(counts).sum()),
        "renk_entropisi": color_entropy(counts),
        "ortalama_doygunluk": mean_saturation(hsv, mask),
        "koyu_ton_orani": dark_tone_ratio(hsv, mask),
        "sicak_ton_payi": warm_share(counts),
        "renklilik_cizim": colorfulness(img, mask),
        "renklilik": colorfulness(img),
        "boyama_orani": painted_ratio(mask),
        "kenar_yogunlugu_cizim": edges_per_pixel,
        "kenar_yogunlugu": edges_per_page,
        "cizgi_uzunlugu": length,
        "cizgi_kalinligi": thickness,
        "bilesen_sayisi": component_count(mask),
    }
    assert list(values) == list(MEASURES)
    return {**values, "soluk_renk_orani": faint, "soluk_renk_bayragi": faint >= FAINT_FLAG}


def measure(path):
    return measure_image(load_drawing(path))
