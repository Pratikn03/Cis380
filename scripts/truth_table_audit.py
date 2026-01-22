from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(".").resolve()


def read_text(p: Path, limit=500_000) -> str:
    try:
        b = p.read_bytes()
        if len(b) > limit:
            b = b[:limit]
        return b.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def find_endpoints(py: Path) -> List[Tuple[str, str, str]]:
    """
    returns (method, path, file)
    """
    t = read_text(py)
    out = []
    # @router.get("/x") / @app.post("/y")
    dec_re = re.compile(r"@(\w+)\.(get|post|put|delete|patch)\(\s*([\"'])(.+?)\3", re.I)
    for m in dec_re.finditer(t):
        out.append((m.group(2).upper(), m.group(4), str(py.relative_to(ROOT))))
    return out


def classify_file(rel: str) -> str:
    s = rel.replace("\\", "/")
    if s.startswith("app/legacy/"):
        return "LEGACY"
    if s.startswith("app/api/"):
        return "CURRENT_API"
    if s.startswith("app/rag_dsa/") or s.startswith("app/rag/"):
        return "RAG_CORE"
    if s.startswith("app/services/"):
        return "SERVICES"
    if s.startswith("deploy/"):
        return "DEPLOY"
    if s.startswith("src/train/") or s.startswith("scripts/train") or "/training/" in s:
        return "TRAINING"
    if s.startswith("app/streamlit_chatbot/"):
        return "STREAMLIT_UI"
    return "OTHER"


def grep_model_loads() -> List[Tuple[str, str]]:
    patterns = [
        r"joblib\.load\(",
        r"pickle\.load\(",
        r"torch\.load\(",
        r"load_model\(",
        r"mlflow\.pyfunc\.load_model\(",
        r"onnxruntime\.InferenceSession\(",
    ]
    hits = []
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT))
        txt = read_text(p, 250_000)
        for pat in patterns:
            if re.search(pat, txt):
                hits.append((rel, pat))
                break
    return hits


def grep_ui_calls() -> List[Tuple[str, str]]:
    """
    Find which API endpoints UI references: http://.../api/..., requests.post/get, fetch, etc.
    """
    hits = []
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT))
        if not rel.startswith("app/streamlit_chatbot/"):
            continue
        txt = read_text(p, 300_000)
        for m in re.finditer(r"/api/[a-zA-Z0-9_\-/]+", txt):
            hits.append((rel, m.group(0)))
    # also check frontend TS/TSX
    for p in ROOT.rglob("*"):
        if p.suffix.lower() not in {".ts", ".tsx", ".js"}:
            continue
        rel = str(p.relative_to(ROOT))
        if not rel.startswith("ui-web/"):
            continue
        txt = read_text(p, 300_000)
        for m in re.finditer(r"/api/[a-zA-Z0-9_\-/]+", txt):
            hits.append((rel, m.group(0)))
    return hits


def main():
    # endpoints
    all_eps = []
    for p in ROOT.rglob("*.py"):
        eps = find_endpoints(p)
        all_eps.extend(eps)

    # group endpoints by category
    grouped: Dict[str, List[Tuple[str, str, str]]] = {}
    for method, path, file in all_eps:
        cat = classify_file(file)
        grouped.setdefault(cat, []).append((method, path, file))

    model_loads = grep_model_loads()
    ui_calls = grep_ui_calls()

    # write markdown
    md = []
    md.append("# Truth Table Audit (Current vs Legacy vs Training vs UI)\n")
    md.append("## Endpoint Inventory (grouped)\n")
    for cat in sorted(grouped.keys()):
        items = grouped[cat]
        md.append(f"### {cat} — {len(items)} endpoints\n")
        for method, path, file in sorted(items)[:120]:
            md.append(f"- `{method}` `{path}` — `{file}`")
        md.append("")
    md.append("## Model Loading Evidence (runtime loads)\n")
    md.append(f"- Files with model-load patterns: **{len(model_loads)}**\n")
    for rel, pat in model_loads[:200]:
        md.append(f"- `{rel}` matched `{pat}`")
    md.append("")
    md.append("## UI → API Calls Evidence\n")
    md.append(f"- UI files referencing `/api/*`: **{len(ui_calls)}**\n")
    for rel, ep in ui_calls[:200]:
        md.append(f"- `{rel}` references `{ep}`")
    md.append("")
    out = ROOT / "reports/TRUTH_TABLE.md"
    out.write_text("\n".join(md), encoding="utf-8")
    print("✅ wrote reports/TRUTH_TABLE.md")
    print("Counts:", {k: len(v) for k, v in grouped.items()})
    print("Model-load hits:", len(model_loads))
    print("UI api refs:", len(ui_calls))


if __name__ == "__main__":
    main()
