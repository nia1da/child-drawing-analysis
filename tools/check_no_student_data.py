"""Commit öncesi veri denetimi: staged dosyalarda FD-LEX öğrenci verisi izi var mı?

Aranan izler: öğrenci kodu deseni (gevşek), gömülü görüntü çıktısı (ipynb `image/png|jpeg`, base64 görüntü), kapaktaki
kullanıcı satırı ("Benutzer: ..."), `data/handwriting/` yolunun kendisi. Bulursa çıkış kodu 1 (commit durur).
Kanca olarak: `.git/hooks/pre-commit` bu betiği çağırır (`python tools/install_hook.py`). Elle: `python tools/check_no_student_data.py`.
"""
import re
import subprocess
import sys

CODE = re.compile(r"\b[0-9][KkHh]\d{2}[A-Za-z]{2}\d{0,3}\b")        # örn. 0K51AB12; 7-9 karakterli/bozuk kodlar dahil
IMAGE_OUT = re.compile(r'"image/(png|jpeg|jpg)"|data:image/(png|jpeg);base64')
USER_LINE = re.compile(r"Benutzer:\s*\S+")
FORBIDDEN_PATH = re.compile(r"(^|/)data/handwriting/")
# desenleri/örnek ihlalleri içeren dosyalar ve eski KIDO arşiv notebook'u (herkese açık KIDO görüntüleri, base64 gürültüsü yanlış pozitif verir)
BINARY_EXT = (".png", ".jpg", ".jpeg", ".pdf", ".zip", ".xlsx", ".tif", ".tiff")
BINARY_ALLOWED = ("docs/el_yazisi_prototip/", "docs/el_yazisi_ornek_rapor/")  # yalnız sentetik demo görselleri
SKIP = {"tools/check_no_student_data.py", "tests/test_check_no_student_data.py", "notebooks/grad_proj.ipynb"}


def scan_text(name, text):
    """Bir dosyanın metninde ihlalleri listeler."""
    out = []
    if FORBIDDEN_PATH.search(name):
        out.append((name, "veri klasörü staged: data/handwriting/"))
    for pat, label in [(CODE, "öğrenci kodu deseni"), (IMAGE_OUT, "gömülü görüntü çıktısı"), (USER_LINE, "kapak kullanıcı satırı")]:
        m = pat.search(text)
        if m:
            out.append((name, f"{label}: {m.group(0)[:30]!r}"))
    return out


def staged_files():
    r = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"], capture_output=True, text=True, encoding="utf-8")
    return [l for l in r.stdout.splitlines() if l.strip()]


def staged_text(name):
    r = subprocess.run(["git", "show", f":{name}"], capture_output=True)
    return r.stdout.decode("utf-8", errors="ignore")


def main():
    bad = []
    for name in staged_files():
        if name in SKIP:
            continue
        if name.lower().endswith(BINARY_EXT):  # ikili dosyalar: yalnız sentetik demo klasörüne izin var, içerik taranamaz
            if not name.startswith(BINARY_ALLOWED):
                bad.append((name, "görüntü/PDF/tablo dosyası staged (izinli klasörler: docs/el_yazisi_prototip/, docs/el_yazisi_ornek_rapor/)"))
            continue
        bad += scan_text(name, staged_text(name))
    for name, why in bad:
        print(f"[veri denetimi] {name}: {why}", file=sys.stderr)
    if bad:
        print("Commit durduruldu: öğrenci verisi izi (temizleyin; notebook çıktıları dahil).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
