> **PASİF (2026-11-27):** el yazısı modülü artık DiaGraMo ile sürüyor; FD-LEX Scriptoria ve Malaysian çalışmaları pasif/arşiv durumunda (dosya ve kod silinmedi, kullanılmıyor). Güncel belge: `docs/el_yazisi_diagramo_deney.md`. Karar: `docs/kararlar.md`.

# Pilot protokolü: 20 öğrenci, gerçek sayfalar (izne bağlı)

Tarih: 2026-11-25. **Durum: hazır, çalıştırılmadı.** Gerçek FD-LEX sayfaları yalnız kullanım izni netleştikten sonra okunur. Kod: `src/handwriting/pilot.py`
(`run_pilot`), `pdf_io.py`, `viz.plot_result`. Pilot **nitel inceleme** içindir: istatistiksel doğrulama, norm ya da bölme sonucu değildir; amaç prototipin gerçek sayfada nerede başarısız olduğunu görmektir.

## 1. İzin geçidi (teknik olarak zorunlu)
`paths.require_permission`: `data/handwriting/fd_lex/permission.json` içinde `{"approved": true, "note": "..."}` yoksa `load_page` ve `run_pilot` `PermissionError` verir.
Dosyayı yalnız kullanıcı oluşturur (izin yazısı/e-postası özetiyle). Dosya yokken hiçbir gerçek sayfa okunmaz; FD-LEX yolu Colab'da ve Drive/OneDrive altında zaten reddedilir.

## 2. Seçim (`pilot.select_pilot`)
- **Ölçüt:** dondurulmuş bölmede **yalnız train**; 6 sayfalı ve tekrarsız öğrenciler (28 belirsiz öğrenci dışarıda); sınıf x öğrencinin çoğunluk dpi grubu x renk tipi (renkli / gri-ikili) hücrelerine yayılır, **nadir hücreler önce** alınır (zor durumları görmek için).
- **Sayfalar:** öğrenci başına 2 sayfa: **Ber_MZP1** ve **Arg_MZP3** (farklı görev ve zaman; sıra varsayımı doğrulanmış öğrencilerden). Toplam 40 sayfa.
- **Kimlik:** görsellerde ve özet tabloda yalnız `pXX`; `pilot_key.csv` (kodlu) ayrı dosyada, yerel.
- **Meta veri üzerinde yapılan ön seçim (kodsuz özet):** 20 öğrenci, 8 hücre (sınıf 5: 9, sınıf 9: 11); sayfaların 11'i gri, biri ikili (nadir hücreler önce seçildiği için gri/ikili payı verideki ≈ %7'den büyüktür, bilinçli); dpi_eff 150–400 aralığı. Kalem türü meta veride yok: pilotta `pen_colored_frac` ile ölçülür; eksik çeşitlilik (kurşun, siyah, yeşil, soluk) varsa `select_pilot` seed'i/yedek öğrencilerle tamamlanır.

## 3. Çalıştırma
`run_pilot()` her sayfa için: PDF'ten render (150 dpi) + metin katmanı kutuları → `analyze_page` → karşılaştırmalı panel: **orijinal | önişlenmiş | maskeler | satırlar ve taban çizgileri | ölçümler ve kalite bayrakları**.
Yazılanlar (yerel, git dışı): `data/handwriting/fd_lex/pilot/pXX_<sayfa>.png`, `ozet.csv` (özellikler, kalite, `failures` kodları), `pilot_key.csv`.
Tam çözünürlük karşılaştırması (150 / 200 / 300 dpi) için `render_page` dpi parametresiyle aynı sayfalar yeniden çalıştırılır (duyarlılık: kararlaştırıldı).

## 4. İnceleme listesi (her sayfa için gözle, evet/hayır + not)
1. Basılı çizgiler doğru bulundu mu (sayı, kayma)? Çizgi bandı silinirken harf alt kenarları kayboldu mu?
2. Kod kutusu ve metin katmanı (XXX, telif, kod) doğru maskelendi mi; ilk satıra taşan yazı kesildi mi?
3. El yazısı maskesi: eksik (soluk kurşun, açık mavi) ve fazla (kenar gölgesi, öğretmen notu, başlık) piksel var mı?
4. Üzeri çizilmiş kelimeler ve karalamalar ölçümü ne kadar bozuyor (yoğun bloklar)?
5. Bileşen ↔ harf: bitişik yazıda bileşenler harf mi, kelime mi? Gövde süzgeci makul mü?
6. Satır ataması: inen/yükselen harfler doğru satırda mı; iki satıra yayılan yazı?
7. Taban çizgisi doğruları gözle makul mü (satır başına)?
8. Sayfa kullanımı: kenar boşlukları, devam sayfası, yazı bitişi.
9. Renk/dpi/kalem bazında farklar: hangi koşulda hangi adım başarısız?
10. `failures` kodları (`pilot.failure_checks`) gözlemle uyumlu mu (yanlış alarm / kaçırılan sorun)?

## 5. Sonuç biçimi
- Sayfa x kontrol tablosu (yukarıdaki 10 madde), başarısız ölçümlerin listesi ve **yalnız gözlenen** sorunlara yönelik iyileştirme önerileri (hipotetik iyileştirme yok).
- Özellik başına: "çalıştı / koşullu / başarısız" (gözlem); sayısal doğrulama ve elle işaretleme (100 sayfa) pilotun sonucuna göre kararlaştırılır.
- Pilot çıktıları **commit'e girmez** (pre-commit denetimi görüntü dosyalarını ve `data/handwriting/` yolunu reddeder); belgeye yalnız kodsuz, özet gözlemler yazılır.
