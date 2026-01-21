from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict

from app.rag.config import settings


def log_event(event: Dict[str, Any]) -> None:
    settings.logs_path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(event)
    payload["ts"] = time.time()
    with settings.logs_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
