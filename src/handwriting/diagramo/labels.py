"""DiaGraMo etiket/değerlendirme değişkenleri: katalog (kod kitabına dayalı), eksik ve dağılım tablosu, grup ayrımı (AUC).

`python -m src.handwriting.diagramo.labels` → `data/handwriting/diagramo/metadata/label_table.csv` (yerel).
Anlamlar `info/Codebook.xlsx`'ten alınmıştır; kod kitabında **yazmayan** bilgi (kim derecelendirdi, tanı kaynağı) "belirtilmemiş" diye bırakılır.
Kullanılabilir katılımcı: `flag_to_omit_total == 0` (README/temizleme betiği: 276 satır, tekrarlayan ID birleştirilince 275).
"""
import numpy as np
import pandas as pd

from .io import ROOT, read_cognitive

# (değişken, aile, araç, kod kitabından ölçek/kodlama, ilişkili yazı görevi, kim/nasıl (kod kitabında))
CATALOG = [
    ("group", "tanı/grup", "special_care'den türetilmiş ölçüt", "1 = el yazısı güçlüğü; 0 = tipik el yazısı gelişimi", "tümü", "belirtilmemiş"),
    ("special_care_type_dysgraphia", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş (kayıt kaynağı yok)"),
    ("special_care_type_dyslexia", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş"),
    ("special_care_type_dysortographia", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş"),
    ("special_care_type_dyspraxia", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş"),
    ("special_care_type_dyscalculia", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş"),
    ("special_care_type_diagnosis_ongoing", "tanı", "SLD tanısı kaydı", "1/0", "tümü", "belirtilmemiş"),
    ("special_care_type_typical_development", "tanı", "SLD tanısı kaydı", "1 = hiçbir SLD yazılmamış", "tümü", "belirtilmemiş"),
    ("hpsqc_sum", "öz bildirim", "HPSQ-C (10 madde)", "0–40", "genel (görevden bağımsız)", "README özetinde 'self-reported'; madde düzeyinde yanıtlayan belirtilmemiş"),
    ("hpsqc_legibility_sum", "öz bildirim", "HPSQ-C okunabilirlik faktörü (madde 1+2+10)", "0–12", "genel", "aynı"),
    ("hpsqc_performance_time_sum", "öz bildirim", "HPSQ-C performans/süre faktörü (3+4+9)", "0–12", "genel", "aynı"),
    ("hpsqc_wellbeing_sum", "öz bildirim", "HPSQ-C duygusal/fiziksel iyilik faktörü (5+6+7+8)", "0–16", "genel", "aynı"),
    ("hls_dictat_a_ledgibility", "yazı ürünü derecelendirmesi", "HLS madde a: okunabilirlik (veride yazım hatalı sütun adı)", "1–5 (1 = tüm kelimeler okunur)", "dictation", "derecelendiren belirtilmemiş"),
    ("hls_dictat_b_effort", "yazı ürünü derecelendirmesi", "HLS madde b: okuma çabası", "1–5", "dictation", "belirtilmemiş"),
    ("hls_dictat_c_page_layout", "yazı ürünü derecelendirmesi", "HLS madde c: sayfa düzeni", "1–5 (1 = çok iyi düzen)", "dictation", "belirtilmemiş"),
    ("hls_dictat_d_letter_formation", "yazı ürünü derecelendirmesi", "HLS madde d: harf biçimi", "1–5 (1 = iyi biçimli)", "dictation", "belirtilmemiş"),
    ("hls_dictat_e_alterations", "yazı ürünü derecelendirmesi", "HLS madde e: düzeltmeler/ek öğeler", "1–5", "dictation", "belirtilmemiş"),
    ("hls_dictat_sum", "yazı ürünü derecelendirmesi", "HLS toplam", "1–25", "dictation", "belirtilmemiş"),
    ("hls_transcript_a_ledgibility", "yazı ürünü derecelendirmesi", "HLS madde a: okunabilirlik", "1–5", "copy", "belirtilmemiş"),
    ("hls_transcript_c_page_layout", "yazı ürünü derecelendirmesi", "HLS madde c: sayfa düzeni", "1–5", "copy", "belirtilmemiş"),
    ("hls_transcript_d_letter_formation", "yazı ürünü derecelendirmesi", "HLS madde d: harf biçimi", "1–5", "copy", "belirtilmemiş"),
    ("hls_transcript_sum", "yazı ürünü derecelendirmesi", "HLS toplam", "1–25", "copy", "belirtilmemiş"),
    ("bach_dictation_sum", "yazım hatası (ortografi)", "BACH dictation, hata sayısı toplamı (4 değerlendirici)", "0–22", "dictation", "değerlendirici sütunları var (evaluator1–4)"),
    ("dib_transription_sum", "yazım hatası (ortografi)", "DIB transcription, hata toplamı (veride sütun adı yazım hatalı: transription)", "kodlama yok", "copy", "değerlendirici sütunları var"),
    ("element_speed_bs_sum", "grafomotor eleman değerlendirmesi", "büyük spiral, hızlı (7 ölçüt, 0/1)", "0–7", "big-spiral-fast", "belirtilmemiş"),
    ("element_speed_ss_sum", "grafomotor eleman değerlendirmesi", "küçük spiral, hızlı", "0–7", "small-spiral-fast", "belirtilmemiş"),
    ("element_speed_zz_sum", "grafomotor eleman değerlendirmesi", "testere (zig-zag), hızlı", "0–7", "saw-fast", "belirtilmemiş"),
    ("element_speed_ul_sum", "grafomotor eleman değerlendirmesi", "üst döngüler, hızlı", "0–7", "upper-loops-fast", "belirtilmemiş"),
    ("element_speed_ll_sum", "grafomotor eleman değerlendirmesi", "alt döngüler, hızlı", "0–7", "lower-loops-fast", "belirtilmemiş"),
    ("element_speed_r_sum", "grafomotor eleman değerlendirmesi", "gökkuşağı, hızlı", "0–7", "rainbow-fast", "belirtilmemiş"),
    ("element_speed_cl_sum", "grafomotor eleman değerlendirmesi", "birleşik döngüler, hızlı", "0–7", "combined-loops-fast", "belirtilmemiş"),
    ("element_precision_ss_sum", "grafomotor eleman değerlendirmesi", "küçük spiral, hassas", "0–7", "small-spiral-precise", "belirtilmemiş"),
    ("element_precision_ll_sum", "grafomotor eleman değerlendirmesi", "alt döngüler, hassas", "0–7", "lower-loops-precise", "belirtilmemiş"),
    ("element_precision_cl_sum", "grafomotor eleman değerlendirmesi", "birleşik döngüler, hassas", "0–7", "combined-loops-precise", "belirtilmemiş"),
    ("rcft_task001_sum_hs", "görsel-mekânsal", "Rey karmaşık figür, kopya (36 puan)", "0–36", "RCFT-recognition (TSK1: kopya olup olmadığı dosya adından belirsiz)", "belirtilmemiş"),
    ("rcft_task002_sum_hs", "görsel-mekânsal / bellek", "Rey karmaşık figür, anlık hatırlama", "0–36", "RCFT-recall (TSK2)", "belirtilmemiş"),
    ("bach_vda_sum_hs", "görsel-mekânsal", "BACH görsel ayırt etme A", "0–60", "yok (kâğıt/test)", "belirtilmemiş"),
    ("bach_vdb_sum_hs", "görsel-mekânsal", "BACH görsel ayırt etme B", "0–60", "yok", "belirtilmemiş"),
    ("wj_voc_sum_hs", "bilişsel", "WJ-IV sözcük bilgisi", "0–59", "yok", "belirtilmemiş"),
    ("wj_ns_sum_hs", "bilişsel", "WJ-IV sayı serisi", "0–42", "yok", "belirtilmemiş"),
    ("wj_va_sum_hs", "bilişsel", "WJ-IV sözel dikkat", "0–37", "yok", "belirtilmemiş"),
    ("bach_pa_d_sum_hs", "fonolojik", "BACH fonolojik analiz", "0–16", "yok", "belirtilmemiş"),
    ("bach_ps_b_sum_hs", "fonolojik", "BACH fonolojik sentez", "0–16", "yok", "belirtilmemiş"),
    ("bach_pm_a_sum_hs", "fonolojik", "BACH fonem değiştirme", "0–14", "yok", "belirtilmemiş"),
    ("mark_czech_1_numeric", "okul notu", "Çekçe karne notu (yıl sonu)", "1–5", "yok", "belirtilmemiş"),
]


def usable_participants():
    """`flag_to_omit_total == 0`, tekrarlayan ID tek satıra birleştirilmiş (eksik olmayan değer korunur)."""
    c = read_cognitive(True)
    k = c[c.flag_to_omit_total == 0]
    return k.groupby("id_participant", as_index=False).first()


def auc_vs_group(x, g):
    """Mann–Whitney tabanlı AUC (grup 1'in daha yüksek değer alma olasılığı); eksikler atılır."""
    d = pd.DataFrame({"x": x, "g": g}).dropna()
    if d.g.nunique() < 2 or len(d) < 10:
        return np.nan
    r = d.x.rank()
    n1, n0 = (d.g == 1).sum(), (d.g == 0).sum()
    return float((r[d.g == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def label_table(part=None):
    part = usable_participants() if part is None else part
    rows = []
    for var, fam, instr, scale, task, who in CATALOG:
        if var not in part:
            rows.append(dict(degisken=var, aile=fam, arac=instr, olcek=scale, gorev=task, kim=who, durum="veride yok")); continue
        s = pd.to_numeric(part[var], errors="coerce") if not pd.api.types.is_numeric_dtype(part[var]) else part[var]; n = int(s.notna().sum())
        r = dict(degisken=var, aile=fam, arac=instr, olcek=scale, gorev=task, kim=who, n=n, eksik=int(s.isna().sum()))
        if pd.api.types.is_numeric_dtype(s):
            r.update(ort=round(float(s.mean()), 2), sd=round(float(s.std()), 2), min=float(s.min()), max=float(s.max()),
                     auc_group=round(auc_vs_group(s, part["group"]), 3) if var != "group" else np.nan)
            r["dagilim"] = "; ".join(f"{k:g}:{v}" for k, v in s.value_counts().sort_index().items()) if s.nunique() <= 6 else ""
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    t = label_table()
    out = ROOT / "metadata" / "label_table.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(out, index=False, encoding="utf-8", lineterminator="\n")
    pd.set_option("display.width", 250, "display.max_rows", 100, "display.max_colwidth", 38)
    print(t[["degisken", "n", "eksik", "ort", "sd", "min", "max", "auc_group"]].to_string(index=False))
