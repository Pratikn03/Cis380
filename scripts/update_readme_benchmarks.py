from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


START = "<!-- BENCHMARKS:START -->"
END = "<!-- BENCHMARKS:END -->"


def _ensure_readme_markers(readme_path: Path) -> str:
    if not readme_path.exists():
        readme_path.write_text("# Sentifargo\n", encoding="utf-8")
    text = readme_path.read_text(encoding="utf-8")
    if START in text and END in text:
        return text

    block = "\n## Benchmarks\n\n" f"{START}\n" "_Benchmarks not generated yet._\n" f"{END}\n"
    return text.rstrip() + "\n" + block + "\n"


def main() -> None:
    readme_path = Path("README.md")
    readme_text = _ensure_readme_markers(readme_path)

    md = subprocess.check_output([sys.executable, "scripts/generate_benchmarks.py"], text=True)

    replacement = f"{START}\n\n`reports/benchmarks.md` is auto-generated.\n\n{md.strip()}\n\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    updated = pattern.sub(replacement, readme_text)
    readme_path.write_text(updated, encoding="utf-8")

    print("✅ Updated README.md benchmarks section.")
    print("✅ Saved table also at reports/benchmarks.md")


if __name__ == "__main__":
    main()
