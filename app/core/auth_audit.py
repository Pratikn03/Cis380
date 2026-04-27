"""Helper for inserting auth_audit rows from auth handlers.

Intentionally best-effort: a DB outage during, say, login should not
cascade into the user's request failing. We log the failure and move on.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

_log = logging.getLogger("Sentifargo.auth_audit")


def log_auth_event(
    *,
    event_type: str,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    """Insert one row into auth_audit. Drop-and-log on errors."""
    try:
        from app.db.models import AuthAudit
        from app.db.session import SessionLocal
    except Exception as exc:
        _log.debug("auth_audit unavailable (db not configured): %s", exc)
        return

    try:
        with SessionLocal() as session:
            row = AuthAudit(
                user_id=user_id,
                username=username,
                event_type=event_type,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata_json=metadata or None,
            )
            session.add(row)
            session.commit()
    except Exception as exc:
        _log.warning("auth_audit insert failed (event=%s): %s", event_type, exc)


__all__ = ["log_auth_event"]
