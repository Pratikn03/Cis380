from __future__ import annotations

import importlib
import importlib.util
import json
import re
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_DIR = ROOT / "reports"
MAX_BYTES = 1_000_000


@dataclass
class Evidence:
    path: Optional[str]
    detail: str


@dataclass
class ClaimResult:
    claim_id: str
    claim: str
    status: str
    evidence: List[Evidence] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def relpath(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path, limit: int = MAX_BYTES) -> str:
    try:
        data = path.read_bytes()
    except Exception:
        return ""
    if len(data) > limit:
        data = data[:limit]
    return data.decode("utf-8", errors="ignore")


def find_lines(path: Path, patterns: Iterable[str], limit: int = 5) -> List[str]:
    text = read_text(path)
    if not text:
        return []
    lines = text.splitlines()
    hits: List[str] = []
    for idx, line in enumerate(lines, 1):
        for pat in patterns:
            if re.search(pat, line):
                hits.append(f"{relpath(path)}:{idx}: {line.strip()}")
                break
        if len(hits) >= limit:
            break
    return hits


def has_pattern(path: Path, pattern: str) -> bool:
    text = read_text(path)
    return bool(text and re.search(pattern, text))


def try_import(module: str) -> Optional[str]:
    try:
        importlib.import_module(module)
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def add_evidence(result: ClaimResult, path: Optional[Path], detail: str) -> None:
    result.evidence.append(Evidence(relpath(path) if path else None, detail))


def claim_orchestrator() -> ClaimResult:
    result = ClaimResult(
        claim_id="C1",
        claim="Orchestrator routes a single request to the right subsystem",
        status="missing",
    )
    orch = ROOT / "app/agent/orchestrator.py"
    chat_api = ROOT / "app/api/chat.py"
    if not orch.exists():
        result.notes.append("Missing app/agent/orchestrator.py")
        return result

    patterns = [
        r"decision_engine\.decide_route",
        r"def _invoke_route",
        r"def _run_rag",
        r"def _run_fraud",
        r"def _run_voice",
        r"def _run_recommend",
    ]
    for hit in find_lines(orch, patterns):
        add_evidence(result, orch, hit)

    if chat_api.exists():
        for hit in find_lines(chat_api, [r"SentifargoOrchestrator", r"\.handle\("]):
            add_evidence(result, chat_api, hit)
    else:
        result.notes.append("Missing app/api/chat.py")

    orch_ok = all(has_pattern(orch, pat) for pat in patterns[:2])
    routes_ok = all(has_pattern(orch, pat) for pat in patterns[2:])
    chat_ok = chat_api.exists() and has_pattern(chat_api, r"SentifargoOrchestrator")

    if orch_ok and routes_ok and chat_ok:
        result.status = "proven"
    else:
        result.status = "partial"

    import_error = try_import("app.agent.orchestrator")
    if import_error:
        result.notes.append(f"Import check failed: app.agent.orchestrator ({import_error})")
    else:
        result.notes.append("Import check: app.agent.orchestrator ok")
    return result


def claim_mlflow_registry() -> ClaimResult:
    result = ClaimResult(
        claim_id="C2",
        claim="MLflow registry patterns",
        status="missing",
    )
    mlflow_utils = ROOT / "src/uais/utils/mlflow_utils.py"
    mlflow_cfg = ROOT / "mlflow_config.yaml"
    registry = ROOT / "app/mlops/registry.py"

    if mlflow_utils.exists():
        for hit in find_lines(
            mlflow_utils, [r"mlflow\.set_tracking_uri", r"mlflow\.set_experiment"]
        ):
            add_evidence(result, mlflow_utils, hit)
    if mlflow_cfg.exists():
        add_evidence(result, mlflow_cfg, "mlflow_config.yaml exists")
    if registry.exists():
        for hit in find_lines(registry, [r"class ModelRegistry", r"def register_model"]):
            add_evidence(result, registry, hit)

    registry_hooks = False
    for path in (ROOT / "app").rglob("*.py"):
        text = read_text(path)
        if "mlflow.register_model" in text or "MlflowClient" in text:
            add_evidence(result, path, f"{relpath(path)}: MLflow registry usage")
            registry_hooks = True
            break

    tracking_ok = mlflow_utils.exists() and has_pattern(mlflow_utils, r"mlflow\.set_tracking_uri")
    registry_ok = registry.exists() and has_pattern(registry, r"class ModelRegistry")
    if tracking_ok and registry_ok:
        result.status = "proven" if registry_hooks else "partial"
    elif tracking_ok or registry_ok:
        result.status = "partial"
    else:
        result.status = "missing"

    spec = importlib.util.find_spec("mlflow")
    if spec is None:
        result.notes.append("mlflow not installed in current environment")
    return result


def claim_dvc() -> ClaimResult:
    result = ClaimResult(
        claim_id="C3",
        claim="DVC implemented",
        status="missing",
    )
    dvc_yaml = ROOT / "dvc.yaml"
    dvc_lock = ROOT / "dvc.lock"

    if dvc_yaml.exists():
        add_evidence(result, dvc_yaml, "dvc.yaml exists")
        for hit in find_lines(dvc_yaml, [r"stages:", r"train_fraud_model", r"evaluate_all"]):
            add_evidence(result, dvc_yaml, hit)
    if dvc_lock.exists():
        add_evidence(result, dvc_lock, "dvc.lock exists")

    if dvc_yaml.exists() and dvc_lock.exists():
        result.status = "proven"
    elif dvc_yaml.exists():
        result.status = "partial"
        result.notes.append("dvc.lock not found; pipeline may be unrun or not tracked")
    else:
        result.status = "missing"
    return result


def claim_offline_first() -> ClaimResult:
    result = ClaimResult(
        claim_id="C4",
        claim="Offline-first",
        status="missing",
    )
    config = ROOT / "app/rag_dsa/config.py"
    online = ROOT / "app/rag_dsa/online.py"
    embed = ROOT / "app/rag_dsa/embeddings.py"
    llm_stub = ROOT / "app/utils/llm_stub.py"

    if config.exists():
        for hit in find_lines(config, [r"DSA_ONLINE_MODE", r"\"false\""]):
            add_evidence(result, config, hit)
    if online.exists():
        for hit in find_lines(online, [r"def online_enabled", r"ONLINE_MODE"]):
            add_evidence(result, online, hit)
    if embed.exists():
        for hit in find_lines(embed, [r"HashingVectorizer", r"Offline-safe"]):
            add_evidence(result, embed, hit)
    if llm_stub.exists():
        add_evidence(result, llm_stub, "offline LLM stub present")

    config_ok = config.exists() and has_pattern(config, r"DSA_ONLINE_MODE")
    online_ok = online.exists() and has_pattern(online, r"online_enabled")
    embed_ok = embed.exists() and has_pattern(embed, r"HashingVectorizer")

    if config_ok and online_ok and embed_ok:
        result.status = "proven"
    elif config_ok or online_ok or embed_ok:
        result.status = "partial"
    else:
        result.status = "missing"
    return result


def claim_prometheus_grafana() -> ClaimResult:
    result = ClaimResult(
        claim_id="C5",
        claim="Prometheus/Grafana",
        status="missing",
    )
    prometheus = ROOT / "deploy/prometheus/prometheus.yml"
    grafana = ROOT / "deploy/grafana/provisioning/datasources/datasource.yml"
    compose = ROOT / "docker-compose.production.yml"
    health = ROOT / "app/core/health.py"

    if prometheus.exists():
        add_evidence(result, prometheus, "prometheus.yml exists")
    if grafana.exists():
        add_evidence(result, grafana, "grafana datasource exists")
    if compose.exists():
        for hit in find_lines(compose, [r"prometheus:", r"grafana:"]):
            add_evidence(result, compose, hit)
    if health.exists():
        for hit in find_lines(health, [r"prometheus_client", r"/metrics", r"prometheus_metrics"]):
            add_evidence(result, health, hit)

    compose_ok = compose.exists() and has_pattern(compose, r"prometheus:")
    metrics_ok = health.exists() and has_pattern(health, r"prometheus_metrics")
    if prometheus.exists() and grafana.exists() and compose_ok and metrics_ok:
        result.status = "proven"
    elif prometheus.exists() or grafana.exists() or compose_ok:
        result.status = "partial"
    else:
        result.status = "missing"
    return result


def claim_fraud_accuracy() -> ClaimResult:
    result = ClaimResult(
        claim_id="C6",
        claim="99.2% fraud accuracy",
        status="missing",
    )
    metrics_candidates = [
        ROOT / "reports/fraud_metrics.json",
        ROOT / "reports/evaluation_summary.json",
        ROOT / "reports/model_comparison.json",
        ROOT / "reports/fraud_metrics.yaml",
        ROOT / "reports/fraud_metrics.csv",
    ]
    found_metric = False
    for path in metrics_candidates:
        if not path.exists():
            continue
        add_evidence(result, path, "metrics file exists")
        if has_pattern(path, r"99\.2|0\.992"):
            add_evidence(result, path, "contains 99.2/0.992")
            found_metric = True

    ui_claims = [
        ROOT / "ui-web/frontend/src/pages/Home.tsx",
        ROOT / "ui-web/frontend/src/pages/CommandCenter.tsx",
        ROOT / "docs/PROJECT_DESCRIPTION.md",
    ]
    for path in ui_claims:
        if path.exists():
            for hit in find_lines(path, [r"99\.2", r"0\.992", r"fraud", r"accuracy"]):
                add_evidence(result, path, hit)

    if found_metric:
        result.status = "proven"
    else:
        result.status = "missing"
        result.notes.append("No metrics artifact with 99.2/0.992 found in reports")
        result.notes.append("Claim appears in UI/docs copy; consider linking to a metrics file")
    return result


def render_markdown(results: List[ClaimResult]) -> str:
    lines: List[str] = []
    lines.append("# Claim Evidence Report")
    lines.append("")
    lines.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    for res in results:
        lines.append(f"## {res.claim_id}. {res.claim}")
        lines.append("")
        lines.append(f"- Status: {res.status.upper()}")
        if res.evidence:
            lines.append("- Evidence:")
            for ev in res.evidence:
                if ev.path:
                    lines.append(f"  - {ev.path} - {ev.detail}")
                else:
                    lines.append(f"  - {ev.detail}")
        if res.notes:
            lines.append("- Notes:")
            for note in res.notes:
                lines.append(f"  - {note}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    results = [
        claim_orchestrator(),
        claim_mlflow_registry(),
        claim_dvc(),
        claim_offline_first(),
        claim_prometheus_grafana(),
        claim_fraud_accuracy(),
    ]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "CLAIM_EVIDENCE.json").write_text(
        json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8"
    )
    (REPORT_DIR / "CLAIM_EVIDENCE.md").write_text(render_markdown(results), encoding="utf-8")

    print("Claim evidence report written:")
    print(f"- {relpath(REPORT_DIR / 'CLAIM_EVIDENCE.md')}")
    print(f"- {relpath(REPORT_DIR / 'CLAIM_EVIDENCE.json')}")


if __name__ == "__main__":
    main()
