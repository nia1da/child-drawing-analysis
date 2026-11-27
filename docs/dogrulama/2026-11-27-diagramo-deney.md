# Doğrulama: DiaGraMo deneyleri (2026-11-27)

Sonuç: **GEÇTİ** (engelleyici bulgu yok). Dogrulayici: testler (161 → 162), sızıntı denetimi (bölme okul bazlı, sha256 eşleşti, bölme özellik/model dosyalarından önce, ön işleme yalnız eğitim katında), belge sayılarının bağımsız yeniden hesabı (hepsi eşleşti), model girdisi (yalnız ikili mürekkep maskesi özellikleri + görev türü), gizlilik ve kapsam temiz.

Bulgular ve işlem:
1. Deney betikleri repoda yoktu → `experiments.py` eklendi; belgeye §11 notu (yeniden çalıştırılarak doğrulanmadı).
2. `cnn.final_test_emb` kilidi denetlemiyordu → düzeltildi (kilit varsa hata).
3. OrdinalLogit monotonlaştırma mutasyonu testte yakalanmıyordu → sinyalsiz etiketli test eklendi.
4. Belge: Model B CV QWK aralığı 0,23–0,48 olarak düzeltildi; render rastgeleleştirmede düzeltmeler hedefinde orijinal ayarda kötüleşme (0,40 → 0,33) belirtildi.
5. Not: sayfa düzeni için RF ile OL_C0,1 arasındaki fark 0,0008 (seçim fiilen kararsız; kural önceden yazılıydı). Sızıntıyı doğrudan sınayan test ve `cnn.py` testi yok (açık).
