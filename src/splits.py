from sklearn.model_selection import train_test_split


def stratified_split(df, test_size=0.15, random_state=42):
    """Train split'inden öğrenci bazında val ayırır (eğitim+cinsiyet'e göre stratifiye).

    Aynı öğrencinin çizimleri hep aynı bölümde kalır; sonuç "bolum" sütununa yazılır.
    """
    df = df.copy()
    train_df = df[df.split == "train"]
    students = train_df.groupby("ogrenci").first().reset_index()
    students["grup"] = students.egitim + "_" + students.cinsiyet

    train_students, val_students = train_test_split(
        students.ogrenci, test_size=test_size, stratify=students.grup, random_state=random_state
    )

    df["bolum"] = df.split
    df.loc[df.ogrenci.isin(val_students), "bolum"] = "val"
    return df
