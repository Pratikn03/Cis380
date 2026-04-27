"""Speech-to-text transcription."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class TranscribeInput(BaseModel):
    attachment_id: str = Field("audio", description="Attachment key holding the audio bytes.")
    language: str = Field(
        "auto", description="ISO language code or 'auto' to detect."
    )


class TranscribeOutput(BaseModel):
    text: str
    language: str
    raw: dict[str, Any]


class TranscribeTool(Tool):
    name = "transcribe"
    description = (
        "Transcribe an uploaded audio clip to text. Use before tools that need "
        "the spoken content as text (e.g. searching the corpus for what was "
        "said)."
    )
    input_schema = TranscribeInput
    output_schema = TranscribeOutput
    requires_attachment = "audio"

    def _run(self, ctx: ToolExecutionContext, args: TranscribeInput) -> ToolResult:
        audio_bytes = ctx.attachments.get(args.attachment_id)
        if not audio_bytes:
            raise ToolError(f"no audio bytes at attachment id {args.attachment_id!r}")

        # Prefer faster-whisper if vendored, else fall back to a stubbed empty
        # transcription so the tool stays best-effort offline.
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except Exception:
            return ToolResult(
                summary="transcribe unavailable (faster_whisper not installed)",
                data=TranscribeOutput(text="", language=args.language, raw={}).model_dump(),
            )

        import io
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
            fh.write(bytes(audio_bytes))
            tmp_path = fh.name

        try:
            model_size = os.getenv("WHISPER_MODEL", "base")
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
            language = None if args.language == "auto" else args.language
            segments, info = model.transcribe(tmp_path, language=language)
            text = "".join(seg.text for seg in segments).strip()
            out = TranscribeOutput(
                text=text,
                language=getattr(info, "language", args.language) or args.language,
                raw={"duration": getattr(info, "duration", None)},
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return ToolResult(
            summary=f"transcribed {len(out.text)} chars (lang={out.language})",
            data=out.model_dump(),
        )
