# El yazısı veri seti analizi (EDA)

Tarih: 2026-11-25. Notebook: `notebooks/handwriting_eda.ipynb` (çıktılar içinde). Veri: `data/handwriting/raw/` (git'e girmez).
Bu çalışma yalnızca okur ve ölçer: veri değiştirilmedi, augmentation uygulanmadı, model eğitilmedi; Çizim modülüne dokunulmadı.
Ara tablo: `data/handwriting/eda_ozellikler.csv` (görüntü başına özellikler, git'e girmez).

Kaynak etiketleri: **[doğrulandı]** dosyalardan ölçüldü. **[yayında]** veri seti sayfası / veri makalesinde yazıyor, dosyalardan doğrulanamadı.
**[bilinmiyor]** ne dosyada ne bulduğum yayında var.

## Özet

- 249 JPEG, iki sınıf: Low Potential Dysgraphia (LPD) 135, Potential Dysgraphia (PD) 114 **[doğrulandı]**.
- Görüntüler **işlenmiş**: ikili (siyah-beyaz), yazı beyaz / arka plan siyah, yazı bölgesine sıkı kırpılmış **[doğrulandı]**.
- **Metadata yok**: öğrenci ID, yaş, sınıf, cinsiyet, yazma görevi dosyalarda bulunmuyor **[doğrulandı]**. Tek etiket klasör adı.
- Yayında 83 katılımcı yazıyor **[yayında]**; hangi görüntünün hangi çocuğa ait olduğu **[bilinmiyor]**. Bu yüzden öğrenci bazında
  bölme ve sızıntı denetimi **bu veriyle yapılamıyor**.
- Birebir ya da yakın kopya yok **[doğrulandı]**. En benzer çiftler aynı cümlenin farklı el yazılarıdır.
- Ölçümler: satır eğimi ve harf boyutu (satır aralığına oranla) uygulanabilir; kelime aralığı sınırlı; satır aralığı ve sayfa düzeni
  çocuğu değil kâğıdı/kırpmayı ölçüyor, uygulanamaz. Hiçbirinin doğruluğu için referans etiket yok.

## 1. Klasör yapısı ve formatlar [doğrulandı]

```
data/handwriting/raw/
  Low Potential Dysgraphia/   LPD (1).jpg ... LPD (135).jpg
  Potential Dysgraphia/       PD (1).jpg  ... PD (114).jpg
```
- Toplam 249 dosya, hepsi `.jpg`; README, CSV ya da başka metadata dosyası yok. Alt klasör derinliği 2.
- Hepsi JPEG, mod `L` (8 bit gri). DPI, EXIF, ICC profili, JPEG yorum alanı: hiçbirinde yok.
- Dosya numaraları sınıf içinde 1..N ardışık, eksik yok. Numaranın öğrenciyle ilişkisi bilinmiyor.

## 2. Sınıf dağılımı ve çözünürlük [doğrulandı]

| Sınıf | Adet | Oran | Medyan genişlik x yükseklik (px) | Medyan dosya boyutu |
|---|---|---|---|---|
| LPD | 135 | %54,2 | 1157 x 159 | 41,8 KB |
| PD | 114 | %45,8 | 1231 x 177,5 | 62,6 KB |

- Genişlik 396–1434, yükseklik 55–448 px; en/boy oranı 3,0–14,2 (medyan 6,9). 249 görüntüde 246 farklı (w,h) çifti: **sabit boyut yok**.
- Sınıf dengesi makul (1,18:1), ama toplam örnek çok az (249).
- Sınıflar arasında görüntü özellikleri farklı: medyan beyaz piksel oranı LPD 0,074, PD 0,107; dosya boyutu PD'de ~1,5 kat.
  Bunun yazı kalitesinden mi, çizgi kalınlığı / ikilileştirme / kırpma farkından mı geldiği **[bilinmiyor]** (bkz. bölüm 8).

## 3. Metadata [doğrulandı, aksi belirtilmedikçe]

| Alan | Durum |
|---|---|
| Öğrenci ID | Dosyada yok. Yayında 83 katılımcı **[yayında]**; eşleme **[bilinmiyor]** |
| Yaş | Yok **[bilinmiyor]** |
| Sınıf düzeyi (grade) | Yok **[bilinmiyor]** |
| Cinsiyet, okul | Yok **[bilinmiyor]** |
| Yazma görevi | Dosyada yok. Görsel kontrolde Malayca cümle kopyalama görüldü (yayında da öyle yazıyor **[yayında]**) |
| Etiket | Klasör adı; iki uzman (Malaysian Dyslexia Association) değerlendirmiş **[yayında]**; ölçüt ve uzman uyumu **[bilinmiyor]** |

Yayında ayrıca katılımcıların ilkokul çocukları ve dislekşi derneğinde müdahale gören çocuklar olduğu yazıyor **[yayında]**;
hangi görüntünün hangi gruptan geldiği **[bilinmiyor]**.

**Sonuç:** KIDO'daki gibi yaş/sınıf normu, cinsiyet ya da eğitim düzeyi alt grup analizi bu veriyle mümkün değil. Çizim modülündeki "sınıf düzeyine göre
yüzdelik" yaklaşımı El Yazısı için bu veriyle kurulamaz.

**Görev yapısı (görsel kontrol, OCR değil, doğrulanmış etiket değil):** en az üç farklı cümle görüldü: "Baju itu baru dibeli oleh emak." (tek satır),
"Burung itu berada di dalam sangkar. Sangkar baru itu milik bapa." (iki satır), "Saya suka bermain basikal pada waktu lapang..." (üç–dört satır).
Görüntü başına cümle etiketi yok. Kâğıttaki çizgi sayısı (1–5) cümleyi ayırmıyor (5 çizgili kâğıtta 2–4 satırlık örnekler var; sayılar 56/99/57/26/11),
yani görev değişkeni otomatik çıkarılamadı. Görev sınıflar arasında dengeli mi **[bilinmiyor]**: çizgi sayısı dağılımı sınıflar arasında farklı (4–5 çizgili
görüntüler PD'de 32, LPD'de 5), bu bir görev ya da kâğıt formu farkına işaret edebilir ama nedeni doğrulanmadı.

## 4. Orijinal mi, kırpılmış mı, işlenmiş mi? [doğrulandı]

- **İkili görüntü:** görüntü başına 15–20 farklı gri değer (JPEG gürültüsü); piksellerin %99,999'u <8 ya da >247.
- **Ters çevrilmiş:** yazı beyaz, arka plan siyah (beyaz piksel oranı medyan %8,3). Yayında da "ikili format, ön plan/arka plan değiştirilmiş" yazıyor **[yayında]**.
- **Sıkı kırpılmış:** yazının kenara uzaklığı: sol medyan 4 px, sağ 0, üst 10, alt 11 (maks 28). 9 görüntünün kenarında %5'ten fazla beyaz piksel var (kırpma yazıya/çizgiye değiyor).
- **Çizgili kâğıt korunmuş:** 249 görüntünün hepsinde en az bir uzun yatay çizgi bulundu (beyaz, kalınlık ~2–3 px). Çizgi açısı: medyan −0,03°, %5–%95 −0,24/+0,23°, hiçbirinde |açı| > 1°.
  Çizgilerin bu kadar yatay olması görüntülerin hizalanmış/düzeltilmiş olabileceğini düşündürür, ama işlem hattı **[bilinmiyor]**.
- Sonuç: bunlar ham tarama/fotoğraf değil; ham görüntüden mevcut ikilileştirme, kırpma ve (olası) hizalama geri alınamaz. Fiziksel ölçek (mm) yok; yeniden boyutlandırma yapılıp yapılmadığı **[bilinmiyor]**.

## 5. Örnekler

Her sınıftan rastgele 10 örnek (seed 42) notebook bölüm 6'dadır. Gözlemler (örneklem küçük, sayısal iddia değil): LPD örneklerinde yazı genelde düzenli,
çizgi üzerinde, harf ve kelime aralıkları belirgin; PD örneklerinde harf boyutu ve aralığı düzensiz, çizgiyi aşan ya da çizgiyle birleşen harfler, silinmiş/üstü çizilmiş
kısımlar, bazı satırlarda kelimelerin bitişik yazılması görüldü. Ancak ince çizgili / soluk görüntüler her iki sınıfta da var (örn. LPD (6), LPD (9)); stroke kalınlığı ve ikilileştirme kalitesi görüntüler arasında çok değişiyor.

## 6. Tekrar ve sızıntı

- **Birebir kopya:** SHA-256 ile 0 çakışma [doğrulandı].
- **Yakın kopya:** 32x256'ya küçültülmüş normalize korelasyonla en yakın komşu korelasyonu medyan 0,40, %95 0,59, maks 0,66. En benzer 6 çift gözle incelendi:
  hepsi aynı cümlenin **farklı el yazılarıyla** yazılmış hâli (aynı görüntü değil). Düşük eşiğin üstünde kopya kanıtı bulunamadı. Not: bu yöntem aynı çocuğun farklı cümlelerini
  yakalayamaz (içerik farklı).
- Aynı boyutlu 3 görüntü çifti (1237x167, 1250x165, 1269x189) piksel düzeyinde özdeş değil (ortalama fark 29–47 gri düzeyi); tesadüf.
- Yazı karşılaştırması (writer identification) yapılmadığı için **aynı çocuğun birden çok görüntüsü** olup olmadığı veriden gösterilemedi.

**Sızıntı riski (öğrenci düzeyinde): doğrulanamıyor, ama yüksek olabilir.**
- Yayında 83 katılımcı, 249 görüntü yazıyor **[yayında]** → katılımcı başına ortalama 3 görüntü. Kimlik dosyalarda olmadığı için görüntü bazlı bir train/val/test bölmesi aynı çocuğu birden çok bölüme
  koyabilir. Katılımcı başına tam 3 görüntü varsayımıyla, rastgele %80/%20 görüntü bölmesinde bir çocuğun görüntülerinin iki tarafa dağılma olasılığı ≈ %48 (varsayım: yayından gelen 83 / 3; eşit dağılım doğrulanmadı).
- Kâğıttaki çizgi sayısına göre gruplar (56/99/57/26/11) 83'er görüntülük üç gruba benzemiyor; yani çocuk ya da görev gruplaması çizgi sayısıyla kurulamadı.
- Aynı cümlenin farklı çocuklarca kopyalanması nedeniyle içerik tekrarı var (görev kaynaklı), bu kopya değil ama model "cümleyi" ezberleyebilir.
- Öneri (karar değil): sızıntı bilinmediği sürece sonuçlar "iyimser olabilir" notuyla raporlanır; mümkünse yazarlardan katılımcı eşlemesi istenir (Mendeley sayfasındaki iletişim) ya da el yazısı benzerliğiyle gruplama ayrı bir çalışma olarak denenir.

## 7. Ölçüm uygulanabilirliği

Yöntem: uzun yatay beyaz çizgiler (kâğıt çizgileri) bulunup çıkarıldı, kalan "mürekkep" üzerinde bağlı bileşenler ve izdüşüm profilleri hesaplandı.
**Doğruluk için referans etiket yok**; aşağıdaki "uygulanabilir" ifadesi "hesaplanabiliyor ve gözle mantıklı" demektir, "doğru" demek değildir.

| Ölçüm | Durum | Gerekçe |
|---|---|---|
| **Satır eğimi** | Kısmen uygulanabilir | Çizgiler hizalı (açı ≈ 0°, sapma < 0,4°); yazı satırı açısı izdüşüm taramasıyla 249 görüntüde hesaplandı (medyan 0°, %25–75: −0,5/0°, aralık −4,5…+2° ; tarama adımı 0,5°). Çizgi hizalandığı için **kâğıt eğimi** bilgi taşımıyor; anlamlı olan yazının çizgiye göre kayması/dalgalanması. Tek açı satır içi dalgalanmayı göstermez; satır bazlı taban çizgisi ölçümü ve çok satırlı görüntülerde satır ayırma gerekir (denenmedi). Hizalama sırasında yazı eğimi de değişmiş olabilir **[bilinmiyor]**. |
| **Harf boyutu** | Göreli olarak uygulanabilir, mutlak değil | Fiziksel ölçek (DPI, mm) yok; piksel boyutu kırpma/yeniden boyutlandırmaya bağlı. Bileşen yüksekliği medyanı 10–54 px (medyan 22). Çizgi aralığına oran (medyan 0,31) hesaplanabildi ama 193/249 görüntüde (≥ 2 çizgi) mümkün. Harfler birbirine ve çizgiye değdiği için bağlı bileşen ≠ harf (çizgi çıkarılınca bileşen sayısı 57 → 64, harf sayısı değil). Kâğıt çizgi aralığı çocuklar arasında aynı mı **[bilinmiyor]**; aynı değilse oran da kâğıttan etkilenir. |
| **Kelime aralığı** | Sınırlı | Sütun boşluklarından boşluk dağılımı çıkarılabiliyor (görüntü başına 8–161 boşluk), ama harf içi boşluk ile kelime boşluğu ayrımı sezgisel eşiğe dayanıyor; bitişik/el yazısı (cursive) ve noktalama bunu bozar; hizmet verecek bir kelime ayırıcı doğrulanmadı. Satır ayırmada alt satırın uzantıları üst bantlara karışabilir. |
| **Satır aralığı** | Uygulanamaz (çocuğu ölçmüyor) | Satır aralığı **basılı kâğıt çizgilerinden** geliyor (çizgi aralığı 38,7–212 px, görüntüye göre değişiyor); çocuğun seçimi değil. Yalnızca "her çizgiye mi yazdı / atlanan çizgi var mı" ölçülebilir; o da cümle ve çizgi sayısı eşlenmeden güvenilir değil. |
| **Yazı düzeni** (kenar boşlukları, hizalama, sayfa kullanımı) | Uygulanamaz | Görüntüler yazıya sıkı kırpılmış (kenar payları 0–28 px), sayfa kenar boşlukları yok olmuş. Satır içi düzen (satır sonunda taşma, girinti) çok sınırlı ve görev cümlesi bilinmeden yorumlanamaz. |

**Karışıklık (confound) uyarısı [doğrulandı]:** sınıf medyanları, ölçümlerin yazı kalitesi dışındaki şeylerle de ayrışabileceğini gösteriyor:

| | LPD | PD |
|---|---|---|
| Genişlik x yükseklik (medyan) | 1157 x 159 | 1231 x 177,5 |
| Beyaz piksel oranı | 0,074 | 0,107 |
| Çizgi sayısı (medyan) | 2 | 3 |
| Bileşen yüksekliği (medyan, px) | 20 | 31 |
| Yükseklik / çizgi aralığı | 0,27 | 0,44 |

PD'de bileşen yüksekliği ve mürekkep oranı daha yüksek; bu "harf büyüklüğü" farkı olabilir, ama aynı zamanda fırça/kalem kalınlığı, kırpma, yeniden boyutlandırma ve (PD'de daha çok olan 4–5 çizgili) kâğıt formu farkı olabilir. Bu veriyle ayırt edilemez.
Bu tablo **sınıf farkı iddiası değildir**; ölçümlerin hangi karışıklıklarla birlikte okunması gerektiğini gösterir (görev ve çocuk eşlemesi olmadan istatistiksel karşılaştırma yapılmadı).

## 8. Sınırlamalar ve açık sorular

1. Çocuk/öğrenci kimliği yok → sızıntı denetlenemiyor, öğrenci bazında bölme yapılamıyor (Çizim modülünde bu kural var, burada uygulanamaz). Yazarlara sorulabilir.
2. Yaş, sınıf, cinsiyet yok → akran normu (Çizim modülündeki yaklaşım) kurulamaz; "yüzdelik" dili kullanılamaz.
3. Etiket ölçütü (iki uzmanın nasıl karar verdiği, uyum oranı) **[bilinmiyor]**; "potential" ve "low potential" tanı değil, tarama etiketidir. Raporda tanı dili kullanılmaz.
4. Çok küçük örnek (249): ince alt grup analizi ve model karşılaştırması 0,5–1 puanlık farkları ayıramaz (Çizim modülündeki seed yayılımı notuyla aynı mantık).
5. Görüntüler işlenmiş (ikili, ters, kırpılmış, olası hizalama); ham görüntü yok. Ölçek bilgisi yok.
6. Sınıf farkı gibi görünen görüntü özellikleri (mürekkep oranı, boyut, bileşen yüksekliği) görev/çizgi formu/ikilileştirme ile karışık.
7. Çizgi sayısı görev vekili olarak geçersiz bulundu; görev etiketi gerekirse elle ya da OCR ile ayrı bir çalışma olarak çıkarılmalı (denenmedi).

## 9. Sıradaki adım için öneriler (karar değil)
- Yayındaki katılımcı eşlemesi mevcut mu diye veri sahiplerine sormak (sızıntı ve bölme için tek gerçek çözüm).
- Çizim modülünün "betimle + akranla karşılaştır" yaklaşımı yerine, norm olmadığından yalnızca betimleyici ölçümler (eğim dalgalanması, göreli harf boyutu) ve açık sınırlama notu düşünülebilir; bu ayrı plan ve denetleyici turu gerektirir (`CLAUDE.md` iş akışı).
- Model eğitimi öncesi: bölme stratejisi (sızıntı), değerlendirme metriği (macro F1 + güven aralığı) ve görev/çocuk gruplaması konusunda karar.

## Kaynaklar [yayında]
- Veri seti: Potential Dysgraphia Handwriting Dataset of School-Age Children, Mendeley Data, DOI 10.17632/39hr8dx76p.1 (https://data.mendeley.com/datasets/39hr8dx76p). Lisans: CC BY (UiTM deposu listesine göre).
- Veri makalesi: Data in Brief 54 (2024), DOI 10.1016/j.dib.2024.110534. Not: yayın bilgilerini yalnızca web arama sonuç özetlerinden okudum, tam makaleyi açmadım; sayfa/makale ayrıntıları ayrıca doğrulanmalı.
