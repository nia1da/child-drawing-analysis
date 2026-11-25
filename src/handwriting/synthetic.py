"""Sentetik A4 el yazısı sayfaları (gerçek veri yok): bilinen gerçek değerli test girdisi.

İki aşama: `make_layout` her şeyi milimetre cinsinden üretir (çözünürlükten bağımsız, tohumla tekrarlanır),
`render` belirli dpi, kalem rengi, eğiklik, gürültü ve JPEG ile piksele çevirir. Böylece aynı sayfa 150/200/300 dpi
ve farklı kalemlerle üretilip ölçümün dayanıklılığı sınanabilir.

Sayfa yapısı gerçek FD-LEX taramalarını taklit eder: gri basılı çizgiler, sağ üstte kod kutusu (içine elle kod),
alt telif satırı ve imza yerine siyah "XXX" (bu ikisi tarama dışı vektör katmanı: eğiklikten etkilenmez).
Yazı "harfleri" elips, gövde (yükselen) ve inen çizgilerden oluşur; gerçek el yazısının yerini tutmaz.
"""
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

A4_MM = (210.0, 297.0)
PENS = {"blue": (30, 50, 170), "black": (25, 25, 25), "pencil": (120, 120, 120)}
RULE_GRAY = 105


@dataclass
class Layout:
    strokes: list            # (noktalar_mm (n,2), kalınlık_mm) elle yazı
    code_strokes: list       # kod kutusu içindeki elle kod
    rules_mm: list           # çizgilerin y konumu (mm)
    box_mm: tuple            # kod kutusu (x0, y0, x1, y1) mm
    xxx_mm: tuple            # XXX kutusu (x0, y0, x1, y1) mm ya da None
    truth: dict = field(default_factory=dict)


def _jitter(pts, rng, s=0.04):
    return pts + rng.normal(0, s, pts.shape)


def make_layout(seed=0, n_rules=23, spacing_mm=10.8, first_rule_mm=45.0, used_lines=8, xh_mm=3.0, size_cv=0.12,
                baseline_gap_mm=1.2, slope_deg=0.0, wobble_mm=0.15, fill=0.8, word_gap_xh=1.0, stroke_mm=0.45,
                left_mm=22.0, right_mm=195.0, with_xxx=True, with_code=True, skip_lines=()):
    """`skip_lines`: atlanan (boş bırakılan) satır indeksleri. Çizgi k'nın üstündeki satır = k."""
    rng = np.random.default_rng(seed)
    rules = [first_rule_mm + k * spacing_mm for k in range(n_rules)]
    tan = np.tan(np.radians(slope_deg))
    strokes, offsets, used, heights = [], [], [], []
    for line in range(used_lines):
        if line in skip_lines:
            continue
        used.append(line)
        rule_y, x = rules[line], left_mm
        x_end = left_mm + fill * (right_mm - left_mm)
        mid_x = (left_mm + x_end) / 2
        offsets.append(baseline_gap_mm - (mid_x - left_mm) * tan)
        while x < x_end:
            n_letters = int(rng.integers(2, 7))
            for _ in range(n_letters):
                w = xh_mm * 0.8 * (1 + rng.normal(0, 0.1))
                h = xh_mm * (1 + rng.normal(0, size_cv))
                base = rule_y - baseline_gap_mm + (x - left_mm) * tan + rng.normal(0, wobble_mm)
                kind = rng.choice(["o", "o", "l", "j", "n"])
                if kind == "o":
                    t = np.linspace(0, 2 * np.pi, 28)
                    pts = np.c_[x + w / 2 + w / 2 * np.cos(t), base - h / 2 + h / 2 * np.sin(t)]
                    heights.append(h)
                elif kind == "n":  # gövde + yay (x-yüksekliği)
                    t = np.linspace(np.pi, 2 * np.pi, 14)
                    arc = np.c_[x + w / 2 + w / 2 * np.cos(t), base - h + h / 2 * np.sin(t) + h / 2]
                    pts = np.vstack([[x, base], [x, base - h + h / 2], arc, [x + w, base]])
                    heights.append(h)
                elif kind == "l":  # yükselen
                    pts = np.array([[x + w / 2, base - 1.8 * h], [x + w / 2, base]])
                else:              # inen
                    pts = np.array([[x + w / 2, base - h], [x + w / 2, base + 0.6 * h]])
                strokes.append((_jitter(pts, rng), stroke_mm))
                x += w + 0.25 * xh_mm
            x += word_gap_xh * xh_mm
    box = (150.0, 22.0, 200.0, 36.0)
    code = []
    if with_code:
        cx = box[0] + 4
        for _ in range(8):
            t = np.linspace(0, 2 * np.pi, 20)
            code.append((_jitter(np.c_[cx + 1.4 + 1.4 * np.cos(t), 29 + 2.0 * np.sin(t)], rng), 0.4)); cx += 5.5
    xxx = None
    if with_xxx:
        y = rules[min(used_lines, n_rules - 2)] - 9
        xxx = (150.0, y, 178.0, y + 7.5)
    off = float(np.median(offsets)) if offsets else None
    # mürekkep kenarları çizgi kalınlığı kadar dışa taşar: ölçülen yükseklik h + kalınlık, taban kalınlığın yarısı aşağıda
    truth = dict(xh_mm=xh_mm, xh_ink_mm=xh_mm + stroke_mm, baseline_offset_mm=off, baseline_offset_ink_mm=None if off is None else off - stroke_mm / 2,
                 slope_deg=slope_deg,
                 used_lines=len(used), n_rules=n_rules, spacing_mm=spacing_mm, left_margin_mm=left_mm,
                 used_idx=used, wobble_mm=wobble_mm)
    return Layout(strokes, code, rules, box, xxx, truth)


def _px(v, dpi):
    return np.asarray(v) * dpi / 25.4


def _draw_strokes(draw, strokes, scale, fill=255):
    for pts, wmm in strokes:
        xy = [tuple(p) for p in _px(pts, scale)]
        draw.line(xy, fill=fill, width=max(1, int(round(wmm * scale / 25.4))), joint="curve")


def render(layout, dpi=150, pen="blue", skew_deg=0.0, noise=3.0, gradient=8.0, jpeg_quality=None, seed=0, bake_overlay=True):
    """Piksele çevirir. Döner: (rgb uint8, hw_truth bool, overlay_boxes_px [telif satırı + XXX], info)."""
    rng = np.random.default_rng(seed)
    W, H = (int(round(m * dpi / 25.4)) for m in A4_MM)
    ss = 2 if dpi <= 200 else 1  # alt örnekleme: kenarlar yumuşak
    big = (W * ss, H * ss)

    def layer(strokes=(), rects=()):
        im = Image.new("L", big, 0); d = ImageDraw.Draw(im)
        for (x0, y0, x1, y1), wmm in rects:
            d.rectangle([*_px((x0, y0), dpi * ss), *_px((x1, y1), dpi * ss)], outline=255, width=max(1, int(round(wmm * dpi * ss / 25.4))))
        _draw_strokes(d, strokes, dpi * ss)
        a = np.asarray(im.resize((W, H), Image.BOX), np.float32) / 255
        return a

    rules_cov = np.zeros((H, W), np.float32)
    for y in layout.rules_mm:
        r = int(round(_px(y, dpi))); t = max(1, int(round(0.28 * dpi / 25.4)))
        rules_cov[r:r + t, int(_px(12, dpi)):int(_px(198, dpi))] = 1
    printed = np.maximum(rules_cov, layer(rects=[(layout.box_mm, 0.3)]))
    hw_cov = layer(strokes=layout.strokes)
    code_cov = layer(strokes=layout.code_strokes)
    paper = np.full((H, W, 3), 250, np.float32)
    ink = np.array(PENS[pen], np.float32)
    for cov, col in [(printed, np.array([RULE_GRAY] * 3, np.float32)), (hw_cov, ink), (code_cov, ink)]:
        paper = paper * (1 - cov[..., None]) + col * cov[..., None]
    if skew_deg:
        paper = np.stack([ndi.rotate(paper[..., k], skew_deg, reshape=False, order=1, cval=250) for k in range(3)], 2)
        hw_cov = ndi.rotate(hw_cov, skew_deg, reshape=False, order=1, cval=0)
    yy = np.linspace(-gradient, gradient, H)[:, None, None]
    paper = paper + yy + rng.normal(0, noise, paper.shape)
    img = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8))
    if not bake_overlay:  # PDF üretiminde telif satırı/XXX metin katmanı olarak eklenir (make_pdf)
        return np.asarray(img), hw_cov > 0.5, [], dict(dpi=dpi, pen=pen, skew_deg=skew_deg)
    # vektör katmanı (tarama dışı): telif satırı ve XXX
    d = ImageDraw.Draw(img)
    ft = ImageFont.load_default(size=max(8, int(2.6 * dpi / 25.4)))
    d.text(tuple(_px((12, 288), dpi)), "(c) synthetic footer text", fill=(60, 60, 60), font=ft)
    boxes = [tuple(int(v) for v in d.textbbox(tuple(_px((12, 288), dpi)), "(c) synthetic footer text", font=ft))]  # metin katmanı kutuları
    if layout.xxx_mm:
        x0, y0, x1, y1 = layout.xxx_mm
        d.text(tuple(_px((x0, y0), dpi)), "XXX", fill=(0, 0, 0), font=ImageFont.load_default(size=int(_px(y1 - y0, dpi) * 1.1)))
        bb = d.textbbox(tuple(_px((x0, y0), dpi)), "XXX", font=ImageFont.load_default(size=int(_px(y1 - y0, dpi) * 1.1)))
        boxes.append(tuple(int(v) for v in bb))
    if jpeg_quality:
        import io
        b = io.BytesIO(); img.save(b, "JPEG", quality=jpeg_quality); img = Image.open(b).convert("RGB")
    return np.asarray(img), hw_cov > 0.5, boxes, dict(dpi=dpi, pen=pen, skew_deg=skew_deg)


def make_pdf(path, layout, dpi=150, rotation=0, **render_kw):
    """Sentetik tek sayfalık A4 PDF: tarama görüntüsü + metin katmanı (telif satırı, XXX), FD-LEX yapısını taklit eder."""
    import io
    import pymupdf
    rgb, truth, _, info = render(layout, dpi=dpi, bake_overlay=False, **render_kw)
    buf = io.BytesIO(); Image.fromarray(rgb).save(buf, "PNG")
    doc = pymupdf.open(); page = doc.new_page(width=595.28, height=841.89)
    page.insert_image(page.rect, stream=buf.getvalue())
    pt = 72 / 25.4
    page.insert_text((12 * pt, 290 * pt), "© synthetic footer text", fontsize=7, color=(0.25, 0.25, 0.25))
    if layout.xxx_mm:
        x0, y0, x1, y1 = layout.xxx_mm
        page.insert_text((x0 * pt, y1 * pt), "XXX", fontsize=(y1 - y0) * pt * 1.1, color=(0, 0, 0))
    if rotation:
        page.set_rotation(rotation)
    doc.save(str(path)); doc.close()
    return truth, info
