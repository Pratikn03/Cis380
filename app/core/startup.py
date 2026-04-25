from __future__ import annotations

import os
from collections.abc import Callable
from logging import Logger
from typing import Any


def initialize_dev_database(
    *,
    app_env: str,
    ensure_schema_fn: Callable[[], None],
    logger: Logger,
) -> None:
    """Best-effort table initialization for non-production environments."""
    if app_env == "production":
        return
    if os.getenv("AUTO_INIT_DB", "true").lower() != "true":
        return
    try:
        ensure_schema_fn()
    except Exception as exc:  # pragma: no cover
        logger.warning("Database auto-init skipped: %s", exc)


def bootstrap_credentials(*, app_env: str, logger: Logger) -> tuple[str | None, str | None]:
    if app_env == "production":
        return None, None

    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")
    if username and password:
        return username, password

    if app_env in {"development", "test"}:
        default_user = os.getenv("DEV_ADMIN_USERNAME", "admin")
        default_password = os.getenv("DEV_ADMIN_PASSWORD", "admin123")
        logger.info(
            "Using dev/test default bootstrap admin credentials (set ADMIN_USERNAME/ADMIN_PASSWORD to override)."
        )
        return default_user, default_password

    return None, None


def bootstrap_admin_user(
    *,
    app_env: str,
    ensure_schema_fn: Callable[[], None],
    session_factory: Callable[[], Any],
    bootstrap_roles_fn: Callable[[Any], Any],
    bootstrap_admin_fn: Callable[[Any, str, str], Any],
    logger: Logger,
) -> None:
    initialize_dev_database(app_env=app_env, ensure_schema_fn=ensure_schema_fn, logger=logger)

    admin_username, admin_password = bootstrap_credentials(app_env=app_env, logger=logger)
    if not admin_username or not admin_password:
        return

    try:
        with session_factory() as db:
            bootstrap_roles_fn(db)
            bootstrap_admin_fn(db, admin_username, admin_password)
    except Exception as exc:  # pragma: no cover
        logger.warning("Admin bootstrap skipped: %s", exc)
