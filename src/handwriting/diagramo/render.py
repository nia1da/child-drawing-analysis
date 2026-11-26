"""Koordinat (SVC) → statik PNG: yalnız kalemin yüzeyde olduğu noktalar çizilir, kalem kalkınca çizgiler birleştirilmez.

İlkeler:
- Birim: x, y milimetre. **Tablet koordinatında y yukarı doğru artar (sol-alt orijin)**: EDA'da 60/60 yazma kaydında ilk vuruşların ortalama y'si son vuruşlardan büyük
  (yazı yukarıdan aşağı ilerler); varsayılan `y_up=True` y'yi `TABLET_MM[1] - y` ile çevirir, görüntüde yukarıdan aşağı okunur.
- **Fiziksel mod** (`px_per_mm`): ölçek = mm başına piksel, her örnek kendi sınırlarına göre kırpılır (kenarlık `margin_mm`); veri seti genelinde
  istatistik/normalizasyon yok. En-boy oranı ve yazı boyutu (mm) korunur. `canvas="tablet"` tablet etkin alanının tamamını çizer.
  Kâğıt (sayfa) boyutu veri setinde **yazmıyor**; bu yüzden gerçek sayfa boyutu varsayılmaz.
- **Sığdırma modu** (`fit_px`): uzun kenar `fit_px` piksel olacak şekilde tek bir ölçekle (en-boy oranı korunur) küçültür/büyütür.
- Beyaz arka plan, sabit piksel kalınlığında siyah çizgi; kenar yumuşatma için 2x örnekleyip küçültülür.
- Hız, basınç, eğim ve vuruş sırası çıktı görüntüde **yoktur** (statik fotoğraftan elde edilemez).
"""
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

from .io import read_svc

TABLET_MM = (348.16, 203.2)  # gözlenen koordinat üst sınırı (EDA): etkin alan boyutu belgelenmemiş, veriden okundu
SS = 2                        # alt örnekleme çarpanı


@dataclass
class Rendered:
    image: Image.Image
    px_per_mm: float
    bbox_mm: tuple          # (x0, y0, x1, y1) çizilen noktaların mm sınırları (görüntü yönünde: y aşağı, y_up çevrilmişse çevrilmiş)
    origin_mm: tuple        # görüntü sol-üst köşesinin mm koordinatı
    n_strokes: int
    n_points: int


def split_strokes(df, max_gap_s=0.05, max_jump_mm=10.0):
    """pen==1 noktalarını vuruşlara böler. Yeni vuruş: kalem havadan yüzeye inince, zaman boşluğu > `max_gap_s` ya da
    ardışık iki nokta arası mesafe > `max_jump_mm` (donanım atlaması) olunca. Döner: [(n_i, 2) mm dizileri]."""
    on = df["pen"].values == 1
    if not on.any():
        return []
    t, x, y = df["t"].values, df["x"].values, df["y"].values
    prev_on = np.r_[False, on[:-1]]
    dt = np.r_[0.0, np.diff(t)]
    jump = np.r_[0.0, np.hypot(np.diff(x), np.diff(y))]
    new = on & (~prev_on | (dt > max_gap_s) | (jump > max_jump_mm))
    ids = np.cumsum(new)[on]
    pts = np.c_[x[on], y[on]]
    return np.split(pts, np.flatnonzero(np.diff(ids)) + 1)


def render_strokes(strokes, px_per_mm=6.0, fit_px=None, canvas="bbox", margin_mm=8.0, line_px=3, y_up=True):
    """Vuruş listesinden PNG. `fit_px` verilirse uzun kenar o kadar piksel olur (ölçek bağımsız, en-boy korunur)."""
    if not strokes:
        raise ValueError("çizilecek vuruş yok (kalem hiç yüzeye temas etmemiş)")
    if y_up:  # tablet y'si yukarı doğru; görüntü y'si aşağı doğru
        strokes = [np.c_[s[:, 0], TABLET_MM[1] - s[:, 1]] for s in strokes]
    allp = np.vstack(strokes)
    bbox = (float(allp[:, 0].min()), float(allp[:, 1].min()), float(allp[:, 0].max()), float(allp[:, 1].max()))
    if canvas == "tablet":
        origin, size = (0.0, 0.0), TABLET_MM
    elif isinstance(canvas, tuple):
        origin, size = (0.0, 0.0), canvas
    else:  # bbox
        origin = (bbox[0] - margin_mm, bbox[1] - margin_mm)
        size = (bbox[2] - bbox[0] + 2 * margin_mm, bbox[3] - bbox[1] + 2 * margin_mm)
    if fit_px:
        px_per_mm = fit_px / max(size)
    W, H = max(1, int(round(size[0] * px_per_mm))), max(1, int(round(size[1] * px_per_mm)))
    im = Image.new("L", (W * SS, H * SS), 255)
    d = ImageDraw.Draw(im)
    s = px_per_mm * SS
    w = max(1, int(round(line_px * SS)))
    for st in strokes:
        xy = [((x - origin[0]) * s, (y - origin[1]) * s) for x, y in st]
        if len(xy) == 1:  # tek noktalı vuruş: nokta
            x, y = xy[0]; d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=0)
        else:
            d.line(xy, fill=0, width=w, joint="curve")
            for x, y in (xy[0], xy[-1]):  # uç yuvarlatma
                d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=0)
    im = im.resize((W, H), Image.BOX)
    return Rendered(im, float(px_per_mm), bbox, origin, len(strokes), int(len(allp)))


def render_svc(path, **kw):
    """SVC dosyasından PNG (Rendered). `max_gap_s`/`max_jump_mm` split_strokes'a, diğerleri render_strokes'a gider."""
    split_kw = {k: kw.pop(k) for k in ("max_gap_s", "max_jump_mm") if k in kw}
    return render_strokes(split_strokes(read_svc(path), **split_kw), **kw)
