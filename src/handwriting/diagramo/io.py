"""DiaGraMo dosya okuma: SVC koordinat kayıtları, görev adı çözümleme, katılımcı tablosu.

SVC biçimi (README ve `convert_SVC_to_JSON.py`): ilk satır örnek sayısı, sonra her satırda
`x y zaman pen_status azimuth altitude(tilt) pressure` (boşlukla ayrık). x, y milimetre, zaman saniye (EDA'da doğrulanır),
pen_status 1 = kalem yüzeyde, 0 = havada. Havadaki noktalar da kaydedilir (kalem yüzeye yakınken).
"""
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / "data" / "handwriting" / "diagramo"
RAW = ROOT / "raw"
SVC_DIR = RAW / "data" / "raw_data" / "handwriting_data" / "data_SVC"
COG_DIR = RAW / "data" / "processed_data" / "cognitive_test_data"
COLUMNS = ["x", "y", "t", "pen", "azimuth", "altitude", "pressure"]

NAME_RE = re.compile(r"^(?P<pid>[A-Za-z0-9]+)_TSK(?P<no>\d+)\(TA\)-(?P<task>.+)_(?P<ver>\d+)\.(?P<ext>svc|json)$")


def parse_name(fname):
    """`BR10301_TSK3(TA)-dictation-3_1.svc` → dict(pid, tsk_no, task, ver, ext). Tanınmayan ad: ValueError."""
    m = NAME_RE.match(Path(fname).name)
    if not m:
        raise ValueError(f"tanınmayan dosya adı: {fname}")
    d = m.groupdict()
    d["no"] = int(d["no"]); d["ver"] = int(d["ver"])
    return d


def task_kind(task):
    """writing (dictation/copy: cümle yazma), element (spiral, döngü, testere vb.), rcft (karmaşık figür)."""
    if task.startswith(("dictation", "copy")):
        return "writing"
    if task.startswith("RCFT"):
        return "rcft"
    return "element"


def read_svc_bytes(data: bytes):
    """SVC içeriğinden (bytes) DataFrame. Başlıktaki örnek sayısı ile satır sayısı uyuşmazsa `attrs['header_n']` karşılaştırılabilir."""
    head, _, body = data.partition(b"\n")
    df = pd.read_csv(io.BytesIO(body), sep=r"\s+", header=None, names=COLUMNS, engine="c")
    df.attrs["header_n"] = int(head.strip())
    return df


def read_svc(path):
    return read_svc_bytes(Path(path).read_bytes())


def read_cognitive(cleaned=True):
    """Bilişsel/etiket tablosu (noktalı virgül ayraçlı, ondalık virgül). `cleaned`: 289 satır + omit bayrakları (satır silinmemiş)."""
    f = COG_DIR / "cognitiveTestCSV2data_cleaned.csv" if cleaned else RAW / "data" / "raw_data" / "cognitive_test_data" / "cognitiveTestCSV2data.csv"
    return pd.read_csv(f, sep=";", decimal=",", encoding="utf-8", low_memory=False)


def svc_files():
    return sorted(SVC_DIR.glob("*/*.svc"))
