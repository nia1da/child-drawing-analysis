"""DiaGraMo SVC envanteri: dosya başına istatistik (başlık/satır sayısı, süre, kalem durumu, aralıklar, hash).

`python -m src.handwriting.diagramo.eda` → `data/handwriting/diagramo/manifests/svc_inventory.csv` (yerel).
"""
import hashlib
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd

from .io import ROOT, SVC_DIR, parse_name, read_svc_bytes, svc_files, task_kind


def scan_svc(path):
    data = path.read_bytes()
    r = dict(path=str(path.relative_to(SVC_DIR)).replace("\\", "/"), bytes=len(data), md5=hashlib.md5(data).hexdigest())
    r.update(parse_name(path.name)); r["kind"] = task_kind(r["task"])
    try:
        d = read_svc_bytes(data)
    except Exception as e:  # bozuk dosya
        r["error"] = str(e)[:80]; return r
    n = len(d); t = d.t.values; on = d.pen.values == 1
    dt = np.diff(t) if n > 1 else np.array([0.0])
    r.update(header_n=d.attrs["header_n"], n=n, nan=int(d.isna().any(axis=1).sum()), duration_s=float(t[-1] - t[0]) if n else 0.0,
             pen_on_frac=float(on.mean()) if n else np.nan, pen_values=",".join(map(str, sorted(set(d.pen.unique())))),
             n_strokes=int(((~np.r_[False, on[:-1]]) & on).sum()) if n else 0,
             x_min=d.x.min(), x_max=d.x.max(), y_min=d.y.min(), y_max=d.y.max(), p_min=d.pressure.min(), p_max=d.pressure.max(),
             dt_med=float(np.median(dt)), dt_max=float(dt.max()), nonmono=int((dt < 0).sum()), zero_dt=int((dt == 0).sum()),
             on_zero_pressure=int((on & (d.pressure.values == 0)).sum()), off_nonzero_pressure=int((~on & (d.pressure.values > 0)).sum()))
    return r


def scan_all(workers=4):
    files = svc_files()
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(scan_svc, files, chunksize=8))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = scan_all()
    out = ROOT / "manifests" / "svc_inventory.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8", lineterminator="\n")
    print("dosya:", len(df), "| hata:", int(df.get("error", pd.Series(dtype=object)).notna().sum()), "| yazıldı:", out)
