"""Versioned prompt registry + deterministic A/B routing.

Prompts live in ``app/agent/prompts/<id>.md``. The registry loads them
lazily on first access and caches by id. The planner picks a variant for
each session by hashing ``session_id`` against the configured split
ratio — same session always lands on the same variant, so the planner's
prompt cache stays warm and the eval harness's per-domain pass rates
stay comparable.

Configuration (``.env`` / ``app/core/config.py::AgentSettings``):

  AGENT_PROMPT_VARIANT=planner_v1     # canonical default
  AGENT_PROMPT_AB_VARIANT=planner_v2  # optional B variant
  AGENT_PROMPT_AB_SPLIT=0.1           # 10 % traffic to B

Pick the active variant for a request:

    from app.agent.prompts import pick_variant
    variant_id, body = pick_variant(session_id="sess_xyz")
"""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_log = logging.getLogger("Sentifargo.agent.prompts")
_PROMPT_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class PromptVariant:
    id: str
    body: str


def _read_prompt(prompt_id: str) -> str:
    path = _PROMPT_DIR / f"{prompt_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt {prompt_id!r} not found at {path}")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=64)
def get_prompt(prompt_id: str) -> PromptVariant:
    """Return a prompt by id (cached)."""
    body = _read_prompt(prompt_id)
    return PromptVariant(id=prompt_id, body=body)


def _bucket(session_id: str) -> float:
    """Stable per-session float in [0, 1)."""
    digest = hashlib.sha256(session_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") / 0xFFFFFFFF


def pick_variant(session_id: str | None = None) -> PromptVariant:
    """Pick the active planner prompt for a session.

    Order of precedence:
      1. ``AGENT_PROMPT_FORCE`` env: forces a variant id (used by tests).
      2. ``AGENT_PROMPT_AB_VARIANT`` + ``AGENT_PROMPT_AB_SPLIT``: stable
         per-session split between the canonical and B variant.
      3. ``AGENT_PROMPT_VARIANT``: the canonical default.
    """
    forced = os.getenv("AGENT_PROMPT_FORCE", "").strip()
    if forced:
        return get_prompt(forced)

    primary = os.getenv("AGENT_PROMPT_VARIANT", "planner_v1").strip() or "planner_v1"
    b_variant = os.getenv("AGENT_PROMPT_AB_VARIANT", "").strip()
    try:
        split = float(os.getenv("AGENT_PROMPT_AB_SPLIT", "0") or "0")
    except ValueError:
        split = 0.0

    if b_variant and 0.0 < split <= 1.0 and session_id:
        if _bucket(session_id) < split:
            try:
                return get_prompt(b_variant)
            except FileNotFoundError:
                _log.warning("AB variant %s missing; falling back to %s", b_variant, primary)

    return get_prompt(primary)


__all__ = ["PromptVariant", "get_prompt", "pick_variant"]
