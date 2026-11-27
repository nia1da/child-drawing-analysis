"""Statik yazı görüntüsünden (kural çizgisiz) geometrik özellikler. Girdi yalnız ikili mürekkep maskesidir: hız, basınç, zaman, vuruş sırası yoktur.

Ölçü birimi `tb` = tablet birimi (README'de birim yazmıyor; muhtemelen mm, doğrulanmadı). Mümkün olduğunca oranlar (x-yüksekliği ve satır aralığına göre) kullanılır.
Yöntem (el yazısı fotoğraf hattındaki kavramların kural çizgisiz karşılığı):
- satırlar: yatay mürekkep profili (otokorelasyonla satır aralığı, tepe noktaları satır bandı merkezleri); x-yüksekliği = satırın yoğun bandı (profil ≥ %50 tepe),
  taban çizgisi = bandın alt kenarı; eğim ve dalgalanma: satırı yatayda parçalara bölüp her parçanın taban kenarına Theil–Sen doğrusu.
- bağlı bileşenler (8 komşuluk): boyut dağılımı, bileşenler arası boşluk (bitişik yazıda "kelime" ile "harf parçası" ayrımı güvenilir değil).
- kesişim/örtüşme: iskelet düğüm yoğunluğu, satırlar arası bölgedeki mürekkep, çok uzun bileşenler; karalama: açma (opening) ile kalan kalın bölge payı.
"""
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage as ndi
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.stats import theilslopes
from skimage.morphology import disk, skeletonize

MIN_COMP_PX = 8


def load_ink(path):
    return np.asarray(Image.open(path).convert("L")) < 128


def _cv(v):
    v = np.asarray(v, float)
    return float(np.std(v) / np.mean(v)) if len(v) > 1 and np.mean(v) > 0 else np.nan


def _iqr_ratio(v):
    v = np.asarray(v, float)
    return float((np.percentile(v, 75) - np.percentile(v, 25)) / np.median(v)) if len(v) > 4 and np.median(v) > 0 else np.nan


def estimate_pitch(profile, ppu, lo_tb=7.0, hi_tb=22.0):
    """Satır aralığı (piksel): yatay profil otokorelasyonunun [7, 22] tb aralığındaki en yüksek tepesi; bulunamazsa 11 tb."""
    p = profile - profile.mean()
    ac = np.correlate(p, p, "full")[len(p) - 1:]
    lo, hi = int(lo_tb * ppu), int(hi_tb * ppu)
    if len(ac) <= hi or ac[0] <= 0:
        return 11.0 * ppu
    return float(np.argmax(ac[lo:hi]) + lo)


def find_lines(profile, pitch):
    """Satır merkezleri (profil tepeleri) ve sınırları (komşu tepeler arasındaki en düşük nokta)."""
    sm = gaussian_filter1d(profile.astype(float), pitch / 6)
    peaks, _ = find_peaks(sm, distance=0.65 * pitch, height=0.08 * sm.max())
    if len(peaks) == 0:
        return np.array([], int), np.array([0, len(profile)])
    mid = [int(a + np.argmin(sm[a:b])) for a, b in zip(peaks[:-1], peaks[1:])]
    return peaks, np.array([0] + mid + [len(profile)])


def band_edges(profile, center, frac=0.5):
    """Yoğun x-yüksekliği bandı: merkez çevresinde profil ≥ frac * tepe olan bitişik satırlar. Döner (üst, alt) ya da None."""
    pk = profile[max(0, center - 3):center + 4].max()
    if pk <= 0:
        return None
    top = center
    while top > 0 and profile[top - 1] >= frac * pk:
        top -= 1
    bot = center
    while bot < len(profile) - 1 and profile[bot + 1] >= frac * pk:
        bot += 1
    return top, bot


def line_measures(ink, peaks, bounds, pitch, ppu):
    rows = []
    chunk = int(12 * ppu)
    for k, c in enumerate(peaks):
        sub = ink[bounds[k]:bounds[k + 1]]
        prof = sub.sum(1).astype(float)
        b = band_edges(gaussian_filter1d(prof, 1.0), int(c - bounds[k]))
        if b is None or sub.sum() < 200:
            continue
        cols = np.flatnonzero(sub.sum(0) >= 2)
        x0, x1 = (int(cols.min()), int(cols.max())) if len(cols) else (0, 0)
        # parça parça taban kenarı
        xs, bs = [], []
        for s in range(x0, x1, chunk):
            ch = sub[:, s:s + chunk]
            if ch.sum() < 150:
                continue
            p = gaussian_filter1d(ch.sum(1).astype(float), 1.0)
            e = band_edges(p, int(np.argmax(p)))
            if e:
                xs.append(s + ch.shape[1] / 2); bs.append(e[1] + bounds[k])
        r = dict(line=k, center=float(c), xh=float(b[1] - b[0] + 1), base=float(b[1] + bounds[k]), x0=x0, x1=x1, ink=int(sub.sum()))
        if len(xs) >= 4:
            sl, ic, _, _ = theilslopes(bs, xs)
            res = np.asarray(bs) - (ic + sl * np.asarray(xs))
            r.update(slope_deg=float(np.degrees(np.arctan(sl))), wobble=float(1.4826 * np.median(np.abs(res - np.median(res)))), sl=float(sl), ic=float(ic))
        rows.append(r)
    return pd.DataFrame(rows)


def features_from_ink(ink, ppu=4.0, canvas=True):
    """ink: bool (H, W). `canvas=True`: tablet tuvali (kenar boşlukları tablet kenarına göre anlamlı); False: kırpılmış görüntü (kenar boşluğu özellikleri NaN)."""
    H, W = ink.shape
    f = {}
    total = int(ink.sum())
    if total < 50:
        return dict(ok=False)
    prof = ink.sum(1).astype(float)
    pitch = estimate_pitch(prof, ppu)
    peaks, bounds = find_lines(prof, pitch)
    lm = line_measures(ink, peaks, bounds, pitch, ppu)
    f.update(ok=len(lm) >= 2, n_lines=int(len(lm)), pitch_tb=pitch / ppu)

    lab, n = ndi.label(ink, structure=np.ones((3, 3)))
    sl = ndi.find_objects(lab)
    area = ndi.sum(ink, lab, range(1, n + 1))
    keep = [i for i, a in enumerate(area) if a >= MIN_COMP_PX]
    bb = np.array([[sl[i][0].start, sl[i][0].stop, sl[i][1].start, sl[i][1].stop] for i in keep])
    ar = area[keep]
    h, w = (bb[:, 1] - bb[:, 0]) / ppu, (bb[:, 3] - bb[:, 2]) / ppu
    cy = (bb[:, 0] + bb[:, 1]) / 2
    xh_tb = float(np.median(lm.xh)) / ppu if len(lm) else np.nan
    f.update(xh_tb=xh_tb, xh_cv_lines=_cv(lm.xh) if len(lm) else np.nan, xh_over_pitch=xh_tb * ppu / pitch if len(lm) else np.nan,
             comp_h_med_tb=float(np.median(h)), comp_h_iqr_ratio=_iqr_ratio(h), comp_w_med_tb=float(np.median(w)), n_comps=int(len(keep)),
             comp_h_over_xh=float(np.median(h)) / xh_tb if xh_tb == xh_tb and xh_tb > 0 else np.nan)

    if "slope_deg" in lm:
        s = lm.slope_deg.dropna()
        f.update(slope_med_deg=float(s.median()) if len(s) else np.nan, slope_abs_med_deg=float(s.abs().median()) if len(s) else np.nan, slope_sd_deg=float(s.std()) if len(s) > 1 else np.nan,
                 wobble_med_tb=float(lm.wobble.median()) / ppu, wobble_over_xh=float(lm.wobble.median() / lm.xh.median()))
    if len(lm) >= 2:
        base = lm.base.values
        f["pitch_cv"] = _cv(np.diff(base)) if len(base) > 2 else np.nan
        f["left_edge_sd_over_xh"] = float(lm.x0.std() / lm.xh.median())
        ln = (lm.x1 - lm.x0).values / ppu
        f.update(right_edge_sd_over_width=float(lm.x1.std() / max(np.mean(lm.x1 - lm.x0), 1)), line_len_med_tb=float(np.median(ln)), line_len_cv=_cv(ln))

    # satırlara atanmış / aykırı bileşenler, bileşenler arası boşluk
    line_of = np.full(len(keep), -1)
    if len(lm):
        top, bot = bounds[lm.line.min()], bounds[lm.line.max() + 1]
        for j, c in enumerate(cy):
            if top <= c < bot:
                line_of[j] = int(np.searchsorted(bounds, c, side="right") - 1)
    stray = line_of < 0
    f["stray_ink_frac"] = float(ar[stray].sum() / ar.sum())
    gaps = []
    for k in set(line_of[~stray]):
        idx = np.flatnonzero(line_of == k); idx = idx[np.argsort(bb[idx, 2])]
        reach = bb[idx[0], 3]
        for j in idx[1:]:
            gaps.append(bb[j, 2] - reach); reach = max(reach, bb[j, 3])
    gaps = np.asarray([g for g in gaps if g > 0], float)
    if len(gaps) > 5 and xh_tb == xh_tb:
        g = gaps / ppu / xh_tb
        f.update(gap_med_over_xh=float(np.median(g)), gap_cv=_cv(g), wide_gap_share=float((g > 1.0).mean()))
    f["tall_comp_frac"] = float(((bb[:, 1] - bb[:, 0]) > 1.2 * pitch).mean())
    # satırlar arası bölgede mürekkep
    if len(peaks):
        d = np.abs(np.arange(H)[:, None] - peaks[None, :]).min(1)
        f["valley_ink_frac"] = float(ink[d > 0.4 * pitch].sum() / total)

    # iskelet: kesişim/düğüm yoğunluğu ve uzunluk
    sk = skeletonize(ink)
    nb = ndi.convolve(sk.astype(np.uint8), np.ones((3, 3), np.uint8), mode="constant") - 1
    sk_n = int(sk.sum())
    f.update(skel_len_tb=sk_n / ppu, junction_density=float(((nb >= 3) & sk).sum() / max(sk_n, 1)), ink_area_tb2=total / ppu ** 2,
             ink_per_line_tb2=total / ppu ** 2 / max(len(lm), 1))
    # karalama: stroke kalınlığından kalın bölgeler
    edt = ndi.distance_transform_edt(ink)
    f["thick_frac"] = float((edt[ink] >= 3.5).mean())                 # çizgi kalınlığı 3 px: ≥ 7 px kalınlık = üst üste binmiş vuruş/leke
    op = ndi.binary_opening(ink, structure=disk(4))
    f["blob_frac"] = float(op.sum() / total)
    labo, no = ndi.label(op, structure=np.ones((3, 3)))
    f["largest_blob_tb2"] = float(np.bincount(labo.ravel())[1:].max() / ppu ** 2) if no else 0.0

    # sayfa kullanımı (yalnız satırlara atanmış bileşenlerle sağlam sınır; ham sınır ayrıca)
    rows_, cols_ = np.flatnonzero(ink.any(1)), np.flatnonzero(ink.any(0))
    f.update(bbox_w_tb=float(cols_.max() - cols_.min() + 1) / ppu, bbox_h_tb=float(rows_.max() - rows_.min() + 1) / ppu)
    if (~stray).any():
        b2 = bb[~stray]
        f.update(rbbox_w_tb=float(b2[:, 3].max() - b2[:, 2].min()) / ppu, rbbox_h_tb=float(b2[:, 1].max() - b2[:, 0].min()) / ppu)
        if canvas:
            f.update(left_margin_tb=float(b2[:, 2].min()) / ppu, right_margin_tb=float(W - b2[:, 3].max()) / ppu, top_margin_tb=float(b2[:, 0].min()) / ppu,
                     bottom_margin_tb=float(H - b2[:, 1].max()) / ppu, rbbox_area_frac=float((b2[:, 3].max() - b2[:, 2].min()) * (b2[:, 1].max() - b2[:, 0].min()) / (H * W)))
    if canvas:
        f.update(left_margin_raw_tb=float(cols_.min()) / ppu, bottom_margin_raw_tb=float(H - 1 - rows_.max()) / ppu)
    return f


def features_for_image(path, ppu=4.0, canvas=True):
    return features_from_ink(load_ink(path), ppu, canvas)


def coord_lines(strokes, bin_tb=0.25):
    """Koordinatlardan satır sayısı ve aralığı (görüntü tabanlı bölütlemeyi doğrulamak için): pen-down noktaların y histogramına aynı yöntem."""
    y = np.concatenate([s[:, 1] for s in strokes])
    h, _ = np.histogram(y, bins=np.arange(y.min(), y.max() + bin_tb, bin_tb))
    pad = int(25 / bin_tb)                      # kenar tepelerini yutmamak için sıfır dolgu (görüntüdeki beyaz kenar boşluğu gibi)
    h = np.r_[np.zeros(pad), h, np.zeros(pad)]
    ppu = 1.0 / bin_tb
    pitch = estimate_pitch(h.astype(float), ppu)
    peaks, _ = find_lines(h.astype(float), pitch)
    return dict(coord_n_lines=int(len(peaks)), coord_pitch_tb=pitch / ppu)


def _row(args):
    path, name, ppu, canvas = args
    try:
        r = features_for_image(path, ppu, canvas)
    except Exception as e:  # bozuk görüntü
        r = dict(ok=False, error=str(e)[:60])
    r["image"] = name
    return r


def feature_table(images, variant="tablet", ppu=4.0, workers=4):
    """Manifest (sütun `image`) için özellik tablosu; `variant`: 'tablet' (kenar boşlukları anlamlı) ya da 'crop'."""
    from concurrent.futures import ProcessPoolExecutor

    from .io import ROOT
    base = ROOT / "processed" / "images" / variant
    jobs = [(base / n, n, ppu, variant == "tablet") for n in images]
    with ProcessPoolExecutor(workers) as ex:
        return pd.DataFrame(list(ex.map(_row, jobs, chunksize=8)))


if __name__ == "__main__":
    from .io import ROOT
    m = pd.read_csv(ROOT / "manifests" / "images.csv", encoding="utf-8")
    for v in ("tablet", "crop"):
        ft = feature_table(m.image, v)
        ft.to_csv(ROOT / "manifests" / f"features_{v}.csv", index=False, encoding="utf-8", lineterminator="\n")
        print(v, "özellik tablosu:", ft.shape, "| ok:", int(ft.ok.sum()))
