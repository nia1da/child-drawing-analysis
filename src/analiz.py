"""Kayıtlı tahminler (tahminler/{deney}_{bolum}.csv) üzerinde analizler.

- Güven bandı: model "emin" mi "belirsiz" mi? Eşik val'de belirlenir, {cikti}/{deney}_esik.json'a kaydedilir.
- Hata yönü: mutlu çizimi "üzgün" ya da üzgünü "mutlu" sanma oranları, alt grup bazında.
- Deney karşılaştırma: aynı ayarın seed'lerini birlikte özetler.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from .config import YOLLAR
from .istatistik import GRUPLAR, _macro_f1, kayitli_tahminler


def guven(sonuc):
    # 0 = kararsız (olasılık 0.5), 1 = tam emin
    return (sonuc.olasilik_uzgun - 0.5).abs() * 2


def _gruplara_bol(sonuc):
    for ad, filtre in GRUPLAR:
        t = sonuc
        for sutun, deger in filtre.items():
            t = t[t[sutun] == deger]
        yield ad, t


def esik_belirle(val, hedef=0.90):
    """'Emin' denen tahminlerin doğruluğu en az hedef olacak şekilde en düşük güven eşiği.

    En düşük eşik seçilir, böylece hedefi tutturan en çok sayıda tahmin "emin" sayılır.
    """
    g = guven(val).to_numpy()
    dogru = (val.gercek == val.tahmin).to_numpy()
    sira = np.argsort(-g)  # en emin olandan başla
    kumulatif = np.cumsum(dogru[sira]) / np.arange(1, len(g) + 1)
    uygun = np.nonzero(kumulatif >= hedef)[0]
    if len(uygun) == 0:
        raise ValueError(f"Hiçbir eşikte doğruluk {hedef} olmuyor.")
    k = uygun.max()
    # Aynı güven değerine sahip tahminler bölünmesin: eşik, k. tahminin güveni
    esik = float(g[sira][k])
    emin = g >= esik
    return {"hedef": hedef, "esik": round(esik, 4),
            "val_kapsama": round(float(emin.mean()), 4), "val_emin_dogruluk": round(float(dogru[emin].mean()), 4)}


def esik_kaydet(deney, hedef=0.90, cikti=YOLLAR["cikti"]):
    """Val tahminlerinden eşiği belirler ve modelin yanına kaydeder (val tahminleri önceden üretilmiş olmalı)."""
    sonuc = esik_belirle(kayitli_tahminler(deney, "val", cikti), hedef)
    sonuc = {"deney": deney, **sonuc, "tarih": datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%Y-%m-%d %H:%M")}
    with open(f"{cikti}/{deney}_esik.json", "w") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    return sonuc


def esik_yukle(deney, cikti=YOLLAR["cikti"]):
    with open(f"{cikti}/{deney}_esik.json") as f:
        return json.load(f)["esik"]


def guven_bandi(sonuc, esik):
    """Alt grup bazında: tahminlerin ne kadarı 'emin', emin ve belirsiz tahminlerin doğruluğu."""
    satirlar = []
    for ad, t in _gruplara_bol(sonuc):
        emin = guven(t) >= esik
        dogru = t.gercek == t.tahmin
        satirlar.append({"grup": ad, "n": len(t), "emin_orani": round(emin.mean(), 3),
                         "emin_dogruluk": round(dogru[emin].mean(), 3),
                         "belirsiz_dogruluk": round(dogru[~emin].mean(), 3) if (~emin).any() else np.nan})
    return pd.DataFrame(satirlar)


def hata_yonu(sonuc):
    """Alt grup bazında: mutlu çizimlerin yüzde kaçı 'üzgün', üzgünlerin yüzde kaçı 'mutlu' tahmin edildi."""
    satirlar = []
    for ad, t in _gruplara_bol(sonuc):
        mutlu, uzgun = t[t.gercek == 0], t[t.gercek == 1]
        satirlar.append({"grup": ad, "mutlu_uzgun_yuzde": round(100 * (mutlu.tahmin == 1).mean(), 1),
                         "uzgun_mutlu_yuzde": round(100 * (uzgun.tahmin == 0).mean(), 1)})
    return pd.DataFrame(satirlar)


def _f1(t):
    hucre = (t.gercek * 2 + t.tahmin).value_counts().reindex(range(4), fill_value=0).to_numpy(float)
    return float(_macro_f1(hucre))


def karsilastir(deneyler, bolum="val", cikti=YOLLAR["cikti"]):
    """Her deney için genel ve alt grup F1'i, ilkokul erkek hata yönü; sonra ayar (seed hariç) bazında ortalama.

    deneyler: {deney_adı: ayar_etiketi}, örn. {"..._s1": "temel", "..._s1_aug-renk": "renk"}
    """
    satirlar = []
    for deney, ayar in deneyler.items():
        t = kayitli_tahminler(deney, bolum, cikti)
        f1 = {ad: _f1(g) for ad, g in _gruplara_bol(t)}
        pm = t[(t.egitim == "Primary") & (t.cinsiyet == "Male") & (t.gercek == 0)]
        satirlar.append({"ayar": ayar, "deney": deney, "f1_genel": f1["Genel"],
                         "f1_ilkokul_erkek": f1["Primary Male"], "f1_ilkokul_kiz": f1["Primary Female"],
                         "kiz_erkek_farki": f1["Female"] - f1["Male"],
                         "ilkokul_erkek_mutlu_uzgun_yuzde": 100 * (pm.tahmin == 1).mean()})
    tek = pd.DataFrame(satirlar).round(4)
    sayisal = tek.columns.drop(["ayar", "deney"])
    ozet = tek.groupby("ayar")[list(sayisal)].agg(["mean", "std"]).round(4)
    ozet.insert(0, ("n_seed", ""), tek.groupby("ayar").size())
    return tek, ozet
