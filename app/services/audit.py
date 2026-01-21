from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.db.models import AuditLog

import json
from pathlib import Path

LOG_DIR = Path("logs/audit")


def record_audit(
    db: Session,
    action: str,
    target: str = "",
    user_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(user_id=user_id, action=action, target=target, meta=meta or {})
    db.add(entry)
    db.commit()
    db.refresh(entry)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "user_id": user_id,
        "action": action,
        "target": target,
        "meta": meta or {},
        "created_at": entry.created_at.isoformat(),
    }
    with (LOG_DIR / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return entry
