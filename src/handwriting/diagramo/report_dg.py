"""DiaGraMo üzerinde geliştirilmiş **deneysel** uzman raporu örnekleri (geometrik ölçümler ile model tahmini ayrı bölümlerde).

`python -m src.handwriting.diagramo.report_dg` → `data/handwriting/diagramo/reports/` (yerel: gerçek çocuk yazısı görüntüleri içerir, git dışı).
Tahminler gerçek uzman değerlendirmesi değildir; gerçek fotoğraflarda bağımsız doğrulama yapılmamıştır. Test kümesi bu modülde yeniden metrik için kullanılmaz
(örnek seçimi yalnız model tahminlerine göre, gerçek etiketlere bakılmadan).
"""
import json

import numpy as np
import pandas as pd

from . import analysis as A
from . import models as M
from .explain import annotate, occlusion_contributions
from .io import ROOT

TAIL = 0.05
MIN_GROUP = 100
ITEM = {"layout": ("Sayfa düzeni", "HLS maddesi c; 1 = çok iyi düzen … 5 = çok kötü düzen (kod kitabı)"),
        "letter": ("Harf biçimi", "HLS maddesi d; 1 = iyi biçimli harfler … 5 = kötü biçimli harfler (kod kitabı)"),
        "alter": ("Düzeltmeler / karalamalar", "HLS maddesi e; 1 = ek öğe yok … 5 = çoğu kelimede ek öğe (kod kitabı)")}
MEASURES = [("n_lines", "Satır sayısı", "adet", "Bölütlenen yazı satırı sayısı (kural çizgisiz, yaklaşık)"),
            ("xh_tb", "Yazı boyutu (x-yüksekliği)", "tb", "Satırların yoğun mürekkep bandının yüksekliği (ortanca)"),
            ("xh_over_pitch", "Yazı boyutu / satır aralığı", "oran", "Yazının satır aralığına göre büyüklüğü"),
            ("xh_cv_lines", "Boyut değişkenliği (satırlar arası)", "CV", "Satır başına x-yüksekliğinin değişim katsayısı"),
            ("comp_h_iqr_ratio", "Bileşen boyutu dağılımı", "IQR/medyan", "Bağlı bileşen yüksekliklerinin yayılımı"),
            ("slope_abs_med_deg", "Satır eğimi (mutlak)", "derece", "Satır taban çizgisi eğiminin ortanca mutlak değeri"),
            ("wobble_over_xh", "Taban çizgisi dalgalanması / x-yüksekliği", "oran", "Satır içi taban kenarı sapması, boyuta göre"),
            ("pitch_cv", "Satır aralığı düzenliliği", "CV", "Ardışık satır tabanları arası mesafenin değişimi"),
            ("left_edge_sd_over_xh", "Sol hizalama değişkenliği", "oran", "Satır başlangıçlarının dağılımı, x-yüksekliğine göre"),
            ("gap_med_over_xh", "Bileşenler arası boşluk (ortanca)", "oran", "Bileşenler arası yatay boşluk; bitişik yazıda kelime/harf ayrımı güvenilir değil"),
            ("junction_density", "Kesişim/düğüm yoğunluğu", "oran", "İskelet düğüm pikselleri / iskelet uzunluğu (çizgi kesişimleri, örtüşmeler)"),
            ("thick_frac", "Kalın (üst üste binmiş) mürekkep payı", "oran", "Karalama/üzeri çizme ile ilişkili görsel özellik"),
            ("valley_ink_frac", "Satırlar arası bölgedeki mürekkep", "oran", "Komşu satırlara taşan/örtüşen yazı"),
            ("skel_len_tb", "Toplam çizgi uzunluğu (iskelet)", "tb", "Statik görüntüdeki mürekkep yolu uzunluğu"),
            ("rbbox_area_frac", "Yazı alanı / tablet alanı", "oran", "Yazının kapladığı alan (tablet konumu biliniyorsa)")]

LIMITS = [
    "Bu rapor, DiaGraMo (Çekçe, 8–12 yaş, tablet) üzerinde geliştirilmiş **deneysel** bir modelin çıktısıdır; **gerçek el yazısı fotoğraflarında bağımsız olarak doğrulanmamıştır**.",
    "Model tahminleri **uzman değerlendirmesi değildir**; HLS puanlarını taklit etmeye çalışır. Tanı, okunabilirlik yargısı ya da risk skoru içermez.",
    "Eğitim görüntüleri kalem koordinatlarından üretilmiştir (kâğıt çizgisi, kalem ve gürültü yok, çizgi kalınlığı sabit); gerçek fotoğraf ile alan farkı beklenir.",
    "Ölçü birimi 'tb' (tablet birimi): README birim belirtmiyor (muhtemelen mm, doğrulanmadı); mutlak boyutlar yerine oranlar tercih edilmelidir.",
    "Geometrik ölçümler görüntüden hesaplanır (koordinatlarla bazı nicelikler için doğrulandı); tahminler ise bu ölçümlerden öğrenilmiş bir modelin çıktısıdır: ikisi ayrı değerlendirilmelidir.",
    "Referans yüzdelikleri DiaGraMo eğitim bölümünden (okul bazlı bölme) hesaplanır; popülasyon ya da klinik norm değildir.",
    "Küçük örnek (≈ 190 çocuk eğitimde) ve geniş belirsizlik: test kümesinde QWK ≈ 0,4 (güven aralığı geniş); tek tek yazılar için tahmin hatalı olabilir.",
    "'Katkıda bulunan özellikler' modelin özelliğe duyarlılığını gösterir, nedensel bir açıklama değildir.",
    "İşaretli bölgeler uzmanın bakacağı yerlerdir; hata ya da bozukluk işareti değildir.",
]


def _pct(v, ref):
    ref = np.asarray(ref, float); ref = ref[np.isfinite(ref)]
    return float(100 * (np.sum(ref < v) + 0.5 * np.sum(ref == v)) / len(ref))


def fit_all(d, feats, dev_table_path=None):
    dev_table_path = dev_table_path or ROOT / "metadata" / "model_a_development.csv"
    chosen = M.choose(pd.read_csv(dev_table_path))
    cfgs = {c.name: c for c in M.CONFIGS}
    dev = d[d.bolum.isin(["train", "val"])]
    models = {}
    for t, name in chosen.items():
        a = dev[dev[t].notna()]
        f, cols = M.fit_model(cfgs[name], a, t, feats)
        oof = M.oof_predictions(cfgs[name], a, t, feats)
        res = np.abs(a[t].values - oof)
        models[t] = dict(predict=f, cols=cols, config=name, q80=float(np.percentile(res, 80)), train=a, cv=M.metrics(a[t].values, oof))
    return models


def pick_examples(d, models, n=3):
    """Test kümesinden örnekler: model tahminlerinin toplamına göre en düşük, ortada ve en yüksek (gerçek etiketlere bakılmaz)."""
    te = d[(d.bolum == "test") & d.usable & ~d.flagged].copy()
    te["pred_sum"] = sum(models[t]["predict"](te) for t in A.TARGETS)
    te = te.sort_values("pred_sum")
    idx = [0, len(te) // 2, len(te) - 1][:n]
    return te.iloc[idx]


def build_report(row, d, models, feats, out_dir, ppu=4.0):
    fam = row.family
    ref = d[(d.bolum == "train") & (d.family == fam)]
    rep = dict(goruntu=row.image, aile=fam, referans_n=int(len(ref)), referans_yeterli=bool(len(ref) >= MIN_GROUP), olcumler=[], tahminler=[], uyarilar=[])
    for col, label, unit, meaning in MEASURES:
        v = row.get(col)
        if v is None or not np.isfinite(v):
            continue
        pct = _pct(v, ref[col]) if len(ref) >= MIN_GROUP else None
        rep["olcumler"].append(dict(ad=col, etiket=label, deger=round(float(v), 3), birim=unit, aciklama=meaning, yuzdelik=None if pct is None else round(pct, 1),
                                    uc=bool(pct is not None and (pct < 100 * TAIL or pct > 100 * (1 - TAIL)))))
    one = pd.DataFrame([row])
    for t in A.TARGETS:
        m = models[t]
        c = float(m["predict"](one)[0])
        contrib = occlusion_contributions(m["predict"], one, m["train"], m["cols"]) if m["cols"] else []
        rep["tahminler"].append(dict(madde=t, ad=ITEM[t][0], olcek=ITEM[t][1], tahmin_surekli=round(c, 2), tahmin_sinif=int(np.clip(np.rint(c), 1, 5)),
                                     aralik80=[round(max(1.0, c - m["q80"]), 2), round(min(5.0, c + m["q80"]), 2)], model=m["config"],
                                     gelistirme_cv=dict(mae=round(m["cv"]["mae"], 3), qwk=round(m["cv"]["qwk"], 3), spearman=round(m["cv"]["spearman"], 3)),
                                     katkilar=[dict(ozellik=k, katki=round(v, 3), deger=round(x, 3), egitim_medyani=round(md, 3)) for k, v, x, md in contrib]))
    if row.n_lines < 3: rep["uyarilar"].append("Satır bölütleme güvenilirliği düşük (3'ten az satır bulundu)")
    if not (9.0 <= row.pitch_tb <= 13.5): rep["uyarilar"].append(f"Tahmini satır aralığı ({row.pitch_tb:.1f} tb) beklenen aralığın (≈ 11 tb) dışında: satır bölütleme hatalı olabilir")
    if row.stray_ink_frac > 0.02: rep["uyarilar"].append("Satır dışında mürekkep var (ek içerik/lekeler olabilir)")
    if row.thick_frac > 0.02: rep["uyarilar"].append("Belirgin kalın/üst üste binmiş mürekkep bölgeleri var (yoğun karalama olabilir)")
    out = out_dir / f"{row.image[:-4]}_bolgeler.png"
    reg = annotate(ROOT / "processed" / "images" / "tablet" / row.image, out, ppu)
    rep["bolgeler"] = dict(gorsel=out.name, dalgali_satir=int(sum(l["flag"] for l in reg["lines"])), satir=len(reg["lines"]), kalin_bolge=len(reg["blobs"]), uzun_bilesen=len(reg["tall"]), satir_disi=len(reg["stray"]))
    return rep


def render_text(rep):
    L = [f"# El yazısı raporu (DiaGraMo üzerinde geliştirilmiş deneysel prototip)", "",
         f"Görüntü: `{rep['goruntu']}` ({'dikte' if rep['aile'] == 'dictation' else 'kopya'} görevi) · Referans: DiaGraMo eğitim bölümü, aynı görev, {rep['referans_n']} yazı"
         + ("" if rep["referans_yeterli"] else " (grup küçük: yüzdelik yok)"), "",
         "## A. Geometrik ölçümler (görüntüden hesaplanan)", "", "| Ölçüm | Değer | Referans yüzdeliği | Not |", "|---|---|---|---|"]
    for m in rep["olcumler"]:
        L.append(f"| {m['etiket']} | {m['deger']} {m['birim']} | {'-' if m['yuzdelik'] is None else str(round(m['yuzdelik'])) + '.'} | {'uç bölge: ölçümü ve görüntüyü kontrol edin' if m['uc'] else ''} |")
    L += ["", "Ölçümlerin anlamı: " + "; ".join(f"**{m['etiket']}**: {m['aciklama']}" for m in rep["olcumler"][:6]) + " …", "",
          "## B. Deneysel model tahmini (**uzman değerlendirmesi değildir**)", "",
          "Aşağıdaki tahminler, DiaGraMo'da uzman HLS puanlarıyla eğitilmiş bir modelin çıktısıdır; gerçek fotoğraflarda doğrulanmamıştır. Geometrik ölçümlerden (A) ayrı değerlendirin.", "",
          "| HLS maddesi | Tahmin (1–5) | Sürekli | %80 aralık | Geliştirme CV (QWK / MAE) |", "|---|---|---|---|---|"]
    for p in rep["tahminler"]:
        L.append(f"| {p['ad']} | {p['tahmin_sinif']} | {p['tahmin_surekli']} | {p['aralik80'][0]}–{p['aralik80'][1]} | {p['gelistirme_cv']['qwk']} / {p['gelistirme_cv']['mae']} |")
    L += ["", "Ölçek yönü: " + "; ".join(f"{p['ad']}: {p['olcek']}" for p in rep["tahminler"]), "", "### Tahmine katkıda bulunan özellikler (model duyarlılığı)", ""]
    for p in rep["tahminler"]:
        L.append(f"- **{p['ad']}**: " + ("; ".join(f"`{k['ozellik']}` {k['deger']} (eğitim medyanı {k['egitim_medyani']}; tahmini {'yükseltiyor' if k['katki'] > 0 else 'düşürüyor'}, {abs(k['katki']):.2f})" for k in p["katkilar"]) or "özellik seçilmedi"))
    b = rep["bolgeler"]
    L += ["", "## C. Görüntü üzerinde incelenebilecek bölgeler", "",
          f"Görsel: `{b['gorsel']}` (yerel). Yeşil/turuncu çizgiler satır taban çizgileri (turuncu: taban dalgalanması ≥ %10 x-yüksekliği; {b['dalgali_satir']}/{b['satir']} satır), kırmızı kutular kalın/üst üste binmiş bölgeler ({b['kalin_bolge']}), "
          f"mor kutular çok uzun bileşenler ({b['uzun_bilesen']}), mavi kutular satır dışı mürekkep ({b['satir_disi']}). Bunlar uzmanın bakacağı yerlerdir, hata işareti değildir.", "",
          "## D. Ölçüm güvenilirliği ve sınırlamalar", ""]
    L += [f"- ⚠ {u}" for u in rep["uyarilar"]] or ["- Bu yazıya özgü bölütleme uyarısı yok."]
    L += [f"- {s}" for s in LIMITS]
    return "\n".join(L) + "\n"


def main(n=3):
    d = A.load_table(); feats = A.feature_columns(d)
    models = fit_all(d, feats)
    out = ROOT / "reports"; out.mkdir(parents=True, exist_ok=True)
    reps = []
    for _, row in pick_examples(d, models, n).iterrows():
        rep = build_report(row, d, models, feats, out)
        (out / f"{row.image[:-4]}_rapor.md").write_text(render_text(rep), encoding="utf-8", newline="\n")
        (out / f"{row.image[:-4]}_rapor.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float), encoding="utf-8", newline="\n")
        reps.append(rep)
    return reps


if __name__ == "__main__":
    for r in main():
        print(r["goruntu"], [(p["madde"], p["tahmin_sinif"], p["tahmin_surekli"]) for p in r["tahminler"]])
