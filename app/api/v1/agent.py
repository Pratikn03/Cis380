"""Agent SSE endpoint.

POST /api/v1/agent/run     — accepts JSON or multipart (with file uploads) and
                              streams agent events as SSE.
GET  /api/v1/agent/trace/{trace_id} — returns the audit trail for a turn.
GET  /api/v1/agent/tools   — returns the tool catalogue (for the frontend).
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Iterator, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agent.audit_logger import get_audit_logger
from app.agent.multi_agent import get_multi_agent
from app.agent.tools import ALL_TOOLS
from app.core.auth import require_roles

router = APIRouter(prefix="/agent", tags=["agent"])

# RBAC dependencies
RunAccess = Depends(require_roles("admin", "analyst"))
TraceAccess = Depends(require_roles("admin"))
ToolsAccess = Depends(require_roles("admin", "analyst", "viewer"))
_log = logging.getLogger("Sentifargo.api.agent")


class AgentRunRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message.")
    session_id: Optional[str] = Field(None, description="Conversation id; auto-generated if absent.")
    user_id: str = Field("anon", description="User identifier.")


def _serialise_event(event: dict) -> str:
    """Convert an event dict to a single SSE frame.

    The frontend EventSource API splits events on blank lines.
    ``event:<type>\ndata:<json>\n\n``
    """
    event_type = event.get("type", "message")
    # Drop non-serialisable PlannerResult dataclass if it slipped through.
    safe_event = {k: v for k, v in event.items() if k != "type"}
    try:
        payload = json.dumps(safe_event, default=str)
    except (TypeError, ValueError):
        payload = json.dumps({"error": "non_serialisable_event"})
    return f"event: {event_type}\ndata: {payload}\n\n"


def _stream_events(
    message: str, user_id: str, session_id: Optional[str], attachments: dict[str, bytes]
) -> Iterator[bytes]:
    orch = get_multi_agent()
    try:
        for event in orch.stream(
            text=message,
            user_id=user_id,
            session_id=session_id,
            attachments=attachments or None,
        ):
            yield _serialise_event(event).encode("utf-8")
    except Exception as exc:
        _log.exception("agent stream failed")
        yield _serialise_event({"type": "error", "message": str(exc)}).encode("utf-8")


@router.post("/run", dependencies=[RunAccess])
async def agent_run(
    message: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    payload: Optional[AgentRunRequest] = None,  # pydantic JSON body alt
):
    """Run the agent. Accepts JSON or multipart with optional file uploads.

    Streams server-sent events; consume via ``new EventSource(...)`` on the
    frontend.
    """
    # Resolve message/user/session from whichever input mode is in play.
    if payload is not None:
        message = message or payload.message
        session_id = session_id or payload.session_id
        user_id = user_id or payload.user_id

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    attachments: dict[str, bytes] = {}
    for key, upload in (("image", image), ("audio", audio), ("video", video)):
        if upload is not None:
            data = await upload.read()
            if data:
                attachments[key] = data

    return StreamingResponse(
        _stream_events(
            message=message,
            user_id=user_id or "anon",
            session_id=session_id,
            attachments=attachments,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering
        },
    )


@router.get("/trace/{trace_id}", dependencies=[TraceAccess])
def agent_trace(trace_id: str):
    """Return all audit entries for a single agent turn."""
    audit = get_audit_logger()
    entries = audit.get_trace(trace_id)
    if not entries:
        raise HTTPException(status_code=404, detail="trace not found")
    return {"trace_id": trace_id, "entries": entries}


@router.get("/tools", dependencies=[ToolsAccess])
def agent_tools():
    """Tool catalogue with input schemas, for the frontend to render."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "requires_attachment": tool.requires_attachment,
                "input_schema": tool.to_anthropic_schema()["input_schema"],
            }
            for tool in ALL_TOOLS
        ]
    }
