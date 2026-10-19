"""Maske kontrol sayfası: seçilmiş çizimlerin orijinali ve maskesi yan yana, gözle kontrol için.

Her sınıf düzeyinden (1-8) 3 çizim; toplamda yarısı renkli, yarısı karakalem. Karakalem: maskedeki
renkli (S > COLOR_S) piksel oranı %5'in altında. Çıktı {output}/maske_kontrol/: her çizim için bir PNG
(orijinal | maske | maske kırmızıyla orijinalin üstünde), 4 özet sayfa (6'şar çizim) ve index.html.

Kullanım: python -m src.measurements.mask_check
"""
import os

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from ..config import PATHS
from ..data import grade_from_filename as grade, image_path, load_metadata
from .mask import COLOR_S, drawing_mask, load_drawing, to_hsv

PENCIL_COLOR_RATIO = 0.05  # maskede bu orandan az renkli (S > COLOR_S) piksel varsa karakalem


def color_ratio(hsv, mask):
    return float((hsv[..., 1][mask] > COLOR_S).mean()) if mask.any() else 0.0


def kind_of(r):
    hsv = to_hsv(load_drawing(image_path(r)))
    return "karakalem" if color_ratio(hsv, drawing_mask(hsv)) < PENCIL_COLOR_RATIO else "renkli"


def pick(df, per_grade=3, seed=0, pool=200):
    """Her sınıf düzeyinden per_grade çizim, toplamda yarısı karakalem.

    Karakalem çizim nadir ve bazı sınıflarda havuzda hiç çıkmayabilir: karakalem kotası, karakalem adayı olan
    sınıflara sırayla dağıtılır (sınıf başına en çok per_grade - 1, en az bir renkli kalsın); kalan yerler renkli.
    """
    rng = np.random.default_rng(seed)
    kinds = {}
    for g in range(1, 9):
        cands = df[df.dosya.map(grade) == g].sample(pool, random_state=int(rng.integers(1e9)))
        kinds[g] = {"renkli": [], "karakalem": []}
        for _, r in cands.iterrows():
            kinds[g][kind_of(r)].append(r)
    quota, pencil = 8 * per_grade // 2, {g: 0 for g in kinds}
    while quota > 0:
        given = 0
        for g in kinds:
            if quota > 0 and pencil[g] < min(per_grade - 1, len(kinds[g]["karakalem"])):
                pencil[g] += 1; quota -= 1; given += 1
        if given == 0:
            break  # havuzda yeterli karakalem yok
    chosen = []
    for g in kinds:
        picks = [("karakalem", r) for r in kinds[g]["karakalem"][:pencil[g]]]
        picks += [("renkli", r) for r in kinds[g]["renkli"][:per_grade - pencil[g]]]
        for kind, r in picks:
            img = load_drawing(image_path(r))
            chosen.append({"row": r, "img": img, "mask": drawing_mask(to_hsv(img)), "tur": kind, "sinif": g})
    return chosen


def panel(item, font):
    img, mask = item["img"], item["mask"]
    w, h = img.size
    mask_img = Image.fromarray(np.where(mask, 0, 255).astype(np.uint8)).convert("RGB")
    overlay = np.asarray(img).copy()
    overlay[mask] = [255, 0, 0]
    out = Image.new("RGB", (w * 3, h + 24), "white")
    for i, im in enumerate([img, mask_img, Image.fromarray(overlay)]):
        out.paste(im, (i * w, 24))
    r = item["row"]
    text = f"{r.dosya} | {item['sinif']}. sınıf | {item['tur']} | {r.duygu} | doluluk {mask.mean():.3f}"
    ImageDraw.Draw(out).text((6, 4), text, fill="black", font=font)
    return out


def build(output_dir=PATHS["output"], seed=0):
    folder = f"{output_dir}/maske_kontrol"
    os.makedirs(folder, exist_ok=True)
    font = ImageFont.load_default(size=16)
    items = pick(load_metadata(), seed=seed)
    panels, rows = [], []
    for k, item in enumerate(items, 1):
        p = panel(item, font)
        name = f"{k:02d}_{item['row'].dosya.replace('.jpg', '')}.png"
        p.save(f"{folder}/{name}")
        panels.append(p)
        rows.append({"no": k, "dosya": item["row"].dosya, "sinif": item["sinif"], "tur": item["tur"],
                     "duygu": item["row"].duygu, "bolum": item["row"].bolum,
                     "doluluk": round(float(item["mask"].mean()), 4), "png": name})
    for s in range(0, len(panels), 6):  # 6 çizimlik özet sayfalar
        group = panels[s:s + 6]
        sheet = Image.new("RGB", (group[0].width, sum(p.height for p in group)), "white")
        y = 0
        for p in group:
            sheet.paste(p, (0, y)); y += p.height
        sheet.save(f"{folder}/ozet_{s // 6 + 1}.png")
    table = pd.DataFrame(rows)
    table.to_csv(f"{folder}/liste.csv", index=False)
    html = ["<!doctype html><meta charset='utf-8'><title>Maske kontrol</title>",
            "<style>body{font-family:sans-serif;margin:16px}img{max-width:100%;border:1px solid #ccc}</style>",
            "<h1>Maske kontrol</h1><p>Her satır: orijinal | maske | maske kırmızıyla orijinalin üstünde.</p>"]
    for r in rows:
        html.append(f"<h3>{r['no']}. {r['dosya']} — {r['sinif']}. sınıf, {r['tur']}, doluluk {r['doluluk']}</h3>"
                    f"<img src='{r['png']}' loading='lazy'>")
    with open(f"{folder}/index.html", "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    return folder, table


if __name__ == "__main__":
    folder, table = build()
    print(table.to_string(index=False))
    print(f"\nKaydedildi: {folder}")
