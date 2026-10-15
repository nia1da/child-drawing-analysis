from sklearn.model_selection import train_test_split


def stratifiye_bol(df, test_size=0.15, random_state=42):
    """Train split'inden öğrenci bazında val ayırır (eğitim+cinsiyet'e göre stratifiye).

    Aynı öğrencinin çizimleri hep aynı bölümde kalır; sonuç "bolum" sütununa yazılır.
    """
    df = df.copy()
    train_df = df[df.split == "train"]
    ogrenciler = train_df.groupby("ogrenci").first().reset_index()
    ogrenciler["grup"] = ogrenciler.egitim + "_" + ogrenciler.cinsiyet

    tr_ogr, val_ogr = train_test_split(
        ogrenciler.ogrenci, test_size=test_size, stratify=ogrenciler.grup, random_state=random_state
    )

    df["bolum"] = df.split
    df.loc[df.ogrenci.isin(val_ogr), "bolum"] = "val"
    return df
