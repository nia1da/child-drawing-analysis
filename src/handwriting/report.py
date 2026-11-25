"""El yazısı örnek rapor üreticisi (tasarım prototipi): ölçümler, referans karşılaştırması, değişim, güvenilirlik, sınırlamalar.

Betimleyicidir: tanı, risk skoru, "normal/anormal" ya da okunabilirlik yargısı yok. Referans grubu verilmediyse yüzdelik
yazılmaz. Önceki yazıyla değişim, **güvenilir değişim eşiği** (aynı öğrencinin sayfaları arası değişkenlikten, gerçek veriyle
kurulacak) verilmediyse yorumlanmaz; değerler yan yana gösterilir. Referans ve eşikler bu sürümde sentetik örnek içindir.
"""
import numpy as np

from .paths import HW_VERSION

MIN_GROUP = 100   # çizim modülüyle aynı: referans grubu bundan küçükse uç işareti yok, "grup küçük" notu
TAIL = 0.05       # referansın her iki ucunda %5

# ad: (etiket, birim, ne ölçer, ne ifade etmez)
MEASURES = {
    "xheight_mm": ("Yazı boyutu (gövde yüksekliği)", "mm", "Satırlardaki gövde bileşenlerinin ortanca yüksekliği, sayfanın fiziksel ölçeğine göre.",
                   "Harfin gerçek x-yüksekliği değil (bitişik yazıda bileşen birden çok harf olabilir); kalem kalınlığını da içerir; motor beceriyi ölçmez."),
    "xheight_cv_lines": ("Boyut tutarlılığı (satırlar arası)", "CV", "Satırların ortanca yükseklikleri arasındaki değişim katsayısı.",
                         "Satır sayısı azsa kararsız; tutarsızlığın nedenini (dikkat, kâğıt, görev) söylemez."),
    "comp_h_iqr_ratio": ("Bileşen boyutu dağılımı", "IQR/medyan", "Bileşen yüksekliklerinin sayfa içi yayılımı (oransal tutarlılık).",
                         "Bitişik/ayrık yazı biçimine, noktalama ve ince uzantılara duyarlı."),
    "baseline_offset_mm_sd": ("Satır hizası değişkenliği", "mm", "Taban çizgisinin basılı çizgiye uzaklığının satırlar arası standart sapması.",
                              "Çizgiye oturmanın düzenliliği; yazının kâğıt çizgisine uyumu ve öğretim alışkanlığı etkiler."),
    "baseline_wobble_mm_median": ("Taban çizgisi dalgalanması (satır içi)", "mm", "Bir satırda gövde bileşenlerinin alt kenarlarının doğru etrafındaki sağlam sapması.",
                                  "Statik izdir; kalem hareketinin titremesini doğrudan ölçmez."),
    "baseline_slope_deg_median": ("Taban çizgisi eğimi", "derece", "Satırların çizgiye göre ortanca eğimi (+: sağa aşağı).",
                                  "Sayfa eğikliği düzeltildikten sonra; harf eğimi (italik) değil."),
    "left_margin_mm": ("Sol kenar boşluğu", "mm", "Sayfa kenarından yazının başladığı yere uzaklık.", "Sayfa organizasyonu; tarama kırpması ve yönerge etkiler."),
    "used_frac": ("Kullanılan satır oranı", "oran", "Yazı içeren satır / sayfadaki basılı çizgi.", "Yazı uzunluğuna bağlıdır; tek başına kötü/iyi demek değil."),
    "mean_line_fill_frac": ("Satır doluluğu", "oran", "Yazılı satırların yazı alanı genişliğinin ne kadarını kapladığı.", "Satır sonu, paragraf ve bitiş satırlarını da içerir."),
}

LIMITATIONS = [
    "Ölçümler tek bir statik görüntünün biçimsel özellikleridir; motor beceriyi, yazma hızını ya da hareket kalitesini doğrudan ölçmez.",
    "Akademik el yazısı ölçeklerinin (ör. BHK) puanını üretmez ve onlarla eşdeğer değildir.",
    "Referans grubu, bu çalışmanın örneklemidir (sınıf, görev ve ölçüm zamanına göre); popülasyon ya da klinik norm değildir.",
    "Referansın uç bölgesi bir değerlendirme değil, ölçümün ve görüntünün kontrol edilmesi için işarettir; tanı ya da gelişimsel yorum içermez.",
    "Tarama çözünürlüğü, kalem ve kâğıt koşulları ölçümleri etkileyebilir; güvenilirlik bölümü bu sayfaya özgü uyarıları listeler.",
]


def percentile_rank(value, ref):
    """Ortalama sıra yüzdeliği (eşit değerlerde orta nokta)."""
    ref = np.asarray(ref, float); ref = ref[np.isfinite(ref)]
    return float(100 * (np.sum(ref < value) + 0.5 * np.sum(ref == value)) / len(ref))


def reliability(res):
    """Sayfaya özgü ölçüm güvenilirliği: ('yüksek'|'orta'|'düşük', nedenler). Eşikler taslaktır (pilotta ayarlanacak)."""
    q, f, low, mid = res.quality, res.features, [], []
    if q.get("no_rules"): low.append("basılı çizgiler bulunamadı")
    if q.get("low_resolution"): low.append("çözünürlük 150 dpi altında")
    if f.get("lines_measured", 0) < 3: low.append("ölçülebilen satır sayısı 3'ten az")
    if q.get("rule_grid_irregular") or q.get("rule_spacing_off"): mid.append("çizgi aralığı beklenenden sapıyor")
    if q.get("rules_filled"): mid.append("eksik çizgi ızgarayla tamamlandı")
    if not q.get("code_box_found"): mid.append("kod kutusu bulunamadı")
    if q.get("pen_colored_frac", 1) < 0.5: mid.append("kalem rengi ayırt edilemedi (gri/soluk kalem olabilir)")
    if abs(q.get("skew_deg", 0)) > 1.0: mid.append("büyük tarama eğikliği düzeltildi")
    if f.get("overflow_last_line"): mid.append("yazı son satıra taşmış (metin devam ediyor olabilir)")
    return ("düşük" if low else "orta" if mid else "yüksek"), low + mid


def build_report(res, reference=None, previous=None, change_threshold=None, context=None, min_group=MIN_GROUP):
    """reference: ölçüm adlarına göre sütunlu DataFrame (akran sayfaları); previous: önceki sayfanın `features` sözlüğü;
    change_threshold: {ölçüm: güvenilir değişim eşiği} (yoksa değişim yorumlanmaz); context: {'grup': ..., 'gorev': ..., ...}."""
    rep = dict(surum=HW_VERSION, baglam=context or {}, olcumler=[], degisim=[], kalite={}, sinirlamalar=LIMITATIONS)
    n_ref = 0 if reference is None else len(reference)
    rep["referans"] = dict(n=n_ref, yeterli=n_ref >= min_group,
                           not_=None if reference is None else ("grup küçük: uç işareti verilmez" if n_ref < min_group else None))
    for key, (label, unit, measures, not_measures) in MEASURES.items():
        v = res.features.get(key)
        if v is None or not np.isfinite(v):
            rep["olcumler"].append(dict(ad=key, etiket=label, birim=unit, deger=None, ne_olcer=measures, ne_ifade_etmez=not_measures)); continue
        row = dict(ad=key, etiket=label, birim=unit, deger=round(float(v), 3), ne_olcer=measures, ne_ifade_etmez=not_measures, yuzdelik=None, uc=False)
        if reference is not None and key in reference and n_ref:
            row["yuzdelik"] = round(percentile_rank(v, reference[key].values), 1)
            row["uc"] = bool(n_ref >= min_group and (row["yuzdelik"] < 100 * TAIL or row["yuzdelik"] > 100 * (1 - TAIL)))
        rep["olcumler"].append(row)
    if previous is not None:
        for key, (label, unit, *_) in MEASURES.items():
            a, b = previous.get(key), res.features.get(key)
            if a is None or b is None or not (np.isfinite(a) and np.isfinite(b)):
                continue
            thr = (change_threshold or {}).get(key)
            row = dict(ad=key, etiket=label, birim=unit, onceki=round(float(a), 3), simdiki=round(float(b), 3), fark=round(float(b - a), 3), esik=thr)
            row["yorum"] = "eşik tanımsız: fark yorumlanmaz" if thr is None else ("güvenilir değişim eşiğini aşıyor" if abs(b - a) > thr else "eşik içinde")
            rep["degisim"].append(row)
    level, reasons = reliability(res)
    rep["kalite"] = dict(guvenilirlik=level, nedenler=reasons, bayraklar={k: v for k, v in res.quality.items() if isinstance(v, (int, float, bool, np.floating))})
    return rep


def render_text(rep):
    """Uzman için okunur metin (Markdown)."""
    L = [f"# El yazısı geometrik ölçüm raporu ({rep['surum']})", ""]
    ctx = rep["baglam"]
    if ctx:
        L.append("**Bağlam:** " + " · ".join(f"{k}: {v}" for k, v in ctx.items()))
    r = rep["referans"]
    L.append(f"**Referans grubu:** {r['n']} sayfa" + (f" ({r['not_']})" if r["not_"] else "") if r["n"] else "**Referans grubu:** verilmedi, yüzdelik yok")
    L += ["", "## Ölçümler", "", "| Ölçüm | Değer | Referans yüzdeliği | Not |", "|---|---|---|---|"]
    for m in rep["olcumler"]:
        val = "ölçülemedi" if m["deger"] is None else f"{m['deger']:.2f} {m['birim']}"
        yz = "-" if m.get("yuzdelik") is None else ("> referansın en büyüğü" if m["yuzdelik"] >= 99.5 else "< referansın en küçüğü" if m["yuzdelik"] <= 0.5 else f"{m['yuzdelik']:.0f}.")
        note = "uç bölge: ölçümü ve görüntüyü kontrol edin" if m.get("uc") else ""
        L.append(f"| {m['etiket']} | {val} | {yz} | {note} |")
    L += ["", "Her ölçümün ne ölçtüğü ve **yorumlanırken dikkat edilecek sınırı**:"] + [f"- **{m['etiket']}**: {m['ne_olcer']} *Sınır:* {m['ne_ifade_etmez']}" for m in rep["olcumler"]]
    if rep["degisim"]:
        L += ["", "## Önceki yazı örneğine göre değişim", "", "| Ölçüm | Önceki | Şimdiki | Fark | Yorum |", "|---|---|---|---|---|"]
        L += [f"| {d['etiket']} | {d['onceki']:.2f} | {d['simdiki']:.2f} | {d['fark']:+.2f} | {d['yorum']} |" for d in rep["degisim"]]
    k = rep["kalite"]
    L += ["", f"## Ölçüm güvenilirliği: {k['guvenilirlik']}", ""] + ([f"- {x}" for x in k["nedenler"]] or ["- Sayfaya özgü uyarı yok."])
    L += ["", "## Sınırlamalar", ""] + [f"- {s}" for s in rep["sinirlamalar"]]
    return "\n".join(L) + "\n"
