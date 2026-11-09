# Plan: metin rapordaki "Detay" yerine "Çizgi miktarı" (aşama 2'nin kalanı)

Durum: onaylandı (2026-11-10; denetleyici önerileri işlendi). Küçük çizim ⚠ kuralı aynı kalır. Karar önceden verildi (`docs/kararlar.md`,
2026-10-21); bu plan uygulamanın kapsamını ve kontrollerini belirler.

## Amaç ve gerekçe
Metin rapordaki beşinci satır "Detay (kenar yoğunluğu)", kenar piksellerinin **çizim piksellerine** oranı. Bu oran
"çok ayrıntı" kadar "ince çizgi / az boyama" da demek: boyama oranıyla −0,67, ortalama çizgi kalınlığıyla −0,75
ilişkili (`docs/olcumler.md`, sınırlama 10). Klinisyen "Detay" adından çizim zenginliği okur, ölçülen şey çizgi
inceliği. Yerine **Çizgi miktarı** = toplam çizgi uzunluğu (`cizgi_uzunlugu`: maskenin iskeleti, piksel) gösterilir.
Kalınlıktan bağımsız bir ölçü olması beklenir; aşağıdaki veri bunu doğruluyor.

## Veri (train normları, 7842 çizim, ölçüm sürümü 3; yeni hesap gerekmedi)
- `cizgi_uzunlugu` JSON'da ve `olcum_normlari.csv`'de zaten var (min 40, ortanca 3896, max 43752; sıfır yok).
  **Ölçüm tanımı, maske ve normlar değişmez → `MEASUREMENT_VERSION` artmaz, normlar yeniden hesaplanmaz.**
  `model_normlari.csv` (val, model skorları) bundan etkilenmez.
- **Ölçek:** 10860 görüntünün tamamı tarandı: 10848'i 512 x 362, 12'si 512 x 364–367 (yükseklik en fazla 5 piksel
  fazla, %0,1). Piksel sayıları KIDO içinde karşılaştırılabilir; fark ihmal edilebilir. Mutlak piksel sayısı ölçeğe
  duyarlıdır (doluluk oransal, çizgi miktarı değil): normlar yalnız bu boyuttaki görüntüler için geçerli.
- Spearman (train): çizgi miktarı ↔ doluluk 0,59; ↔ çizgi kalınlığı −0,20; ↔ boyama −0,23; ↔ renklilik (çizim)
  −0,21; ↔ koyu ton 0,05; ↔ renk sayısı 0,25. Eski "Detay" için ölçüt |0,7| idi: çizgi miktarı hiçbirinde yaklaşmıyor
  (en yüksek 0,59, dolulukla). Aynı doluluk bandında (0,08–0,12, n=650) çizgi miktarı 5.–95. dilim 967–4435: dolulukta
  olmayan bilgi taşıyor.
- ⚠ oranı (sınıf x görev grubunda %5–95 dışı, rapordaki kuralla): genel %9,8; doluluk > 0,1 çizimlerde %8,2; doluluk
  < 0,03 (küçük çizim) %79,6 (doluluk için %100). Küçük çizimde çizgi miktarının düşük çıkması çizimin küçük olmasının
  sonucu; bkz. "Küçük çizim".

## Değişiklikler
1. `src/report.py`: `TEXT_MEASURES`'ta beşinci eleman `kenar_yogunlugu_cizim: "Detay (kenar yoğunluğu)"` yerine
   `cizgi_uzunlugu: "Çizgi miktarı"` (aynı sıra). `kenar_yogunlugu_cizim` JSON'da, normlarda ve
   `SMALL_DRAWING_MEASURES`/`SMALL_DRAWING_CANDIDATES`'ta kalır (kural değişmez, tablo yeniden hesaplanmaz). Değer
   biçimi: `cizgi_uzunlugu` zaten `INTEGER_MEASURES`'ta, tamsayı gösterilir.
2. **Tanım ve metin rapor:** `docs/olcumler.md` tanımı "iskelet uzunluğu, piksel; boyanmış alanlar iskelette kısa
   sayılır, boyama miktarını ölçmez; yoğun boyalı ama az çizgili çizim düşük çıkar" diye yazılır. JSON'daki ad
   ("Toplam çizgi uzunluğu") ile metin rapordaki ad ("Çizgi miktarı") belgede eşlenir. Metin rapora (⚠ açıklama
   notunun yanına) tek cümlelik, koşulsuz bir not: "Çizgi miktarı, çizgilerin toplam uzunluğudur; boyanmış alanlar
   çizgi sayılmaz." Gürültü (JPEG halesi, seyrek tarama) iki yönde uzunluk ekler; aynı maskeyle çıkarılan normlar aynı
   yönde etkilendiği için kabul sınıfında, tek cümle olarak yazılır.
3. **Küçük çizim:** `cizgi_uzunlugu` mutlak bir ölçüm; kuralın tasarımı gereği (`metrics.SMALL_DRAWING_CANDIDATES`
   yorumu: mutlak ve büyüklüğü betimleyen ölçümler aday değil) küçük çizimde ⚠ verilir ve "*" almaz, tıpkı doluluk
   gibi. Yani küçük bir çizimde hem doluluk hem çizgi miktarı ⚠ alır (iki satır aynı olguyu söylüyor, birbirinden
   bağımsız bulgu değil). Küme tablosu ve eşik değişmez. Bu çakışma `docs/olcumler.md`'ye sınırlama olarak yazılır;
   küçük çizimde metin rapor ⚠ açıklama notuna "doluluk ve çizgi miktarı aynı olguyu yansıtır" cümlesi eklenir
   (yalnız doluluk < `MIN_FILL` iken).
4. Testler (`tests/test_measurements.py`): metin raporun satır adları ve sırası (Çizgi miktarı, Detay yok);
   JSON'da `kenar_yogunlugu_cizim` ve `cizgi_uzunlugu` duruyor; eski "Detay" adının kalmaması.
   Somut: `test_measurements.py` satır 344'teki ad listesi ve 383–387'deki "Detay" beklentisi "Çizgi miktarı"na;
   küçük çizimde "Çizgi miktarı" satırı "*" ile değil ⚠ ile biter (doluluk gibi); `synthetic_norms`'a gerçekçi
   `cizgi_uzunlugu` dağılımı (≈ 2000–6000 tamsayı; şimdi `uniform(0,1)`, test çizimi yanlış nedenle "ust" ⚠ alırdı)
   eklenir ve "alt" / "ust" ⚠ ayrı ayrı sınanır; `expected` sözlüğüne `cizgi_uzunlugu`; 5 haneli değerin
   (max 43752) satır hizasını bozmadığı; küçük çizim notundaki ek cümle.
5. Belgeler: `docs/olcumler.md` (satır 20 ölçüm tablosundaki "Detay ve karmaşıklık" anlamı, 76 ve 82 tanımlar,
   147–148 metin rapor listesi, 189–196 Spearman tablosu yeni beş ölçüm + boyama için [değerler normlardan hesaplandı,
   doğrulayıcı yeniden hesaplar], sınırlama 8/10 "kenar yoğunluğu artık yalnız JSON'da", yeni sınırlama 11: iskelet
   boyalı alanları kısa sayar, doluluk ile 0,59, küçük çizimde doluluk ile çakışan ⚠, normlar yalnız 512 x ~362
   görüntüler için geçerli; başka çözünürlükte uzunluk yeniden ölçeklenmeli ya da norm yeniden çıkarılmalı);
   `docs/rapor_taslagi.md` satır 63 "doluluk ve çizgi miktarı belirgin biçimde düşük" cümlesi boyalı çizimi yanlış
   betimlemesin diye gözden geçirilir; `notebooks/colab.ipynb`'de "Detay" geçiyor mu kontrol edilir;
   `docs/kararlar.md` ("Uygulanmadı" → uygulandı, tarih; "metin rapor biçimi 2026-11-10'dan itibaren değişti, JSON
   aynı; eski kayıtlı raporlar ve `docs/dogrulama/` belgeleri 'Detay' ile kalır, değişmez");
   `docs/durum.md` ("ölçüm sürümü artarsa" maddesi "artmadı" diye kapanır), `docs/plan.md` (aşama 2 bitti); **CLAUDE.md** (Kod yapısı `report.py` satırı: TEXT_MEASURES listesi;
   "Sürüm 3" paragrafı: "detay"→"çizgi miktarı", |0,7| ölçütüne ek) — CLAUDE.md değişikliği kullanıcı onayına dahil.
6. Kapsam dışı: yeni ölçüm, maske değişikliği, norm yeniden hesabı, eski kayıtlı raporlar (Drive `raporlar/`'daki
   mevcut dosyalar "Detay" ile kalır, yeniden üretilmez), `kenar_yogunlugu*` ölçümlerinin silinmesi.

## Doğrulama
- `unittest discover` (şu an 85 test) yeşil.
- Gerçek train çiziminden rapor: `PY -m src.report data/kido/Dataset/Images/Emotion/train/Sadness/110-3H-1081-F-S.jpg`;
  satır, yüzdelik ve ⚠ biçimi, Drive `raporlar/`; eski ve yeni rapor aynı JSON ölçümlerini içeriyor (yalnız metin
  satırı değişti).
- Yüzdelik doğruluğu: bir çizim için `olcum_normlari.csv`'den elle hesaplanan yüzdelik raporla aynı.
- Anlam kontrolü (görsel): doluluğu benzer (0,08–0,12) iken çizgi miktarı düşük ve yüksek olan, aynı sınıf ve
  görevden **train** çizimleri (3 + 3) dogrulayici tarafından açılıp bakılır; ayrıca en az bir yoğun boyalı (yüksek
  doluluk, kısa iskelet) ve bir seyrek taramalı / dokulu çizim seçilir. "Çok çizgi / az çizgi" betimlemesi görünenle
  uyuşuyor mu, boyalı ve taramalı çizimlerde yanıltıcı mı, yüzdeliğin görünenle çelişip çelişmediği kaydedilir.
  Val/test görüntüsü kullanılmaz.
- Dogrulayici raporu `docs/dogrulama/<tarih>-cizgi-miktari.md`; küçük bir iş olduğu için aşama sonu denetimi
  aşama 2 kapanışında bir kez.

## Eklenmedi (not)
- Rapora görüntü boyutu uyarısı (kod): bu iş için şart değil; KIDO dışı veri gelirse ayrı iş (olcumler.md'de not var).

## Açık nokta (kullanıcıya)
- Küçük çizimde doluluk ve çizgi miktarı birlikte ⚠ alır (öneri: kural olduğu gibi kalsın; bir satırı "*" yapmak
  çizimin büyüklüğünü betimleyen bir ölçümü susturur). Alternatif: çizgi miktarını da "*" kümesine almak, ama
  kuralla sabitlenen küme değişir ve tablo yeniden hesaplanır.
