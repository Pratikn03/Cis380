"""Voice emotion classification on uploaded audio."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class VoiceEmotionInput(BaseModel):
    attachment_id: str = Field("audio", description="Attachment key holding the audio bytes.")


class VoiceEmotionOutput(BaseModel):
    emotion: str
    confidence: float
    raw: dict[str, Any]


class VoiceEmotionTool(Tool):
    name = "voice_emotion"
    description = (
        "Classify the speaker's emotion from an uploaded audio clip "
        "(WAV/MP3/FLAC). Returns the top emotion label and confidence."
    )
    input_schema = VoiceEmotionInput
    output_schema = VoiceEmotionOutput
    requires_attachment = "audio"

    def _run(self, ctx: ToolExecutionContext, args: VoiceEmotionInput) -> ToolResult:
        audio_bytes = ctx.attachments.get(args.attachment_id)
        if not audio_bytes:
            raise ToolError(f"no audio bytes at attachment id {args.attachment_id!r}")

        try:
            from app.models.voice.emotion_predict import predict_emotion
        except Exception as exc:
            raise ToolError(f"voice_emotion unavailable: {exc}") from exc

        try:
            raw = predict_emotion(audio_bytes=bytes(audio_bytes))
        except Exception as exc:
            raise ToolError(f"predict_emotion failed: {exc}") from exc

        out = VoiceEmotionOutput(
            emotion=str(raw.get("emotion", "neutral")),
            confidence=float(raw.get("confidence", 0.0)),
            raw=raw,
        )
        return ToolResult(
            summary=f"emotion={out.emotion} confidence={out.confidence:.2f}",
            data=out.model_dump(),
            confidence=out.confidence,
        )
