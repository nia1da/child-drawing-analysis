# Doğrulama: görev uyumu planı adım 2 (val analizi, norm grubu kararı; commit'lenmemiş değişiklik, 2026-10-21)

Denetleyen: dogrulayici subagent'ı. Kapsam: yeni `src/task_fit.py`, yeni `tests/test_task_fit.py`,
`docs/olcumler.md` sonuna eklenen "Model tabanlı ölçümler" bölümü.
Sonuç: **GEÇTİ**. Kod, önceden yazılmış ölçütü harfiyen uyguluyor; sayılar bağımsız hesapla birebir aynı.
Aşağıda iki not var (Bonferroni'nin testsiz olması, belgede "düzeltmesiz anlamlı" durumunun açık yazılmaması); düzeltme
şart değil ama öneriliyor.

## Çalıştırılanlar
- unittest: 57 test geçti (7'si yeni).
- `python -m src.training --model convnext_tiny --size 320 --quick`: cuda, 1 epoch, "kayıt yazılmadı".
  `evaluation --quick` çalıştırılmadı: varsayılan bölümü `test`, bu aşamada test açılmamalı.
- `python -m src.task_fit`: 1386 çizim, 693 öğrenci; karar "eğitim seviyesi x görev".
- `deneyler.csv`: son değişiklik 2026-10-19 19:02, koşulardan sonra da aynı.
- Bölme: `data/kido_metadata.csv` 2026-10-19'dan beri değişmedi (train 7842, val 1386, test 1632); val tahmin
  dosyasındaki 1386 dosya metadata'daki val kümesiyle birebir aynı.

## 1. Ölçüt plana uygun mu (`git show b0e80d4` ile karşılaştırma)
- Zaman sırası: plan commit'i 15:51:40, val tahmin dosyası 15:52:29. Ölçüt tahminlerden önce yazılmış.
- Hücreler: 4 görev uyumu (seviye x görev, çizim başına) + 2 ayrışma (seviye, öğrenci başına) = 6. Plana uygun.
- Bonferroni: `alpha = ALPHA / len(found)` = 0,05 / 6 = 0,00833; anlamlılık `p < alpha` (katı). Plana uygun.
- Yüzdelik: `pool_percentiles` = (ortalama sıra − 0,5) / n x 100; eşitlik bloğunda bu, `norms.percentile`'ın
  (altta kalanlar + eşitlerin yarısı) / n tanımıyla cebirsel olarak aynı. Test (`test_pool_percentiles_match_norms`)
  eşitli bir dizide de doğruluyor. Havuz = seviye x görev hücresinin kendisi; sınıf medyanı bu havuzdaki yüzdeliklerin
  medyanı. Plana uygun.
- Pratik eşik: `shift >= MIN_SHIFT` ("en az 10 puan"), yuvarlanmamış sapma üzerinden (yuvarlama sadece gösterimde).
- Belirgin: `p < alpha and shift >= MIN_SHIFT`, aynı satırda (aynı hücre). Karar: herhangi bir hücre belirginse "sinif".
- d kuralı: `saturation_share > 0,25` ("%25'inden fazlası", eşitte olasılık kalır; testle sabit), uçlar katı
  `< 0,1` / `> 0,9`. Seçim `cells()` içinde gruplama testinden önce yapılıyor. Plana uygun.
- Veriye bakarak ölçütü değiştiren bir şey yok: sabitler modül başında, veri bağımlı eşik, hücre eleme, sınıf
  birleştirme ya da alternatif test yok. Kruskal–Wallis scipy'nin eşitlik düzeltmeli hali.

## 2. Çıktı ve belge
`python -m src.task_fit` çıktısı `docs/olcumler.md` tablosuyla birebir aynı (6 hücrenin KW p'leri, en büyük sapmalar,
bütün sınıf medyanları). Belgedeki diğer sayılar da çıktıyla tutarlı: aynı uçta yığılma %5,9; `d > 0` %86,4
(olasılık ve logitte aynı, `d = 0` olan çift yok); seviye n'leri 346 / 347; sınıf x görev grupları 44–134.

## 3. Bağımsız yeniden hesap
Scratchpad betiği (`csv` modülü + elle sıralama, elle eşitlik düzeltmeli H, `chi2.sf`; `task_fit` import edilmeden)
altı hücrenin hepsini yeniden hesapladı. KW p'leri 6 ondalığa kadar aynı (örn. ortaokul üzgün 0,030151; ilkokul
ayrışma 0,218447), sınıf medyanları 0,1'e kadar aynı, sınıf n'leri (1: 44, 2: 53, 3: 134, 4: 115, 5: 116, 6: 93,
7: 83, 8: 55) planla aynı.

Ek duyarlılık (karar değişmez, bilgi için): ayrışmada logit farkı kullanılsaydı KW p ilkokul 0,226, ortaokul 0,254;
en büyük sapma ilkokulda 10,0 (2. sınıf 40,0). Karar yine "seviye".

## 4. pairs()
- Tam bir mutlu + bir üzgün kontrolü: `counts == 1` (eksik görev 0 ile dolduruluyor, fazla görev 2 olur), ikisi de
  hata veriyor. Mutasyonla kontrol kaldırılınca test düşüyor.
- Gerçek veride: 693 öğrencinin hepsinde tam 2 çizim (H + S); öğrenci içinde sınıf ya da eğitim tutarsızlığı 0;
  sınıf–eğitim eşlemesi (1–4 Primary) her satırda tutarlı; `duygu` sütunu dosya adındaki görev harfiyle 1386 satırda
  aynı. Dolayısıyla `drop_duplicates("ogrenci")` ile ilk satırdan eğitim/sınıf almak güvenli; ancak kod bu tutarlılığı
  kendisi kontrol etmiyor (KIDO'da sorun yok, not).
- Yön: görev uyumu mutluda 1 − p, üzgünde p; `d = p_uzgun − p_mutlu` (pozitif = görevlerine uygun yönde). Doğru;
  ikisinin de ters çevrilmesi testlerde yakalanıyor.

## 5. Testler ve mutasyon (scratchpad kopyasında, repo değişmedi)
| Mutasyon | Sonuç |
|---|---|
| pratik eşik 10 → 50 | düştü |
| belirgin `and` → `or` | düştü |
| yüzdelik orta sıra → max sıra | düştü |
| görev uyumu yönü ters | düştü (2) |
| doygunluk eşiği `>` → `>=` | düştü |
| çift kontrolü kaldırıldı | düştü |
| `d` işareti ters | düştü |
| **Bonferroni kaldırıldı (`alpha = ALPHA`)** | **geçti (yakalanmadı)** |

Not 1: Bonferroni bu veride kararı belirleyen öğe. Düzeltmesiz (p < 0,05) ortaokul üzgün hücresi (p = 0,030, sapma
11,8) iki koşulu birden sağlar ve karar "sınıf x görev" olurdu. Kod doğru, ama bu satırı koruyan test yok; p'si
0,0083 ile 0,05 arasında, sapması ≥ 10 olan bir hücreyle "seviye" kararını bekleyen bir test öneriliyor.

## 6. Hijyen
- Test bölümü okunmadı: `SPLIT = "val"` sabit, `load_predictions` tek çağrı `(args.experiment, SPLIT)`; 320px model
  için `tahminler/` altında test dosyası yok (yalnız 16 Ekim'den kalma 448px ve resnet50 test dosyaları).
- Train norma girmiyor: modül train'e hiç dokunmuyor; havuz yalnız val tahminleri.
- Cinsiyet: `task_fit.py`'de `cinsiyet` geçmiyor; hiçbir hesapta, grupta ya da çıktıda yok. Testlerde sentetik
  tablonun sütunu olarak sabit "Female", hesaba girmiyor.
- Dosya okuma pandas üzerinden (`read_csv`, UTF-8 varsayılan); yazma yok.
- Görev talimatındaki Spearman (doluluk / boyama / kalınlık) ve küçük çizim savrulması kontrolleri bu adıma
  uygulanmadı: görüntü ölçümü değişmedi, model skoru train üzerinde hesaplanmıyor. Seyrek çizim etkisi plandaki
  sınırlama notunda; adım 3–6'da bakılmalı.

## 7. Belgedeki yorumlar
- Yığılma sayıları doğru: medyan 0,907–0,935 ("0,91–0,94"), %75 0,946–0,954 ("0,95"), %95 0,962–0,966
  ("0,96–0,97"); uyum > 0,9 mutluda 0,549 / 0,527, üzgünde 0,552 / 0,620 ("%53–55", "%55–62"). "50. ile 95. dilim
  arası ≈ 0,04": gerçek aralık 0,031–0,056; "≈ 0,03–0,06" daha kesin olur (küçük not).
- "Hiçbir hücrede iki koşul birlikte sağlanmadı", "iki hücrede sapma 10'u geçti ama anlamlı değil (7. sınıf üzgün,
  2. sınıf ayrışma)": doğru. Not 2: 7. sınıf üzgün hücresinin p'si (0,030) düzeltmesiz 0,05'in altında; "anlamlı
  değil" Bonferroni'ye göre doğru ama belgede "Bonferroni sonrası" diye yazılması ve kararın bu düzeltmeye bağlı
  olduğunun söylenmesi daha dürüst olur (ölçüt önceden yazıldığı için karar meşru, sadece okuyucuya sınır durumu
  görünmeli).
- "label smoothing 0,1 skorları 0,95 civarında topluyor": iki sınıflı ls 0,1'in hedefi 0,95; gözlenen %75 değeriyle
  uyumlu, kabul.
- Açık iş: plan sonucun `docs/kararlar.md`'ye de yazılmasını istiyor; kararlar.md'de ölçüt satırı var (46. satır) ama
  sonuç ("seviye x görev", KW p'leri) henüz yok.

## Sonuç: GEÇTİ
Öneriler (zorunlu değil): (1) Bonferroni'yi koruyan test; (2) `olcumler.md`'de ortaokul üzgün hücresi için
"düzeltmesiz p = 0,030; Bonferroni sonrası anlamlı değil" ifadesi; (3) kararlar.md'ye sonuç satırı; (4) isteğe bağlı
olarak `pairs()`'te öğrenci içi eğitim/sınıf tutarlılık kontrolü.
