from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Set

ROOT = Path(".").resolve()

EXCLUDE_DIRS = {
    ".venv",
    "venv",
    "__pycache__",
    ".git",
    "ui-web/frontend/node_modules",
    "ui-web/frontend/dist",
    "src/mlruns",
    "runs",
    "data",
    "artifacts",
    "ui-web/frontend/.cache",
}


def is_excluded(p: Path) -> bool:
    s = p.as_posix()
    for d in EXCLUDE_DIRS:
        if d in s:
            return True
    return False


def collect_ui_api_refs() -> Set[str]:
    refs = set()
    # Streamlit Python + frontend TS/TSX/JS
    patterns = [
        ("app/streamlit_chatbot", {".py"}),
        ("ui-web/frontend/src", {".ts", ".tsx", ".js"}),
    ]
    api_re = re.compile(r"(/api/[a-zA-Z0-9_\-\/]+)")
    for base, exts in patterns:
        basep = ROOT / base
        if not basep.exists():
            continue
        for p in basep.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts:
                continue
            if is_excluded(p):
                continue
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in api_re.finditer(txt):
                refs.add(m.group(1))
    return refs


def load_openapi(path: Path) -> Set[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    paths = set(data.get("paths", {}).keys())
    return paths


def main():
    openapi_path = ROOT / "reports/openapi.json"
    if not openapi_path.exists():
        print("❌ reports/openapi.json not found.")
        print(
            "Run the server then: curl -s http://localhost:8000/openapi.json > reports/openapi.json"
        )
        sys.exit(1)

    ui_refs = sorted(collect_ui_api_refs())
    api_paths = sorted(load_openapi(openapi_path))

    ui_set = set(ui_refs)
    api_set = set(api_paths)

    missing = sorted(ui_set - api_set)  # UI references not served
    unused = sorted(api_set - ui_set)  # served routes never referenced by UI (not always bad)

    out = []
    out.append("# API Contract Diff Report\n")
    out.append("## Counts\n")
    out.append(f"- OpenAPI routes served: **{len(api_set)}**")
    out.append(f"- UI routes referenced: **{len(ui_set)}**")
    out.append(f"- UI routes missing in OpenAPI (likely 404): **{len(missing)}**")
    out.append(f"- OpenAPI routes unused by UI: **{len(unused)}**\n")

    out.append("## Missing (UI references that are not in OpenAPI)\n")
    for x in missing[:300]:
        out.append(f"- `{x}`")
    out.append("\n## Unused (OpenAPI routes not referenced by UI)\n")
    for x in unused[:300]:
        out.append(f"- `{x}`")

    report_path = ROOT / "reports/CONTRACT_DIFF.md"
    report_path.write_text("\n".join(out), encoding="utf-8")
    print("✅ wrote reports/CONTRACT_DIFF.md")
    print(
        f"OpenAPI={len(api_set)} UIrefs={len(ui_set)} Missing={len(missing)} Unused={len(unused)}"
    )


if __name__ == "__main__":
    main()
