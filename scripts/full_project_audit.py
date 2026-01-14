from __future__ import annotations
import os, re, json, time, hashlib, ast, subprocess, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", "dist", "build", ".next", ".cache",
    ".idea", ".vscode",
}

FASTAPI_DECORATORS = ("get","post","put","delete","patch","options","head")
TRAIN_HINTS = [
    "train(", "fit(", "Trainer", "DataLoader", "torch", "pytorch", "tensorflow", "keras",
    "ultralytics", "YOLO", "yolov8", "yolo", "mAP", "coco",
    "autogluon", "lightautoml", "h2o", "H2OAutoML", "flaml", "xgboost", "lightgbm", "catboost",
    "librosa", "torchaudio", "mfcc", "spectrogram", "wav2vec",
]

RAG_HINTS = ["langchain","chromadb","Chroma","FAISS","OpenAIEmbeddings","vectorstore","retriever","rerank","rewrite"]

@dataclass
class Endpoint:
    file: str
    router: str
    method: str
    path: str

@dataclass
class RouterInclude:
    file: str
    expr: str

@dataclass
class DupGroup:
    sha256: str
    files: List[str]

@dataclass
class Audit:
    root: str
    files_scanned: int
    py_files: int
    total_bytes: int

    fastapi_includes: List[RouterInclude]
    fastapi_endpoints: List[Endpoint]

    training_candidates: List[str]
    rag_candidates: List[str]

    duplicates: List[DupGroup]

    py_compile_errors: List[str]
    pip_requirements_files: List[str]
    docker_files: List[str]
    ci_files: List[str]

    data_dirs: Dict[str,int]
    missing_expected_data_dirs: List[str]

    unreferenced_internal_modules: List[str]
    notes: List[str]

def is_excluded_dir(d: str) -> bool:
    return d in EXCLUDE_DIRS

def walk(root: Path) -> List[Path]:
    out: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not is_excluded_dir(d)]
        for fn in filenames:
            out.append(Path(dirpath) / fn)
    return out

def read_text(p: Path, limit: int = 400_000) -> str:
    try:
        b = p.read_bytes()
        if len(b) > limit:
            b = b[:limit]
        return b.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def sha256_file(p: Path, max_bytes: int = 2*1024*1024) -> Optional[str]:
    try:
        if p.stat().st_size > max_bytes:
            return None
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024*1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def detect_fastapi(p: Path) -> Tuple[List[RouterInclude], List[Endpoint]]:
    t = read_text(p)
    inc: List[RouterInclude] = []
    eps: List[Endpoint] = []

    for m in re.finditer(r"\binclude_router\s*\((.*?)\)", t, flags=re.S):
        expr = " ".join(m.group(1).split())
        inc.append(RouterInclude(file=str(p), expr=expr[:250]))

    dec_re = re.compile(r"@(\w+)\.(" + "|".join(FASTAPI_DECORATORS) + r")\(\s*([\"'])(.+?)\3", re.I)
    for m in dec_re.finditer(t):
        eps.append(Endpoint(file=str(p), router=m.group(1), method=m.group(2).upper(), path=m.group(4)))

    return inc, eps

def looks_like_training(p: Path) -> bool:
    t = read_text(p, 250_000).lower()
    hits = sum(1 for h in TRAIN_HINTS if h.lower() in t)
    return hits >= 3 or ("yolo" in t and "train" in t) or ("autogluon" in t and "fit" in t)

def looks_like_rag(p: Path) -> bool:
    t = read_text(p, 250_000)
    hits = sum(1 for h in RAG_HINTS if h in t)
    return hits >= 2

def compile_check(py_files: List[Path]) -> List[str]:
    errs = []
    for p in py_files:
        try:
            src = read_text(p)
            compile(src, str(p), "exec")
        except Exception as e:
            errs.append(f"{p}: {type(e).__name__}: {e}")
    return errs

def import_graph_unreferenced(py_files: List[Path], root: Path) -> List[str]:
    module_map: Dict[str, Path] = {}
    for p in py_files:
        rel = p.relative_to(root).as_posix()
        if rel.startswith(("app/","src/")) and rel.endswith(".py"):
            mod = rel[:-3].replace("/", ".")
            if mod.endswith(".__init__"):
                mod = mod[:-len(".__init__")]
            module_map[mod] = p

    referenced: Set[Path] = set()
    entry_like: Set[Path] = set()
    entry_names = {"main.py","app.py","server.py","wsgi.py","asgi.py"}
    for p in py_files:
        rel = p.as_posix()
        if p.name in entry_names or "/scripts/" in rel or p.name.startswith("run_") or p.name.endswith("_cli.py"):
            entry_like.add(p)

    for p in py_files:
        txt = read_text(p)
        try:
            tree = ast.parse(txt)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    nm = a.name
                    if nm.startswith(("app.","src.")):
                        if nm in module_map:
                            referenced.add(module_map[nm])
            elif isinstance(node, ast.ImportFrom):
                nm = node.module or ""
                if nm.startswith(("app.","src.")):
                    # try exact or parent
                    parts = nm.split(".")
                    while parts:
                        cand = ".".join(parts)
                        if cand in module_map:
                            referenced.add(module_map[cand])
                            break
                        parts.pop()

    # router files count as referenced
    for p in py_files:
        t = read_text(p, 100_000)
        if "APIRouter" in t and ("@router." in t or "include_router" in t):
            referenced.add(p)

    unref = []
    for mod, path in module_map.items():
        if path not in referenced and path not in entry_like:
            unref.append(str(path))
    return sorted(unref)

def summarize_data(root: Path) -> Tuple[Dict[str,int], List[str]]:
    expected = ["data/raw","data/processed","artifacts","runs","models","configs","reports"]
    summary: Dict[str,int] = {}
    missing: List[str] = []
    for d in expected:
        p = root / d
        if not p.exists():
            missing.append(d)
            continue
        cnt = 0
        for x in p.rglob("*"):
            if x.is_file():
                cnt += 1
        summary[d] = cnt
    return summary, missing

def find_files_by_names(root: Path, names: List[str]) -> List[str]:
    out = []
    for p in root.rglob("*"):
        if p.is_file() and p.name in names:
            out.append(str(p))
    return sorted(out)

def find_ci_files(root: Path) -> List[str]:
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        s = p.as_posix()
        if ".github/workflows/" in s or s.endswith((".gitlab-ci.yml",".circleci/config.yml")):
            out.append(str(p))
    return sorted(out)

def main():
    root = Path(".").resolve()
    t0 = time.time()

    files = [p for p in walk(root) if p.is_file()]
    py_files = [p for p in files if p.suffix == ".py"]
    total_bytes = sum(p.stat().st_size for p in files)

    # duplicates
    hash_map: Dict[str,List[str]] = {}
    for p in files:
        h = sha256_file(p, max_bytes=2*1024*1024)
        if not h:
            continue
        hash_map.setdefault(h, []).append(str(p))
    dups = [DupGroup(sha256=h, files=sorted(v)) for h,v in hash_map.items() if len(v) >= 2]
    dups.sort(key=lambda g: (-len(g.files), g.sha256))

    # fastapi
    includes: List[RouterInclude] = []
    endpoints: List[Endpoint] = []
    for p in py_files:
        inc, eps = detect_fastapi(p)
        includes.extend(inc)
        endpoints.extend(eps)

    # training and rag candidates
    training = [str(p) for p in py_files if looks_like_training(p)]
    rag = [str(p) for p in py_files if looks_like_rag(p)]
    training.sort(); rag.sort()

    # compile errors
    compile_errors = compile_check(py_files)

    # other infra files
    reqs = [str(p) for p in root.rglob("*") if p.is_file() and p.name in {"requirements.txt","pyproject.toml","poetry.lock","Pipfile","Pipfile.lock"}]
    docker = find_files_by_names(root, ["Dockerfile","docker-compose.yml","docker-compose.yaml","Dockerfile.production","Dockerfile.prod"])
    ci = find_ci_files(root)

    # data summary
    data_summary, missing_data_dirs = summarize_data(root)

    # unreferenced (heuristic)
    unref = import_graph_unreferenced(py_files, root)

    notes = []
    if not includes and not endpoints:
        notes.append("No FastAPI include_router/endpoints detected (maybe different patterns/framework).")
    if compile_errors:
        notes.append("Python compile errors found. Fix these first; they usually break integration.")
    if dups:
        notes.append("Duplicate files found with identical content hash (safe to consolidate later).")
    if unref:
        notes.append("Unreferenced internal modules found (may indicate duplicates/dead code).")
    if missing_data_dirs:
        notes.append("Some standard data dirs missing (not always a problem, but check).")

    audit = Audit(
        root=str(root),
        files_scanned=len(files),
        py_files=len(py_files),
        total_bytes=total_bytes,
        fastapi_includes=includes[:800],
        fastapi_endpoints=endpoints[:1200],
        training_candidates=training[:400],
        rag_candidates=rag[:400],
        duplicates=dups[:250],
        py_compile_errors=compile_errors[:250],
        pip_requirements_files=reqs,
        docker_files=docker,
        ci_files=ci,
        data_dirs=data_summary,
        missing_expected_data_dirs=missing_data_dirs,
        unreferenced_internal_modules=unref[:400],
        notes=notes,
    )

    Path("reports").mkdir(parents=True, exist_ok=True)
    Path("reports/PROJECT_AUDIT.json").write_text(json.dumps(asdict(audit), indent=2, ensure_ascii=False), encoding="utf-8")

    # Markdown report
    md = []
    md.append("# Full Project Audit Report\n")
    md.append(f"- Root: `{audit.root}`")
    md.append(f"- Files scanned: **{audit.files_scanned}**")
    md.append(f"- Python files: **{audit.py_files}**")
    md.append(f"- Total size (bytes): **{audit.total_bytes}**\n")

    md.append("## Infra Files Found\n")
    md.append(f"- Requirements/pyproject files: {len(audit.pip_requirements_files)}")
    for x in audit.pip_requirements_files: md.append(f"  - `{x}`")
    md.append(f"- Docker files: {len(audit.docker_files)}")
    for x in audit.docker_files: md.append(f"  - `{x}`")
    md.append(f"- CI files: {len(audit.ci_files)}")
    for x in audit.ci_files[:20]: md.append(f"  - `{x}`")
    md.append("")

    md.append("## Data / Artifacts Summary (file counts)\n")
    if audit.data_dirs:
        for k,v in audit.data_dirs.items():
            md.append(f"- `{k}`: **{v}** files")
    if audit.missing_expected_data_dirs:
        md.append("\nMissing expected dirs (not always fatal):")
        for d in audit.missing_expected_data_dirs:
            md.append(f"- `{d}`")
    md.append("")

    md.append("## FastAPI Wiring\n")
    md.append(f"- include_router() found: **{len(includes)}**")
    md.append(f"- endpoints found: **{len(endpoints)}**\n")
    if includes:
        md.append("### include_router snippets (first 50)")
        for r in includes[:50]:
            md.append(f"- `{r.file}` → `include_router({r.expr})`")
        md.append("")
    if endpoints:
        md.append("### endpoints (first 100)")
        for e in endpoints[:100]:
            md.append(f"- `{e.file}` → `{e.router}.{e.method}` `{e.path}`")
        md.append("")

    md.append("## RAG-related Candidates (heuristic)\n")
    md.append(f"- Files flagged: **{len(rag)}**\n")
    for p in rag[:80]:
        md.append(f"- `{p}`")
    md.append("")

    md.append("## Training/Modeling Candidates (heuristic)\n")
    md.append(f"- Files flagged: **{len(training)}**\n")
    for p in training[:80]:
        md.append(f"- `{p}`")
    md.append("")

    md.append("## Duplicate Files (identical hash; <=2MB)\n")
    md.append(f"- Groups: **{len(dups)}** (showing top 30)\n")
    for g in dups[:30]:
        md.append(f"### sha256 `{g.sha256}` ({len(g.files)} files)")
        for fp in g.files[:30]:
            md.append(f"- `{fp}`")
        md.append("")
    md.append("")

    md.append("## Python Compile Errors\n")
    md.append(f"- Errors: **{len(compile_errors)}** (showing up to 50)\n")
    for err in compile_errors[:50]:
        md.append(f"- `{err}`")
    md.append("")

    md.append("## Unreferenced Internal Modules (heuristic)\n")
    md.append(f"- Unreferenced: **{len(unref)}** (showing up to 100)\n")
    for p in unref[:100]:
        md.append(f"- `{p}`")
    md.append("")

    md.append("## Notes\n")
    if notes:
        for n in notes:
            md.append(f"- {n}")
    else:
        md.append("- No major notes found.")
    md.append("")

    dt = time.time() - t0
    md.append(f"_Generated in {dt:.2f}s._\n")

    Path("reports/PROJECT_AUDIT.md").write_text("\n".join(md), encoding="utf-8")

    # terminal summary for copy/paste back to chat
    print("\n================ FULL PROJECT AUDIT SUMMARY ================")
    print(f"Root: {audit.root}")
    print(f"Files scanned: {audit.files_scanned} | Python: {audit.py_files}")
    print(f"FastAPI include_router: {len(includes)} | endpoints: {len(endpoints)}")
    print(f"RAG candidates: {len(rag)} | Training candidates: {len(training)}")
    print(f"Duplicate groups: {len(dups)} (<=2MB hashed)")
    print(f"Python compile errors: {len(compile_errors)}")
    print(f"Unreferenced internal modules: {len(unref)} (heuristic)")
    if audit.data_dirs:
        print("Data summary:", ", ".join([f"{k}={v}" for k,v in audit.data_dirs.items()]))
    if audit.missing_expected_data_dirs:
        print("Missing expected dirs:", ", ".join(audit.missing_expected_data_dirs))
    if notes:
        print("Notes:")
        for n in notes:
            print(" -", n)
    print("\nWrote reports:")
    print(" - reports/PROJECT_AUDIT.md")
    print(" - reports/PROJECT_AUDIT.json")
    print("===========================================================\n")

if __name__ == "__main__":
    main()
