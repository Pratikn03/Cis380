#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised in local shells without PyYAML
    yaml = None


REQUIRED_WAIVER_FIELDS = {
    "module",
    "owner",
    "reason",
    "expires_on",
    "temporary_threshold",
}


def _load_waiver_file(path: Path) -> dict[str, Any]:
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


def _validate(payload: dict[str, Any], now: dt.date) -> tuple[int, int, dict[str, int]]:
    default_threshold = int(payload.get("default_threshold", 95))
    max_waiver_days = int(payload.get("max_waiver_days", 28))
    waivers = payload.get("waivers", [])
    if not isinstance(waivers, list):
        raise SystemExit("Invalid waiver file: 'waivers' must be a list.")

    thresholds: dict[str, int] = {}
    errors: list[str] = []

    for idx, waiver in enumerate(waivers, start=1):
        if not isinstance(waiver, dict):
            errors.append(f"waiver #{idx}: must be a mapping")
            continue

        missing = REQUIRED_WAIVER_FIELDS - set(waiver.keys())
        if missing:
            errors.append(f"waiver #{idx}: missing fields: {', '.join(sorted(missing))}")
            continue

        module = str(waiver["module"]).strip()
        owner = str(waiver["owner"]).strip()
        reason = str(waiver["reason"]).strip()

        if not module:
            errors.append(f"waiver #{idx}: module is empty")
        if not owner:
            errors.append(f"waiver #{idx}: owner is empty")
        if not reason:
            errors.append(f"waiver #{idx}: reason is empty")

        try:
            expires_on = dt.date.fromisoformat(str(waiver["expires_on"]))
        except ValueError:
            errors.append(
                f"waiver #{idx}: expires_on must be ISO date (YYYY-MM-DD), got {waiver['expires_on']!r}"
            )
            continue

        delta = (expires_on - now).days
        if delta < 0:
            errors.append(f"waiver #{idx}: expired on {expires_on.isoformat()}")
        if delta > max_waiver_days:
            errors.append(
                f"waiver #{idx}: expires_on exceeds max_waiver_days={max_waiver_days} "
                f"({expires_on.isoformat()})"
            )

        try:
            temporary_threshold = int(waiver["temporary_threshold"])
        except (TypeError, ValueError):
            errors.append(f"waiver #{idx}: temporary_threshold must be an integer")
            continue

        if temporary_threshold <= 0:
            errors.append(f"waiver #{idx}: temporary_threshold must be > 0")
        if temporary_threshold > default_threshold:
            errors.append(
                f"waiver #{idx}: temporary_threshold ({temporary_threshold}) exceeds default_threshold ({default_threshold})"
            )

        if module in thresholds:
            errors.append(f"waiver #{idx}: duplicate module '{module}'")
        thresholds[module] = temporary_threshold

    if errors:
        joined = "\n".join(f"- {e}" for e in errors)
        raise SystemExit(f"Waiver validation failed:\n{joined}")

    return default_threshold, max_waiver_days, thresholds


def _threshold_for_module(payload: dict[str, Any], module: str, now: dt.date) -> int:
    default_threshold, _, thresholds = _validate(payload, now)
    return int(thresholds.get(module, default_threshold))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and resolve quality gate thresholds.")
    sub = parser.add_subparsers(dest="command", required=True)
    check_parser = sub.add_parser(
        "check", help="Validate waiver file and print resolved thresholds."
    )
    check_parser.add_argument(
        "--waivers",
        default="quality/waivers.yml",
        help="Path to waiver file.",
    )
    check_parser.add_argument(
        "--no-active",
        action="store_true",
        help="Fail if any active waiver is present.",
    )

    threshold_parser = sub.add_parser("threshold", help="Get threshold for a module.")
    threshold_parser.add_argument(
        "--waivers",
        default="quality/waivers.yml",
        help="Path to waiver file.",
    )
    threshold_parser.add_argument("--module", required=True, help="Module key.")

    dump_parser = sub.add_parser("dump-json", help="Emit resolved threshold map as JSON.")
    dump_parser.add_argument(
        "--waivers",
        default="quality/waivers.yml",
        help="Path to waiver file.",
    )

    args = parser.parse_args()
    now = dt.date.today()
    payload = _load_waiver_file(Path(args.waivers))

    if args.command == "check":
        default_threshold, max_waiver_days, thresholds = _validate(payload, now)
        if args.no_active and thresholds:
            modules = ", ".join(sorted(thresholds))
            raise SystemExit(f"Active quality waivers are not allowed: {modules}")
        print(
            json.dumps(
                {
                    "status": "ok",
                    "date": now.isoformat(),
                    "default_threshold": default_threshold,
                    "max_waiver_days": max_waiver_days,
                    "waiver_modules": sorted(thresholds.keys()),
                }
            )
        )
        return 0

    if args.command == "threshold":
        print(_threshold_for_module(payload, args.module, now))
        return 0

    if args.command == "dump-json":
        default_threshold, max_waiver_days, thresholds = _validate(payload, now)
        print(
            json.dumps(
                {
                    "default_threshold": default_threshold,
                    "max_waiver_days": max_waiver_days,
                    "thresholds": thresholds,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
