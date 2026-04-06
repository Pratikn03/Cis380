#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - local shells may not have PyYAML
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DEFAULT_WAIVERS = ROOT / "quality" / "waivers.yml"
DEFAULT_JSON = REPORTS_DIR / "RELEASE_BAR.json"
DEFAULT_MD = REPORTS_DIR / "RELEASE_BAR.md"
DOCS_STALE_HOURS = 720
REPORT_STALE_HOURS = 720
SMOKE_STALE_HOURS = 72
SMOKE_CANDIDATE_PATTERNS = ("*SMOKE*", "*smoke*", "*runtime*smoke*")


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _ensure_aware(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.timezone.utc)
    return value.astimezone(dt.timezone.utc)


def _parse_timestamp(raw: str) -> dt.datetime | None:
    text = raw.strip()
    if not text:
        return None
    if text.endswith(" UTC"):
        text = text[:-4] + "+00:00"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return dt.datetime.fromisoformat(f"{text}T00:00:00+00:00")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return _ensure_aware(dt.datetime.fromisoformat(text))
    except ValueError:
        return None


def _hours_between(now: dt.datetime, then: dt.datetime | None) -> float:
    if then is None:
        return 0.0
    delta = now - then
    return max(delta.total_seconds() / 3600.0, 0.0)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _report_timestamp(path: Path) -> dt.datetime | None:
    if not path.exists():
        return None

    if path.suffix == ".json":
        payload = _load_json(path)
        for key in ("generated_at", "updated_at"):
            raw = payload.get(key)
            if isinstance(raw, str):
                ts = _parse_timestamp(raw)
                if ts is not None:
                    return ts
        raw_date = payload.get("date")
        if isinstance(raw_date, str):
            ts = _parse_timestamp(raw_date)
            if ts is not None:
                return ts
        return _ensure_aware(dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc))

    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"^# .*?\((\d{4}-\d{2}-\d{2})\)\s*$", text, re.MULTILINE)
    if match:
        ts = _parse_timestamp(match.group(1))
        if ts is not None:
            return ts
    match = re.search(r"^- Generated:\s*(.+)$", text, re.MULTILINE)
    if match:
        ts = _parse_timestamp(match.group(1))
        if ts is not None:
            return ts
    match = re.search(r"^- Date:\s*(\d{4}-\d{2}-\d{2})$", text, re.MULTILINE)
    if match:
        ts = _parse_timestamp(match.group(1))
        if ts is not None:
            return ts
    return _ensure_aware(dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc))


def _freshness_payload(path: Path, now: dt.datetime) -> tuple[str, float, str]:
    ts = _report_timestamp(path)
    if ts is None:
        return str(path), 0.0, now.isoformat()
    return str(path), round(_hours_between(now, ts), 1), ts.isoformat()


def _read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


def _find_training_auth_guard() -> tuple[bool, list[str]]:
    training_router = ROOT / "app" / "api" / "v1" / "training.py"
    text = _read_text_if_exists(training_router)
    if not text:
        return False, [f"missing file: {training_router}"]
    if "dependencies=[Depends(require_auth)]" in text and "APIRouter(" in text:
        return True, []
    return False, ["training API router lacks explicit canonical auth dependency"]


def _find_gateway_auth_contract() -> tuple[bool, list[str]]:
    path = ROOT / "services" / "gateway-kotlin" / "src" / "main" / "kotlin" / "com" / "sentifargo" / "gateway" / "graphql" / "GatewayResolver.kt"
    text = _read_text_if_exists(path)
    signals: list[str] = []

    if not text:
        return False, [f"missing file: {path}"]

    if not re.search(r"private fun requireAuthHeader\(authToken: String\?\): String", text):
        signals.append("missing requireAuthHeader helper")
    if "raw.isNullOrBlank()" not in text or "UNAUTHORIZED" not in text or "Missing authorization token" not in text:
        signals.append("requireAuthHeader does not reject missing/blank tokens as unauthorized")
    for op in ("createUploadSession", "finalizeUpload"):
        start = text.find(f"fun {op}")
        if start == -1:
            signals.append(f"{op} handler missing from GatewayResolver")
            continue
        end = text.find("fun ", start + 1)
        if end == -1:
            end = len(text)
        op_body = text[start:end]
        if f"val authHeader = requireAuthHeader(authToken)" not in op_body:
            signals.append(f"{op} does not consume normalized auth header")

    if "fun login" not in text or "fun refreshToken" not in text:
        signals.append("login/refresh public resolver handlers missing")
    return len(signals) == 0, signals


def _latest_smoke_report(now: dt.datetime) -> Path | None:
    candidates: list[Path] = []
    for pattern in SMOKE_CANDIDATE_PATTERNS:
        candidates.extend(REPORTS_DIR.glob(pattern))
    candidates.extend(REPORTS_DIR.glob("*RUNTIME_RECOVERY*.*"))
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _load_waivers(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Waiver file not found: {path}")
    raw = path.read_text(encoding="utf-8")
    if yaml is not None:
        payload = yaml.safe_load(raw) or {}
    else:
        payload = _parse_minimal_yaml(raw)
    if not isinstance(payload, dict):
        raise SystemExit(f"Invalid waiver file format: {path}")
    return payload


def _coerce_scalar(value: str) -> Any:
    cleaned = value.strip().strip("'").strip('"')
    if cleaned.isdigit():
        return int(cleaned)
    if cleaned.lower() in {"true", "false"}:
        return cleaned.lower() == "true"
    return cleaned


def _parse_minimal_yaml(raw: str) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    current_list: str | None = None
    current_item: dict[str, Any] | None = None

    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and stripped.endswith(":") and ":" not in stripped[:-1]:
            key = stripped[:-1].strip()
            payload[key] = []
            current_list = key
            current_item = None
            continue

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            payload[key.strip()] = _coerce_scalar(value)
            current_list = None
            current_item = None
            continue

        if current_list is not None and stripped.startswith("- "):
            item: dict[str, Any] = {}
            remainder = stripped[2:].strip()
            if remainder and ":" in remainder:
                key, value = remainder.split(":", 1)
                item[key.strip()] = _coerce_scalar(value)
            payload[current_list].append(item)
            current_item = item
            continue

        if current_list is not None and current_item is not None and ":" in stripped:
            key, value = stripped.split(":", 1)
            current_item[key.strip()] = _coerce_scalar(value)

    return payload


def _load_auth_sources() -> tuple[list[str], list[str]]:
    runtime = ROOT / "ui-web" / "next" / "src" / "lib" / "runtime.ts"
    login = ROOT / "ui-web" / "next" / "src" / "app" / "login" / "page.tsx"
    auth_provider = ROOT / "ui-web" / "next" / "src" / "components" / "auth" / "AuthProvider.tsx"
    app_main = ROOT / "app" / "main.py"
    gateway_resolver = ROOT / "services" / "gateway-kotlin" / "src" / "main" / "kotlin" / "com" / "sentifargo" / "gateway" / "graphql" / "GatewayResolver.kt"
    training_router = ROOT / "app" / "api" / "v1" / "training.py"
    paths = [runtime, login, auth_provider, app_main, gateway_resolver, training_router]

    signals: list[str] = []
    app_main_text = _read_text_if_exists(app_main)

    training_ok, training_signals = _find_training_auth_guard()
    gateway_ok, gateway_signals = _find_gateway_auth_contract()
    if not training_ok:
        signals.extend(training_signals)
    if not gateway_ok:
        signals.extend(gateway_signals)
    if 'app.mount("/ui"' in app_main_text and 'ENABLE_LEGACY_RUNTIME", "false"' not in app_main_text:
        signals.append("backend still mounts legacy /ui frontend by default")

    return [str(path) for path in paths if path.exists()], signals


def _load_waiver_summary(path: Path, now: dt.datetime) -> dict[str, Any]:
    payload = _load_waivers(path)
    waivers = payload.get("waivers", [])
    if not isinstance(waivers, list):
        raise SystemExit("Invalid waiver file: 'waivers' must be a list.")

    expired: list[str] = []
    active: list[str] = []
    errors: list[str] = []
    for idx, waiver in enumerate(waivers, start=1):
        if not isinstance(waiver, dict):
            errors.append(f"waiver #{idx}: must be a mapping")
            continue
        module = str(waiver.get("module", "")).strip()
        owner = str(waiver.get("owner", "")).strip()
        reason = str(waiver.get("reason", "")).strip()
        expires_raw = waiver.get("expires_on")
        if not module or not owner or not reason or not expires_raw:
            errors.append(f"waiver #{idx}: missing required fields")
            continue
        try:
            expires_on = dt.date.fromisoformat(str(expires_raw))
        except ValueError:
            errors.append(f"waiver #{idx}: invalid expires_on {expires_raw!r}")
            continue
        if expires_on < now.date():
            expired.append(module)
        else:
            active.append(module)

    return {
        "path": str(path),
        "generated_at": _report_timestamp(path).isoformat() if _report_timestamp(path) else now.isoformat(),
        "freshness_hours": round(_hours_between(now, _report_timestamp(path)), 1),
        "default_threshold": int(payload.get("default_threshold", 95)),
        "max_waiver_days": int(payload.get("max_waiver_days", 28)),
        "active_modules": sorted(active),
        "expired_modules": sorted(expired),
        "errors": errors,
    }


@dataclass
class Pillar:
    status: str
    blocking: bool
    evidence_path: str
    freshness_hours: float
    generated_at: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "status": self.status,
            "blocking": self.blocking,
            "evidence_path": self.evidence_path,
            "freshness_hours": self.freshness_hours,
            "generated_at": self.generated_at,
        }
        payload.update(self.details)
        return payload


def _auth_contract(now: dt.datetime) -> Pillar:
    evidence_files, signals = _load_auth_sources()
    primary = ROOT / "ui-web" / "next" / "src" / "lib" / "runtime.ts"
    _, freshness_hours, generated_at = _freshness_payload(primary, now)
    blocking = bool(signals)
    status = "blocking" if blocking else "pass"
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=", ".join(evidence_files),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "signals": signals,
        },
    )


def _code_quality(now: dt.datetime, waivers_path: Path) -> tuple[Pillar, dict[str, Any]]:
    summary = _load_waiver_summary(waivers_path, now)
    blocking = bool(summary["expired_modules"] or summary["errors"])
    status = "blocking" if blocking else "pass"
    return (
        Pillar(
            status=status,
            blocking=blocking,
            evidence_path=summary["path"],
            freshness_hours=summary["freshness_hours"],
            generated_at=summary["generated_at"],
            details={
                "default_threshold": summary["default_threshold"],
                "max_waiver_days": summary["max_waiver_days"],
                "active_modules": summary["active_modules"],
                "expired_modules": summary["expired_modules"],
                "validation_errors": summary["errors"],
            },
        ),
        summary,
    )


def _artifact_readiness(now: dt.datetime) -> Pillar:
    path = ROOT / "reports" / "ARTIFACT_GATE.json"
    payload = _load_json(path)
    _, freshness_hours, generated_at = _freshness_payload(path, now)
    missing_required = payload.get("missing_required", [])
    blocking = bool(missing_required)
    status = "blocking" if blocking else ("warning" if freshness_hours > REPORT_STALE_HOURS else "pass")
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=str(path),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "required_ok": not blocking,
            "missing_required_count": len(missing_required),
            "missing_optional_count": len(payload.get("missing_optional", [])),
            "strict": bool(payload.get("strict", False)),
        },
    )


def _training_data_readiness(now: dt.datetime) -> Pillar:
    path = ROOT / "reports" / "TRAINING_DATA.json"
    payload = _load_json(path)
    _, freshness_hours, generated_at = _freshness_payload(path, now)
    required = payload.get("required", [])
    blocking = any(item.get("status") != "ok" for item in required if isinstance(item, dict))
    status = "blocking" if blocking else ("warning" if freshness_hours > REPORT_STALE_HOURS else "pass")
    voice_row = next((item for item in required if isinstance(item, dict) and "voice_source" in item), None)
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=str(path),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "required_ok": not blocking,
            "required_count": len(required),
            "voice_source": voice_row.get("voice_source") if isinstance(voice_row, dict) else None,
        },
    )


def _runtime_smoke(now: dt.datetime) -> Pillar:
    path = _latest_smoke_report(now)
    if path is None:
        return Pillar(
            status="blocking",
            blocking=True,
            evidence_path="",
            freshness_hours=float("inf"),
            generated_at=now.isoformat(),
            details={
                "stale": True,
                "signals": ["runtime smoke evidence missing"],
            },
        )

    text = path.read_text(encoding="utf-8", errors="ignore")
    _, freshness_hours, generated_at = _freshness_payload(path, now)
    failed_markers = [
        "INTERNAL_ERROR",
        "backend warning",
        "no new row observed",
        "degraded backend behavior",
    ]
    signals = [marker for marker in failed_markers if marker.lower() in text.lower()]
    stale = freshness_hours > SMOKE_STALE_HOURS
    blocking = stale or bool(signals)
    status = "blocking" if blocking else "pass"
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=str(path),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "stale": stale,
            "signals": signals,
        },
    )


def _docs_quality(now: dt.datetime) -> Pillar:
    path = ROOT / "reports" / "docs_scorecard.json"
    payload = _load_json(path)
    _, freshness_hours, generated_at = _freshness_payload(path, now)
    score = float(payload.get("score", 0))
    threshold = int(payload.get("threshold", 95))
    stale = freshness_hours > DOCS_STALE_HOURS
    blocking = score < threshold
    status = "blocking" if blocking else ("warning" if stale else "pass")
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=str(path),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "score": score,
            "threshold": threshold,
            "stale": stale,
        },
    )


def _production_blockers(now: dt.datetime) -> Pillar:
    plan = ROOT / "docs" / "PRODUCTION_READINESS_PLAN.md"
    compose = ROOT / "docker-compose.production.yml"
    app_main = ROOT / "app" / "main.py"
    plan_text = plan.read_text(encoding="utf-8", errors="ignore") if plan.exists() else ""
    compose_text = compose.read_text(encoding="utf-8", errors="ignore") if compose.exists() else ""
    app_main_text = app_main.read_text(encoding="utf-8", errors="ignore") if app_main.exists() else ""
    _, freshness_hours, generated_at = _freshness_payload(plan, now)
    signals: list[str] = []
    if "Rotate exposed secrets" in plan_text:
        signals.append("Rotate exposed secrets")
    if "Enforce auth globally" in plan_text:
        signals.append("Enforce auth globally")
    if "Bootstrap safety" in plan_text:
        signals.append("Bootstrap safety")
    if 'CORS_ORIGINS=${CORS_ORIGINS:-*}' in compose_text:
        signals.append("CORS must be explicit")
    if 'ALLOWED_HOSTS=${ALLOWED_HOSTS:-}' in compose_text or 'FORCE_HTTPS=${FORCE_HTTPS:-false}' in compose_text:
        signals.append("Allowed hosts & HTTPS")
    if "legacy routes allow unauthenticated access" in plan_text:
        signals.append("legacy routes allow unauthenticated access")
    if 'app.mount("/ui"' in app_main_text and 'ENABLE_LEGACY_RUNTIME", "false"' not in app_main_text:
        signals.append('app.mount("/ui"')
    if "Legacy routers (no authentication required for demo)" in app_main_text:
        signals.append("Legacy routers (no authentication required for demo)")
    blocking = bool(signals)
    status = "blocking" if blocking else "pass"
    return Pillar(
        status=status,
        blocking=blocking,
        evidence_path=str(plan),
        freshness_hours=freshness_hours,
        generated_at=generated_at,
        details={
            "signals": signals,
            "compose_path": str(compose),
            "app_main_path": str(app_main),
        },
    )


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Release Bar",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Release ready: {report['release_ready']}",
        f"- Blocking pillars: {', '.join(report['summary']['blocking_pillars']) or 'none'}",
        f"- Warning pillars: {', '.join(report['summary']['warning_pillars']) or 'none'}",
        "",
        "## Pillars",
        "",
        "| Pillar | Status | Blocking | Freshness (h) | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for name, pillar in report["pillars"].items():
        lines.append(
            f"| {name} | {pillar['status']} | {pillar['blocking']} | {pillar['freshness_hours']} | {pillar['evidence_path']} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
        ]
    )
    for name, pillar in report["pillars"].items():
        lines.append(f"- `{name}` generated_at: {pillar['generated_at']}")
        if pillar.get("details"):
            detail = pillar["details"]
            if detail:
                lines.append(f"  - details: {json.dumps(detail, sort_keys=True)}")
    return "\n".join(lines) + "\n"


def build_release_bar(waivers_path: Path) -> dict[str, Any]:
    now = _utcnow()
    auth = _auth_contract(now)
    code_quality, waiver_summary = _code_quality(now, waivers_path)
    artifact = _artifact_readiness(now)
    training = _training_data_readiness(now)
    smoke = _runtime_smoke(now)
    docs = _docs_quality(now)
    production = _production_blockers(now)

    pillars = {
        "auth_contract": auth.as_dict(),
        "code_quality": code_quality.as_dict(),
        "artifact_readiness": artifact.as_dict(),
        "training_data_readiness": training.as_dict(),
        "runtime_smoke": smoke.as_dict(),
        "docs_quality": docs.as_dict(),
        "production_blockers": production.as_dict(),
    }
    blocking_pillars = [name for name, pillar in pillars.items() if pillar["blocking"]]
    warning_pillars = [name for name, pillar in pillars.items() if pillar["status"] == "warning"]

    report = {
        "generated_at": now.isoformat(),
        "release_ready": not blocking_pillars,
        "summary": {
            "blocking_pillars": blocking_pillars,
            "warning_pillars": warning_pillars,
            "pass_pillars": [name for name, pillar in pillars.items() if pillar["status"] == "pass"],
            "waivers": waiver_summary,
        },
        "pillars": pillars,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the canonical release bar report.")
    parser.add_argument("--waivers", type=Path, default=DEFAULT_WAIVERS, help="Path to quality waivers.")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON, help="Path to write the JSON report.")
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD, help="Path to write the markdown report.")
    args = parser.parse_args()

    report = build_release_bar(args.waivers)

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown.write_text(_render_markdown(report), encoding="utf-8")

    print(json.dumps({"release_ready": report["release_ready"], "blocking_pillars": report["summary"]["blocking_pillars"]}))
    return 0 if report["release_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
