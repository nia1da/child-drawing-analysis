# Rapor taslağı

Hedef rapor (örnek, uydurma değerlerle). Aşamalar: `docs/plan.md`. Görev uyumu ve ayrışmada karşılaştırma grubu
eğitim seviyesi x görev (karar verildi, `docs/plan_gorev_uyumu.md`). Görev uyumu / ayrışma satırları `src.report`'un
gerçek metin çıktısı biçiminde; ayrışma şimdilik ayrı `<öğrenci>_cift.txt` dosyasında, tek rapora birleştirme aşama 7.

```
═══════════════════════════════════════════════════════════════
ÇOCUK ÖN ANALİZ RAPORU                Betimleyicidir, tanı içermez
Kayıt: C-0142 | Sınıf: 3 | Cinsiyet: K | Ziyaret: 2 (08.10.2026)
═══════════════════════════════════════════════════════════════

▌ÇİZİM MODÜLÜ                    Durum: Aktif | Sürüm 0.3
  Normlar: KIDO (n=5.430, Şanlıurfa, 1–8. sınıf)
  Protokol kontrolü: tamam | Kalite kontrolü: iki çizim de geçti

  ── Mutluluk çizimi ──────────────────────────────────────────
  Sahne (otomatik; doğruluk: figür %88, mekân %71, n=200)
    Figür: 2 (1 yetişkin, 1 çocuk) | Mekân: iç mekân, muhtemelen mutfak
    Nesneler: tencere, kaşık, masa, pencere
    Eylem: çocuk figürü tencerede kahverengi bir şeyi karıştırıyor
  Gelişimsel konum: tahmini sınıf 3,4 (gerçek 3) → tipik aralıkta
  Özellikler (3. sınıf, mutluluk normu, yüzdelik):
    Doluluk 58 | Renk sayısı 71 | Renklilik 64 | Koyu ton 22 | Çizgi miktarı 49
  Görev uyumu (mutlu): modelin bu çizimi KIDO'daki "mutlu" görevi çizimlerine benzetme
    derecesi, karşılaştırma grubunun 71. yüzdelik diliminde.
    Karşılaştırma grubu: ilkokul (1–4. sınıf) mutlu normu, n=346 (KIDO val)
  Çağrışım (benzer çizimleri yapan akranların açıklamaları):
    Aileyle birlikte olmak %54 | Yemek/sofra %31 | Oyun %9

  ── Üzüntü çizimi ────────────────────────────────────────────
  Sahne: Figür: 1 (çocuk) | Mekân: belirsiz | Nesneler: yok
  Gelişimsel konum: tahmini sınıf 2,1 (gerçek 3) → tipik aralıkta
  Özellikler (3. sınıf, üzüntü normu, yüzdelik):
    Doluluk 4 ⚠ | Renk sayısı 9 | Renklilik 12 | Koyu ton 61 | Çizgi miktarı 6 ⚠
  Görev uyumu (üzgün): modelin bu çizimi KIDO'daki "üzgün" görevi çizimlerine benzetme
    derecesi, karşılaştırma grubunun 58. yüzdelik diliminde.
    Karşılaştırma grubu: ilkokul (1–4. sınıf) üzgün normu, n=346 (KIDO val)
  Çağrışım: Yalnızlık %38 | Dışlanma %21 | Kayıp %14

  ── İki çizim birlikte ───────────────────────────────────────
  Mutlu–üzgün ayrışma: d = 0,81 (olasılık farkı: üzgün çizim − mutlu çizim),
    karşılaştırma grubunun 66. yüzdelik diliminde.
    Karşılaştırma grubu: ilkokul (1–4. sınıf) normu, n=346 (KIDO val)
    (d < 0 ise: "Model iki çizimi görevlerinin tersi yönünde sıralıyor.")
  Sınırlamalar (her raporda aynı, koşulsuz; tam metin `task_fit.LIMITATIONS`):
   - Görev uyumu, çizimin KIDO'daki aynı görev çizimlerine modelce benzerliğidir; çocuğun duygu
     durumunu göstermez.
   - Üst dilimlerde skorlar birbirine çok yakın (50.–95. dilim arası 0,03–0,06 olasılık farkı);
     küçük yüzdelik farkları anlamlı okunmamalı.
   - Model ilkokul erkek çocukların mutlu çizimlerini daha sık "üzgün" görevine benzetir (320px
     modelde test: %28,3); bu gruptaki çocuklarda düşük görev uyumu ve düşük ayrışma daha sık beklenir.
   - Seyrek ya da az renkli çizimlerde görev uyumu düşebilir; doluluk ve renk sayısıyla birlikte okunmalı.
   - Normlar KIDO (Şanlıurfa, 1–8. sınıf) val bölümünden; başka bir örneklemde dağılım farklı olabilir.
   - Bu ölçümlerde ⚠ verilmez.
  Modelin KIDO test setindeki ayırt ediciliği (rapor dışı kayıt, `docs/olcumler.md`): AUC 0,89 (816 öğrenci).

  ── Açıklama metinleri ───────────────────────────────────────
  Kelime sayısı: 14 / 6 | Duygu kelimesi: 2 / 1
  Yazım hatası yoğunluğu: 3. sınıf normunun 71. yüzdelik dilimi

  ⚠ Tipik aralık (%5–95) dışında kalanlar:
    Üzüntü çiziminde doluluk ve çizgi miktarı belirgin biçimde düşük

  Görüşme önerileri (bulguya bağlı, açık uçlu):
    • "Bana resmini anlatır mısın?"
    • Üzüntü çizimi için: "Bu resimde neler oluyor?"

  İzlem (ziyaret 1 → 2): Mutluluk çiziminde doluluk 31 → 58

▌YAZI MODÜLÜ                     Durum: Planlı, bu ziyarette çalışmadı
▌KONUŞMA MODÜLÜ                  Durum: Planlı, bu ziyarette çalışmadı

▌KLİNİSYEN NOTU
  [serbest metin alanı]
  Bulgu geri bildirimi: [faydalı / faydasız] her satır için
═══════════════════════════════════════════════════════════════
```
