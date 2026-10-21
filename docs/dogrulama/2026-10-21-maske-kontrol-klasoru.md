# Doğrulama: maske kontrol sayfası yeni klasöre yazıyor (2026-10-21)

Kapsam: commit'lenmemiş değişiklik (`git diff`): `src/measurements/mask_check.py`, `tests/test_measurements.py`
(`MaskCheckTest.test_build_keeps_approved_page`), `docs/olcumler.md` (maske kontrol cümlesi).
Ölçüm ya da norm tanımı değişmedi; korelasyon / uç değer / küçük çizim denetimi bu değişiklik için geçerli değil.
`--quick` eğitim koşulmadı (eğitim koduna dokunulmadı, görevde istenmedi). Hiçbir dosya düzeltilmedi.

## Sonuç: GEÇTİ (küçük notlarla)

## Yapılan kontroller

1. **Testler**: `.venv/Scripts/python -m unittest discover -s tests -t .` → 50 test, OK. `MaskCheckTest` 2 test, OK.

2. **Onaylı klasöre yazan yol var mı**: yok.
   - `build()` artık sadece `{output_dir}/maske_kontrol_<YYYYMMDD-HHMM>` oluşturuyor; bütün yazmalar (PNG'ler,
     `ozet_*.png`, `liste.csv`, `index.html`) `folder` altında. `os.makedirs(folder)` `exist_ok` olmadan: klasör
     varsa yazmadan önce hata.
   - Repo genelinde (`*.py`, `*.md`, `*.ipynb`) `maske_kontrol` geçen başka yazma kodu yok; notebook'larda da yok.
   - Drive'daki onaylı `maske_kontrol/` salt okunur incelendi: dosya zamanları 2026-10-19 19:23 (değişmemiş),
     Drive'da `maske_kontrol_*` klasörü yok (testler Drive'a yazmadı). `deneyler.csv` zamanı 2026-10-19 19:02, değişmemiş.

3. **Aynı dakikada iki çalıştırma** (geçici klasörde, `datetime` sabitlenerek, `pick` mock'lu):
   1. çalıştırma `maske_kontrol_20261021-1530/` oluşturdu; 2. çalıştırma
   `FileExistsError: [WinError 183] Cannot create a file when that file already exists: '...\maske_kontrol_20261021-1530'`
   verdi, mevcut klasöre hiçbir şey yazmadı. Davranış doğru ve güvenli; mesaj işletim sisteminin İngilizce mesajı,
   klasör yolu görünür, anlaşılır ama "bir dakika sonra tekrar deneyin" gibi Türkçe yönlendirme yok (not 1).
   Zaman damgası gerçekten Europe/Istanbul (o anda UTC 12:52, damga 15:52).

4. **Test davranışı sınıyor mu**: evet. Yeni test, HEAD'deki eski `mask_check.py`'ye karşı koşturuldu:
   `AssertionError: 'maske_kontrol' == 'maske_kontrol'` ile düşüyor; yeni kodla geçiyor. Test ayrıca onaylı
   `liste.csv`'nin içeriğinin bozulmadığını kontrol ediyor (eski kod boş tabloyla üzerine yazardı, bu da yakalanırdı).
   Testin sınamadıkları (not 2): var olan klasörde hata verme (`exist_ok` geri eklense test yine geçer) ve saat dilimi.

5. **Belgeler kodla tutarlı mı**: evet.
   - `docs/olcumler.md`: "aday havuzu o zaman bütün bölümlerdi, seçilen 24 çizimin 21'i train, 3'ü val" iddiası
     Drive'daki onaylı `maske_kontrol/liste.csv`'den doğrulandı (24 satır; `bolum`: train 21, val 3). "Yeni
     çalıştırmalar sadece train'den seçer" `pick()`'teki `df[df.bolum == "train"]` ile ve mevcut
     `test_pick_reads_only_train_images` ile tutarlı.
   - Modül docstring'i ve CLAUDE.md (satır 74-75, zaten commit'li) aynı şeyi söylüyor.
   - Küçük kesinsizlik: belgelerde `maske_kontrol_<tarih>`, gerçek ad tarih + saat-dakika (`<YYYYMMDD-HHMM>`) (not 3).

6. **Test seti / bölme / deneyler.csv**: test görseli okunmadı, `kido_metadata.csv` ve bölme değişmedi, `deneyler.csv`'ye
   kayıt düşmedi (testlerdeki `deneyler.csv` taşıma mesajları geçici klasörlerde).

## Notlar (engelleyici değil)

1. Aynı dakikada ikinci çalıştırmanın hatası ham `FileExistsError`. İstenirse yakalanıp Türkçe açıklama verilebilir.
2. Test, `os.makedirs` çağrısının `exist_ok` olmadan yapıldığını sınamıyor; sabitlenmiş saatle iki kez `build()`
   çağırıp `FileExistsError` beklemek bu açığı kapatır.
3. `makedirs` `pick()`'ten önce: `pick()` / `load_metadata()` hata verirse boş `maske_kontrol_<damga>/` kalıyor
   (denendi) ve aynı dakika içinde tekrar çalıştırma engelleniyor. Zararsız ama Drive'da boş klasör bırakabilir.
4. Belgelerde `<tarih>` yerine `<YYYYMMDD-HHMM>` yazmak adı tam tarif ederdi.
