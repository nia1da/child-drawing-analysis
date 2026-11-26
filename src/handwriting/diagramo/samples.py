"""DiaGraMo örnek görüntü üretimi: 16 örnek (yazma görevleri öncelikli), katılımcı/görev/etiket eşleştirmesiyle.

`python -m src.handwriting.diagramo.samples` → `data/handwriting/diagramo/processed/images/*.png`, `manifests/samples.csv`
ve `processed/images/_contact_sheet.png` (hepsi yerel, git dışı). Bütün veri seti dönüştürülmez.
"""
import numpy as np
import pandas as pd

from .io import ROOT, SVC_DIR
from .labels import usable_participants
from .render import render_svc

LABEL_COLS = ["group", "class", "age", "sex_female", "site_type_ppp", "id_school_ppp", "special_care_type", "special_care_type_dysgraphia",
              "special_care_type_dyslexia", "special_care_type_dyspraxia", "hpsqc_sum", "hls_dictat_sum", "hls_transcript_sum",
              "hls_dictat_c_page_layout", "hls_dictat_d_letter_formation", "bach_dictation_sum"]


def build_table(inv, part):
    """Envanter x kullanılabilir katılımcı etiketleri (yalnız kullanılabilir katılımcıların dosyaları)."""
    lab = part[["id_participant"] + [c for c in LABEL_COLS if c in part]].rename(columns={"id_participant": "pid"})
    for c in ("hls_transcript_sum",):
        lab[c] = pd.to_numeric(lab[c], errors="coerce")
    return inv.merge(lab, on="pid", how="inner")


def select_samples(t, seed=42):
    """Dengeli 16 örnek: 4 yazma görevi x 2 grup (8), HLS uç değerleri (4), eleman görevleri (4). Katılımcılar tekrarlanmaz."""
    rng = np.random.default_rng(seed)
    used, picks = set(), []

    def take(df, why, k=1):
        df = df[~df.pid.isin(used)]
        for i in rng.permutation(len(df))[:k]:
            r = df.iloc[i]; used.add(r.pid); picks.append((r, why))

    for task in ["dictation-3", "dictation-4", "copy-3", "copy-4"]:
        for g in (0.0, 1.0):
            take(t[(t.task == task) & (t.group == g)], f"{task}, group={int(g)}")
    for task, col in [("dictation-4", "hls_dictat_sum"), ("copy-4", "hls_transcript_sum")]:
        d = t[(t.task == task) & t[col].notna() & ~t.pid.isin(used)].sort_values(col)
        for name, row in (("en düşük HLS toplamı", d.iloc[0]), ("en yüksek HLS toplamı", d.iloc[-1])):
            used.add(row.pid); picks.append((row, f"{task}, {name} ({row[col]:g})"))
    for task in ["big-spiral-fast", "saw-fast", "combined-loops-fast", "lower-loops-precise"]:
        take(t[t.task == task], f"{task} (eleman görevi)")
    return picks


def main(out_dir=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    inv = pd.read_csv(ROOT / "manifests" / "svc_inventory.csv", encoding="utf-8")
    t = build_table(inv, usable_participants())
    out = out_dir or ROOT / "processed" / "images"
    out.mkdir(parents=True, exist_ok=True)
    rows, imgs = [], []
    for r, why in select_samples(t):
        res = render_svc(SVC_DIR / r.path, px_per_mm=5.0 if r.kind == "writing" else 6.0)
        name = f"{r.pid}_{r.task}.png"
        res.image.save(out / name, "PNG")
        imgs.append((name, why, res.image))
        rows.append(dict(image=name, why=why, pid=r.pid, task=r.task, kind=r.kind, svc=r.path, px_per_mm=res.px_per_mm, width_px=res.image.width, height_px=res.image.height,
                         n_strokes=res.n_strokes, n_points=res.n_points, **{c: r[c] for c in LABEL_COLS if c in r.index}))
    pd.DataFrame(rows).to_csv(ROOT / "manifests" / "samples.csv", index=False, encoding="utf-8", lineterminator="\n")
    fig, axs = plt.subplots(8, 2, figsize=(16, 22))
    for a, (name, why, im) in zip(axs.ravel(), imgs):
        a.imshow(im, cmap="gray"); a.set_title(f"{name} | {why}", fontsize=7); a.axis("off")
    fig.tight_layout(); fig.savefig(out / "_contact_sheet.png", dpi=70); plt.close(fig)
    return rows


if __name__ == "__main__":
    rows = main()
    for r in rows:
        print(r["image"], "|", r["why"], "|", r["width_px"], "x", r["height_px"], "| vuruş", r["n_strokes"])
