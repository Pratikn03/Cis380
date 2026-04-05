"""Legacy compatibility wrapper for the shared auth dependency."""

from app.core.auth import check_token_query, require_auth


__all__ = ["check_token_query", "require_auth"]
