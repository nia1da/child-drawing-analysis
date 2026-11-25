"""`.git/hooks/pre-commit` kancasını kurar: commit öncesi `tools/check_no_student_data.py` çalışır.

Kanca git tarafından izlenmez (her klonda bir kez kurulur): `python tools/install_hook.py`.
Mevcut bir pre-commit kancası varsa üzerine yazmaz.
"""
import stat
import sys
from pathlib import Path

HOOK = """#!/bin/sh
# FD-LEX öğrenci verisi denetimi (tools/install_hook.py ile kuruldu)
for py in .venv/Scripts/python .venv/bin/python python3 python; do
  if command -v "$py" >/dev/null 2>&1 || [ -x "$py" ]; then exec "$py" tools/check_no_student_data.py; fi
done
echo "pre-commit: python bulunamadı, veri denetimi atlandı" >&2
exit 1
"""


def main():
    hook = Path(__file__).resolve().parents[1] / ".git" / "hooks" / "pre-commit"
    if hook.exists() and "check_no_student_data" not in hook.read_text(encoding="utf-8", errors="ignore"):
        print(f"{hook} zaten var (başka bir kanca); üzerine yazılmadı.", file=sys.stderr)
        return 1
    hook.write_text(HOOK, encoding="utf-8", newline="\n")
    hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    print("Kuruldu:", hook)
    return 0


if __name__ == "__main__":
    sys.exit(main())
