"""Pilot hazırlığı: 20 öğrencilik temsil edici seçim, karşılaştırmalı görselleştirme, otomatik başarısızlık işaretleri.

**İzin geçidi:** `run_pilot` gerçek FD-LEX sayfalarını okur; `paths.require_permission` izin dosyası yoksa durur.
Çıktılar (görseller, özet) yalnız yerel `data/handwriting/fd_lex/pilot/` altına yazılır; kodlar yalnız `pilot_key.csv`'de,
görsellerde ve özet tabloda `pXX` kimliği kullanılır. Pilot, **nitel inceleme** içindir: istatistiksel doğrulama ya da norm değildir.
"""
import numpy as np
import pandas as pd

from .paths import require_permission
from .pdf_io import render_page
from .pipeline import analyze_page
from .splits import student_table
from .viz import plot_result

PILOT_PAGES = ("Ber_MZP1", "Arg_MZP3")  # farklı görev ve zaman; sıra varsayımı doğrulanmış öğrencilerden
COLOR_TYPES = {"DeviceRGB": "renkli", "ICCBased": "renkli", "DeviceGray": "gri/ikili", "Indexed": "gri/ikili"}


def select_pilot(pages, splits, n=20, seed=42, pages_per_student=PILOT_PAGES):
    """Train'den, sınıf x çoğunluk dpi x renk tipi hücrelerine yayılmış n öğrenci; her birinden `pages_per_student` sayfa.

    Dışlanır: 6 sayfa olmayan, tekrar eden sayfası olan (belirsiz eşleme) öğrenciler. Kalem türü meta veride yok: hücreler
    renk tipine göredir, kalem türü pilotta ölçülür (`pen_colored_frac`) ve eksik çeşitlilik raporlanır.
    Döner: (öğrenci tablosu [pilot_id, code, hücre], sayfa tablosu [pilot_id, pdf, seite, ...]).
    """
    p = pages.dropna(subset=["code"]).copy()
    dup = p["img_sha1"].duplicated(keep=False) & p["img_sha1"].notna()
    bad = set(p[dup]["code"]) | set(p.groupby("code").size().loc[lambda s: s != 6].index)
    train = set(splits.loc[splits["bolum"] == "train", "code"])
    p = p[p["code"].isin(train - bad) & p["gorev_zaman_varsayim"].isin(pages_per_student)]
    p["renk_tipi"] = p["cs"].map(COLOR_TYPES).fillna("diğer")
    first_page = p[p["gorev_zaman_varsayim"] == pages_per_student[0]].set_index("code")
    st = student_table(pages).set_index("code").loc[first_page.index]
    st["renk_tipi"] = first_page["renk_tipi"]  # seçilen ilk sayfanın renk tipi (öğrencinin sayfaları karışık olabilir)
    st["hucre"] = st["Klassenstufe"].astype(str) + " | " + st["dpi_major"].astype(str) + " | " + st["renk_tipi"]
    rng = np.random.default_rng(seed)
    cells = {c: list(rng.permutation(g.index.values)) for c, g in st.groupby("hucre")}
    order = sorted(cells, key=lambda c: (len(cells[c]), c))  # küçük (nadir) hücreler önce
    picked = []
    while len(picked) < n and any(cells.values()):
        for c in order:
            if cells[c] and len(picked) < n:
                picked.append((c, cells[c].pop()))
    key = pd.DataFrame(picked, columns=["hucre", "code"])
    key.insert(0, "pilot_id", [f"p{i + 1:02d}" for i in range(len(key))])
    pg = p[p["code"].isin(key["code"])].merge(key[["pilot_id", "code"]], on="code")
    return key, pg.sort_values(["pilot_id", "gorev_zaman_varsayim"]).reset_index(drop=True)


def failure_checks(res, min_lines=3, max_skew=1.0, density_range=(0.002, 0.08)):
    """Bir sayfa sonucunda gözlenebilir başarısızlık işaretleri (kısa kodlar). Eşikler taslaktır; pilotta gözleme göre ayarlanır."""
    q, f, out = res.quality, res.features, []
    if q.get("no_rules"): out.append("cizgi_yok")
    if q.get("rule_grid_irregular"): out.append("cizgi_duzensiz")
    if q.get("rule_spacing_off"): out.append("cizgi_araligi_sapma")
    if q.get("rules_filled"): out.append("cizgi_tamamlandi")
    if not q.get("code_box_found"): out.append("kod_kutusu_bulunamadi")
    if q.get("low_resolution"): out.append("dusuk_cozunurluk")
    if abs(q.get("skew_deg", 0)) > max_skew: out.append("buyuk_egiklik")
    if f.get("lines_measured", 0) < min_lines: out.append("az_satir_olculdu")
    if not np.isfinite(f.get("xheight_mm", np.nan)): out.append("xyukseklik_yok")
    d = f.get("ink_density", np.nan)
    if np.isfinite(d) and not (density_range[0] <= d <= density_range[1]): out.append("murekkep_yogunlugu_uc")
    if f.get("overflow_last_line"): out.append("son_satira_tasma")
    return out


def run_pilot(root=None, n=20, dpi=150, out_dir=None):
    """Pilotu çalıştırır (izin gerekir). Yazılanlar: pilot/pXX_<sayfa>.png, pilot/ozet.csv (kodsuz), pilot/pilot_key.csv (kodlu)."""
    from pathlib import Path
    base = require_permission(root)
    pages = pd.read_csv(base / "manifests" / "pages.csv", encoding="utf-8")
    splits = pd.read_csv(base / "splits.csv", encoding="utf-8")
    key, sel = select_pilot(pages, splits, n=n)
    from .paths import check_data_dir
    out = check_data_dir(out_dir) if out_dir else base / "pilot"  # çıktı da bulut/Drive yoluna yazılamaz
    out.mkdir(parents=True, exist_ok=True)
    key.to_csv(out / "pilot_key.csv", index=False, encoding="utf-8", lineterminator="\n")
    rows = []
    for r in sel.itertuples():
        rgb, boxes = render_page(base / "raw" / r.pdf, r.seite - 1, dpi)
        res = analyze_page(rgb, dpi, boxes)
        tag = f"{r.pilot_id}_{r.gorev_zaman_varsayim}"
        plot_result(res, out / f"{tag}.png", title=f"{tag} | {r.Klassenstufe} | native dpi {r.dpi_eff:.0f} | {r.cs}", original=rgb)
        rows.append(dict(pilot_id=r.pilot_id, sayfa=r.gorev_zaman_varsayim, sinif=r.Klassenstufe, dpi_eff=r.dpi_eff, cs=r.cs,
                         failures=";".join(failure_checks(res)), **{k: v for k, v in res.features.items() if isinstance(v, (int, float, np.floating))},
                         **{f"q_{k}": v for k, v in res.quality.items() if isinstance(v, (int, float, bool, np.floating))}))
    pd.DataFrame(rows).to_csv(out / "ozet.csv", index=False, encoding="utf-8", lineterminator="\n")
    return out
