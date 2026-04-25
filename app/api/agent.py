from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.models import Incident
from app.services.audit import record_audit

router = APIRouter(prefix="/agent", tags=["agent"])


class EscalationRequest(BaseModel):
    message: str
    route: str = "agent"
    severity: str = "medium"
    evidence: dict[str, Any] = {}
    user_id: str = "web_user"


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _read_upload(file: UploadFile | None, max_bytes: int) -> bytes | None:
    if file is None:
        return None
    content = await file.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail=f"{file.filename or 'upload'} is too large")
    return content


@router.post("/stream")
async def agent_stream(
    message: str = Form(""),
    user_id: str = Form("web_user"),
    use_rag: bool = Form(True),
    image: UploadFile | None = File(default=None),
    audio: UploadFile | None = File(default=None),
    video: UploadFile | None = File(default=None),
    document: UploadFile | None = File(default=None),
) -> StreamingResponse:
    async def events():
        try:
            text = (message or "").strip()
            attachments: dict[str, Any] = {}
            upload_steps: list[dict[str, Any]] = []

            image_bytes = await _read_upload(image, 10 * 1024 * 1024)
            if image_bytes is not None:
                attachments["image"] = image_bytes
                upload_steps.append(
                    {"tool": "vision", "filename": image.filename, "status": "queued"}
                )

            audio_bytes = await _read_upload(audio, 25 * 1024 * 1024)
            if audio_bytes is not None:
                attachments["audio"] = audio_bytes
                upload_steps.append(
                    {"tool": "voice", "filename": audio.filename, "status": "queued"}
                )

            video_bytes = await _read_upload(video, 100 * 1024 * 1024)
            if video_bytes is not None:
                attachments["video"] = {"filename": video.filename, "bytes": len(video_bytes)}
                upload_steps.append(
                    {"tool": "video", "filename": video.filename, "status": "queued"}
                )

            doc_bytes = await _read_upload(document, 10 * 1024 * 1024)
            if doc_bytes is not None:
                attachments["document"] = {"filename": document.filename, "bytes": len(doc_bytes)}
                upload_steps.append(
                    {"tool": "rag", "filename": document.filename, "status": "queued"}
                )
                if not text:
                    text = f"Summarize uploaded document {document.filename or 'document'}."

            if not text:
                raise HTTPException(status_code=400, detail="Message or upload is required.")

            yield _sse("step", {"label": "Classifying intent", "status": "running"})
            for step in upload_steps:
                yield _sse("step", step)

            from app.api.chat import _get_orchestrator

            yield _sse("step", {"label": "Running agent route", "status": "running"})
            result = _get_orchestrator().handle(
                text,
                user_id=user_id,
                use_rag=use_rag,
                attachments=attachments or None,
            )
            answer = str(result.get("answer") or result.get("reply") or "")
            for token in answer.split():
                yield _sse("token", {"text": token + " "})

            meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
            citations = meta.get("citations") or meta.get("sources") or meta.get("chunks") or []
            if isinstance(citations, list):
                for citation in citations[:8]:
                    yield _sse("citation", {"citation": citation})

            yield _sse("final", {"result": result})
        except HTTPException as exc:
            yield _sse("error", {"detail": exc.detail, "status": exc.status_code})
        except Exception as exc:  # pragma: no cover - runtime integration path
            yield _sse("error", {"detail": str(exc), "status": 500})

    return StreamingResponse(events(), media_type="text/event-stream")


@router.post("/escalate")
def escalate(payload: EscalationRequest) -> dict[str, Any]:
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        incident = Incident(
            incident_type=payload.route,
            severity=payload.severity,
            description=payload.message,
            evidence=payload.evidence,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        record_audit(
            db,
            action="agent_escalation",
            target=incident.id,
            user_id=payload.user_id,
            meta={"route": payload.route, "severity": payload.severity},
        )
        return {"id": incident.id, "status": "escalated", "severity": incident.severity}
