import asyncio
import os
import requests
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import model_validator

from ...agent.orchestrator import SentifargoOrchestrator
from ..deps import check_token_query, require_auth

router = APIRouter(prefix="/api/chat", tags=["chat"], dependencies=[Depends(require_auth)])
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


class ChatRequest(BaseModel):
    # Backward compatible: Streamlit sends {"message": "..."}; tests/other clients may send {"text": "..."}.
    message: str | None = None
    text: str | None = None
    user_id: str = "anon"
    use_rag: bool = True

    @model_validator(mode="after")
    def _validate_text(self):
        if not (self.message or self.text):
            raise ValueError("Provide 'message' or 'text'.")
        return self

    def resolved_text(self) -> str:
        return (self.message or self.text or "").strip()


@lru_cache(maxsize=1)
def _get_agent() -> SentifargoOrchestrator:
    return SentifargoOrchestrator()


@router.post("")
def chat(req: ChatRequest):
    out = _get_agent().handle(
        req.resolved_text(), user_id=req.user_id, use_rag=req.use_rag, attachments=None
    )
    # Keep "reply" for UI compatibility; expose structured fields for agent/module debugging.
    out["reply"] = out.get("answer", "")
    return out


@router.post("/multimodal")
async def chat_multimodal(
    message: str = Form(""),
    instruction: str = Form(""),
    user_id: str = Form("anon"),
    use_rag: bool = Form(True),
    audio: UploadFile | None = File(default=None),
    image: UploadFile | None = File(default=None),
    video: UploadFile | None = File(default=None),
    fps: float = Form(1.0),
    max_frames: int = Form(25),
    transcribe_audio: bool = Form(False),
    stt_language: str | None = Form(default=None),
):
    """Single request: optional audio/image/video + message -> routed response + meta.

    This endpoint runs in-process inference for voice/vision and attaches results to `meta`.
    """
    attachments: dict[str, object] = {}
    context_lines: list[str] = []
    base_message = (message or "").strip()
    instruction_text = (instruction or "").strip()
    audio_bytes: bytes | None = None

    if audio is not None:
        try:
            from app.models.voice.emotion_predict import predict_emotion

            audio_bytes = await audio.read()
            voice = predict_emotion(audio_bytes=audio_bytes, filename=audio.filename)
            voice_summary = {
                "emotion": voice.get("emotion"),
                "confidence": voice.get("confidence"),
                "supported_emotions": voice.get("supported_emotions"),
                "model_emotions": voice.get("model_emotions"),
                "missing_emotions": voice.get("missing_emotions"),
            }
            attachments["voice"] = voice_summary
            if voice_summary.get("emotion") is not None:
                context_lines.append(
                    f"[voice] emotion={voice_summary.get('emotion')} confidence={voice_summary.get('confidence')}"
                )
        except Exception as exc:
            attachments["voice_error"] = str(exc)

    # Optional: speech-to-text to drive the chat message from mic audio.
    want_stt = bool(transcribe_audio) or (audio is not None and not base_message)
    if want_stt and audio_bytes is not None:
        try:
            from app.services.stt.whisper_stt import WhisperSTT  # type: ignore

            suffix = ".wav"
            if audio.filename:
                try:
                    from pathlib import Path

                    suf = Path(audio.filename).suffix.lower()
                    if suf:
                        suffix = suf
                except Exception:
                    pass
            stt = WhisperSTT.transcribe_bytes(audio_bytes, suffix=suffix, language=stt_language)
            stt_text = str(stt.get("text") or "").strip()
            attachments["stt"] = stt
            if stt_text:
                context_lines.append(f"[speech] {stt_text}")
                if not base_message:
                    base_message = stt_text
        except ModuleNotFoundError:
            attachments["stt_error"] = (
                "Speech-to-text unavailable: install `faster-whisper` to enable live voice chat."
            )
        except Exception as exc:
            attachments["stt_error"] = str(exc)

    if image is not None:
        try:
            from .vision import vision_predict

            image_bytes = await image.read()
            try:
                image.file.seek(0)  # type: ignore[attr-defined]
            except Exception:
                pass
            try:
                import io

                from PIL import Image

                from app.streamlit_chatbot.image_tags import extract_tags_from_image

                image_obj = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                tags = extract_tags_from_image(image_obj, top_k=5)
                if tags:
                    attachments["image_tags"] = tags
                    context_lines.append(f"[image_tags] {', '.join(tags)}")
            except Exception as exc:
                attachments["image_tags_error"] = str(exc)
            vision_res = await vision_predict(file=image, top_k=3)
            vision_summary = {
                "label": vision_res.get("label"),
                "confidence": vision_res.get("confidence"),
                "top_k": vision_res.get("top_k"),
            }
            attachments["vision_image"] = vision_summary
            if vision_summary.get("label") is not None:
                context_lines.append(
                    f"[vision] label={vision_summary.get('label')} confidence={vision_summary.get('confidence')}"
                )

            # Optional face emotion classifier (requires trained artifact).
            try:
                from app.models.vision.face_emotion_predict import (
                    FaceEmotionModelNotTrainedError,
                    predict_face_emotion,
                )

                face_res = predict_face_emotion(
                    image_bytes=image_bytes,
                    filename=image.filename,
                    top_k=3,
                )
                face_summary = {
                    "emotion": face_res.get("emotion"),
                    "confidence": face_res.get("confidence"),
                    "top_k": face_res.get("top_k"),
                }
                attachments["face_emotion"] = face_summary
                if face_summary.get("emotion") is not None:
                    context_lines.append(
                        f"[face] emotion={face_summary.get('emotion')} confidence={face_summary.get('confidence')}"
                    )
            except FaceEmotionModelNotTrainedError as exc:
                attachments["face_emotion_error"] = str(exc)
            except Exception as exc:
                attachments["face_emotion_error"] = str(exc)
        except Exception as exc:
            attachments["vision_image_error"] = str(exc)

    if video is not None:
        try:
            from .vision import vision_video_predict

            video_res = await vision_video_predict(
                file=video, fps=float(fps), max_frames=int(max_frames), top_k=3
            )
            temporal = video_res.get("temporal") or {}
            vision_summary = {
                "label": video_res.get("label"),
                "confidence": video_res.get("confidence"),
                "temporal_confidence_model": video_res.get("temporal_confidence_model"),
                "frames_used": video_res.get("frames_used"),
                "fps": video_res.get("fps"),
                "temporal": {
                    "label_flip_rate": temporal.get("label_flip_rate"),
                    "prob_entropy": (
                        temporal.get("prob_entropy", {}).get("mean")
                        if isinstance(temporal, dict)
                        else None
                    ),
                    "anomaly_score_heuristic": temporal.get("anomaly_score_heuristic"),
                    "notes": temporal.get("notes"),
                },
            }
            attachments["vision_video"] = vision_summary
            if vision_summary.get("label") is not None:
                context_lines.append(
                    f"[vision] label={vision_summary.get('label')} confidence={vision_summary.get('confidence')} (video)"
                )
        except Exception as exc:
            attachments["vision_video_error"] = str(exc)

    if not base_message:
        raise HTTPException(
            status_code=400,
            detail="Empty message. Provide `message` text or enable STT by attaching audio with `transcribe_audio=true`.",
        )

    full_message = base_message
    if context_lines:
        full_message += "\n\nContext:\n" + "\n".join(context_lines)
    if instruction_text:
        full_message += "\n\nInstruction:\n" + instruction_text

    out = _get_agent().handle(
        full_message, user_id=user_id, use_rag=use_rag, attachments=attachments or None
    )
    out["reply"] = out.get("answer", "")

    # Expose attachments at top-level meta for convenience.
    if isinstance(out.get("meta"), dict) and attachments:
        out["meta"]["attachments"] = attachments
    return out


@router.get("/stream")
async def chat_stream(message: str, token: str | None = None):
    """SSE-style streaming endpoint.

    If OPENAI_API_KEY is set, streams LLM tokens from OpenAI.
    Otherwise, falls back to word-chunk streaming of orchestrator reply.
    """
    check_token_query(token)

    async def event_gen_llm():
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
        payload = {
            "model": "gpt-3.5-turbo",  # adjust here if you change providers/models
            "stream": True,
            "messages": [{"role": "user", "content": message}],
        }
        # simple retry/backoff for 429
        for attempt in range(3):
            try:
                with requests.post(
                    url, headers=headers, json=payload, stream=True, timeout=30
                ) as resp:
                    if resp.status_code == 429 and attempt < 2:
                        await asyncio.sleep(2**attempt)  # backoff
                        continue
                    resp.raise_for_status()
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if data == "[DONE]":
                            yield "data: [DONE]\\n\\n"
                            return
                        try:
                            chunk = requests.compat.json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content")
                            if delta:
                                yield f"data: {delta}\\n\\n"
                        except Exception:
                            continue
                break
            except requests.HTTPError as exc:
                if resp.status_code == 429 and attempt < 2:
                    await asyncio.sleep(2**attempt)
                    continue
                yield f"data: [ERROR] {exc}\\n\\n"
                return

    async def event_gen_fallback():
        try:
            reply = (
                _get_agent()
                .handle(message, user_id="anon", use_rag=True, attachments=None)
                .get("answer", "")
            )
            for word in reply.split():
                yield f"data: {word}\\n\\n"
                await asyncio.sleep(0.01)
            yield "data: [DONE]\\n\\n"
        except Exception as exc:
            yield f"data: [ERROR] {exc}\\n\\n"

    gen = event_gen_llm() if OPENAI_KEY else event_gen_fallback()
    return StreamingResponse(gen, media_type="text/event-stream")
