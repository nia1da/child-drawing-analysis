"""Çizim maskesi: hangi pikseller çizime ait?

Bir piksel çizime aittir, eğer
- parlaklığı (V) belirgin şekilde düşükse (kurşun kalem, siyah, koyu boya), ya da
- doygunluğu (S) kağıt gürültüsünün üstündeyse (renkli kalem, boya).

Eşikler KIDO'dan ölçülerek seçildi (2026-10-19, 1500 rastgele çizim):
- Kağıt neredeyse her zaman beyaz (V ortancası 254–255). Gri görünen sayfalar tamamen boyanmış çizimler.
- Boş sayfalarda kağıdın S'si: 95. yüzdelik en çok 23. Soluk sarı kalem çizgisinde S ortancası 43,
  alt çeyrek 32 -> COLOR_S = 30.
- Silinmiş kalem / arka yüzden geçen hayalet izler V ≈ 230–250; kalem çizgileri bunun altında -> DARK_V = 230.
- Tarama gölgesi kenarın ilk 3 pikselinde (koyu piksel oranı %9,4 / %3,1 / %1,4; sonra %0,3–0,6) -> CROP = 4.
- Histerezis (Canny'deki gibi): kesin eşikleri (DARK_V, COLOR_S) geçen pikseller çekirdek; daha gevşek
  eşikleri (WEAK_V, WEAK_S) geçenler sadece bir çekirdeğe bağlı bir parçadaysa çizime katılır. Soluk renkli
  kalem çizgilerinin kopuk kalmaması için; kağıttaki bağımsız hayalet izler çekirdek içermediğinden dışarıda kalır.
- Eşik sınırındaki tek tük gürültü pikselleri MIN_COMPONENT'ten küçük bağlı parçalar olarak atılır;
  ince ama bağlı kalem çizgileri bundan etkilenmez.
- Kırpmadan sonra da kalan tarama kenar çizgileri (kontrol sayfasında görüldü): piksellerinin en az
  EDGE_SHARE'i kenara EDGE_BAND pikselden yakın olan parçalar atılır. Kenardan içeri uzanan boyamalar kalır;
  bedeli: kenara 10 pikselden yakın çizilmiş bir çerçeve de atılır.
"""
import numpy as np
from PIL import Image
from scipy import ndimage

CROP = 4  # kenarlardan kırpılan piksel (tarama gölgesi)
DARK_V = 230  # V bunun altındaysa çizim (0-255)
COLOR_S = 30  # S bunun üstündeyse çizim (0-255)
WEAK_V, WEAK_S = 240, 20  # gevşek eşikler: sadece çekirdeğe bağlı parçalarda
MIN_COMPONENT = 8  # bundan küçük bağlı parçalar gürültü sayılır (piksel)
EDGE_BAND, EDGE_SHARE = 10, 0.9  # kenar şeridi (piksel) ve parçanın şeritte kalma oranı
EIGHT = np.ones((3, 3), bool)  # 8-komşuluk: çapraz değen pikseller aynı parça


def load_drawing(path, crop=CROP):
    """Görüntüyü RGB olarak açar ve kenarlarını kırpar; bütün ölçümler bu kırpılmış sayfa üzerinden."""
    img = Image.open(path).convert("RGB")
    return crop_border(img, crop)


def crop_border(img, crop=CROP):
    w, h = img.size
    return img.crop((crop, crop, w - crop, h - crop)) if crop > 0 else img


def to_hsv(img):
    """PIL HSV: H, S, V hepsi 0-255 (uint8), şekil (yükseklik, genişlik, 3)."""
    return np.asarray(img.convert("HSV"))


def remove_small_components(mask, min_size=MIN_COMPONENT):
    labels, n = ndimage.label(mask, structure=EIGHT)
    if n == 0:
        return mask
    sizes = np.bincount(labels.ravel())
    keep = sizes >= min_size
    keep[0] = False  # arka plan
    return keep[labels]


def remove_edge_components(mask, band=EDGE_BAND, share=EDGE_SHARE):
    labels, n = ndimage.label(mask, structure=EIGHT)
    if n == 0:
        return mask
    edge = np.zeros(mask.shape, bool)
    edge[:band], edge[-band:], edge[:, :band], edge[:, -band:] = True, True, True, True
    total = np.bincount(labels.ravel(), minlength=n + 1)
    in_band = np.bincount(labels[edge], minlength=n + 1)
    keep = in_band < share * total
    keep[0] = False
    return keep[labels]


def drawing_mask(hsv, dark_v=DARK_V, color_s=COLOR_S, weak_v=WEAK_V, weak_s=WEAK_S, min_component=MIN_COMPONENT):
    """hsv: to_hsv çıktısı. Çizime ait pikseller True."""
    s, v = hsv[..., 1], hsv[..., 2]
    strong = (v < dark_v) | (s > color_s)
    weak = strong | (v < weak_v) | (s > weak_s)
    labels, n = ndimage.label(weak, structure=EIGHT)
    has_seed = np.zeros(n + 1, bool)
    has_seed[labels[strong]] = True
    has_seed[0] = False
    return remove_edge_components(remove_small_components(has_seed[labels], min_component))
