"""DiaGraMo yazma kayıtları: kayıt tablosu (hedefler, kalite bayrakları), tüm kayıtların PNG'ye dönüşümü, okul bazlı bölme.

`python -m src.handwriting.diagramo.dataset` → `processed/images/{tablet,crop}/*.png`, `manifests/images.csv`, `manifests/splits.csv` (hepsi yerel).

Hedefler (kod kitabı + veri doğrulaması): her yazma ailesi için HLS'nin üç bağımsız maddesi (1–5 tam sayı): sayfa düzeni (c), harf biçimi (d), düzeltmeler (e).
Dikte kayıtları `hls_dictat_*`, kopya kayıtları `hls_transcript_*` sütunlarıyla eşleşir. HLS toplamı, okunabilirlik (a) ve çaba (b) hedef olarak kullanılmaz.
Koordinat birimi README'de belirtilmemiş: görüntü ölçeği "piksel / tablet birimi"dir (muhtemelen mm; doğrulanmadı), özellikler tb (tablet birimi) ya da oran olarak yazılır.
"""
import hashlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from .io import RAW, ROOT, SVC_DIR, read_svc
from .labels import usable_participants
from .render import TABLET_MM, render_strokes, split_strokes

PPU = 4.0          # piksel / tablet birimi (tablet tuvali 1393 x 813 px)
LINE_PX = 3
TARGETS = {"dictation": {"layout": "hls_dictat_c_page_layout", "letter": "hls_dictat_d_letter_formation", "alter": "hls_dictat_e_alterations"},
           "copy": {"layout": "hls_transcript_c_page_layout", "letter": "hls_transcript_d_letter_formation", "alter": "hls_transcript_e_alterations"}}
META = ["class", "age", "sex_female", "id_school_ppp", "id_city", "site_type_ppp", "group", "special_care_type_dysgraphia", "special_care_type_dyslexia"]
EXCLUDE_LABELS = {"not_complete"}  # yazı tamamlanmamış: metnin tamamı yok; diğer işaretliler korunur, bayrak olarak taşınır


def records():
    """Kullanılabilir (omit=0) çocukların yazma kayıtları + hedefler + bayraklar. Hedefi eksik olan satırlar `usable=False`."""
    inv = pd.read_csv(ROOT / "manifests" / "svc_inventory.csv", encoding="utf-8")
    w = inv[inv.kind == "writing"].copy()
    w["family"] = w.task.str.replace(r"-\d$", "", regex=True)
    w["grade_ver"] = w.task.str.extract(r"-(\d)$")[0].astype(int)
    part = usable_participants()
    keep = ["id_participant"] + META + sorted({c for d in TARGETS.values() for c in d.values()})
    w = w.merge(part[keep], left_on="pid", right_on="id_participant", how="inner")
    for k in ("layout", "letter", "alter"):
        w[k] = np.nan
        for fam, cols in TARGETS.items():
            m = w.family == fam
            w.loc[m, k] = pd.to_numeric(w.loc[m, cols[k]], errors="coerce")
    w = w.drop(columns=[c for d in TARGETS.values() for c in d.values()] + ["id_participant"])
    dist = pd.read_excel(RAW / "info" / "distorted_data.xlsx")
    dist["fname"] = dist.Filename
    labels = dist.groupby("fname").Label.agg(lambda s: ",".join(sorted(set(s)))).to_dict()
    w["distort_label"] = w.path.str.split("/").str[-1].map(labels).fillna("")
    w["extra_content"] = w.distort_label.str.contains("extra_content")
    w["flagged"] = w.distort_label != ""
    w["has_targets"] = w[["layout", "letter", "alter"]].notna().all(axis=1)
    w["usable"] = w.has_targets & ~w.distort_label.apply(lambda s: bool(EXCLUDE_LABELS & set(s.split(","))))
    w["image"] = w.pid + "_" + w.task + ".png"
    return w.reset_index(drop=True)


def coord_reference(strokes):
    """Koordinatlardan doğrudan statik niceliklerin (hız/basınç/sıra değil) hesabı: görüntü özelliklerini doğrulamak için."""
    allp = np.vstack(strokes)
    L = float(sum(np.hypot(*np.diff(s, axis=0).T).sum() for s in strokes if len(s) > 1))
    return dict(coord_x0=float(allp[:, 0].min()), coord_x1=float(allp[:, 0].max()), coord_y0=float(TABLET_MM[1] - allp[:, 1].max()),
                coord_y1=float(TABLET_MM[1] - allp[:, 1].min()), coord_path_len=L, coord_ink_pts=int(len(allp)))


def _render_one(args):
    path, name, out = args
    st = split_strokes(read_svc(SVC_DIR / path))
    row = dict(image=name, **coord_reference(st))
    for mode, kw in (("tablet", dict(canvas="tablet")), ("crop", dict(canvas="bbox", margin_mm=8.0))):
        r = render_strokes(st, px_per_mm=PPU, line_px=LINE_PX, **kw)
        d = out / mode; d.mkdir(parents=True, exist_ok=True)
        r.image.save(d / name, "PNG")
        row[f"{mode}_w"], row[f"{mode}_h"] = r.image.size
    row["n_strokes"] = len(st)
    return row


def render_all(workers=4, only_usable=True):
    rec = records()
    todo = rec[rec.usable] if only_usable else rec
    out = ROOT / "processed" / "images"
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(_render_one, [(r.path, r.image, out) for r in todo.itertuples()], chunksize=4))
    m = todo.merge(pd.DataFrame(rows), on="image")
    m["ppu"] = PPU; m["line_px"] = LINE_PX
    m.to_csv(ROOT / "manifests" / "images.csv", index=False, encoding="utf-8", lineterminator="\n")
    return m


def make_school_split(children, seed=42, fractions=(0.70, 0.15, 0.15), n_candidates=20000):
    """Okul bazlı train/val/test: aynı okulun çocukları tek bölümde. Yalnız meta veriye (çocuk sayısı, sınıf, grup) bakar; hedeflere bakılmaz.
    Aday atamalar rastgele üretilir, hedef oran, sınıf ve grup dengesi için en düşük sapma puanlı aday seçilir (seed sabit, tekrarlanabilir).
    `children`: sütunlar pid, school, class, group."""
    rng = np.random.default_rng(seed)
    sch = children.groupby("school").agg(n=("pid", "size"), c4=("class", lambda s: (s == 4).sum()), hd=("group", "sum")).reset_index()
    tot = sch[["n", "c4", "hd"]].sum().values.astype(float)
    target = np.array(fractions)
    best, best_score = None, np.inf
    for _ in range(n_candidates):
        a = rng.choice(3, size=len(sch), p=target)
        if len(set(a)) < 3:
            continue
        score = 0.0
        for k in range(3):
            v = sch.loc[a == k, ["n", "c4", "hd"]].sum().values
            share = v[0] / tot[0]
            score += 4 * abs(share - target[k]) + abs(v[1] / max(v[0], 1) - tot[1] / tot[0]) * 0.5 + abs(v[2] / max(v[0], 1) - tot[2] / tot[0]) * 0.5
        if score < best_score:
            best, best_score = a, score
    part = dict(zip(sch.school, np.array(["train", "val", "test"])[best]))
    out = children.assign(bolum=children.school.map(part))
    return out, best_score


def split_children(rec):
    """Hedefi olan en az bir yazma kaydı bulunan çocuklar → okul bazlı bölme tablosu (pid, school, class, group, bolum)."""
    ch = rec[rec.usable].drop_duplicates("pid")[["pid", "id_school_ppp", "class", "group"]].rename(columns={"id_school_ppp": "school"})
    ch["school"] = ch.school.fillna("school_na")
    return make_school_split(ch)


def write_split(rec):
    sp, score = split_children(rec)
    path = ROOT / "manifests" / "splits.csv"
    sp.sort_values("pid").to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
    return sp, hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    rec = records()
    print("kayıt:", len(rec), "| hedefi tam:", int(rec.has_targets.sum()), "| kullanılabilir:", int(rec.usable.sum()), "| extra_content:", int(rec.extra_content.sum()))
    sp, sha = write_split(rec)
    print("bölme (çocuk):", sp.bolum.value_counts().to_dict(), "| okul:", sp.groupby("bolum").school.nunique().to_dict(), "| sha256", sha)
    m = render_all()
    print("render edilen:", len(m))
