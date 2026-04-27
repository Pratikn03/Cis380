"""Generic image analysis (deepfake / scene labelling)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class VisionAnalyzeInput(BaseModel):
    attachment_id: str = Field(
        "image", description="Attachment key holding the image bytes (default: 'image')."
    )


class VisionAnalyzeOutput(BaseModel):
    label: str
    confidence: float
    raw: dict[str, Any]


class VisionAnalyzeTool(Tool):
    name = "vision_analyze"
    description = (
        "Run scene/deepfake/object analysis on an uploaded image. The image must "
        "be uploaded with the request and referenced by its attachment id "
        "(usually 'image'). Returns the top label and confidence."
    )
    input_schema = VisionAnalyzeInput
    output_schema = VisionAnalyzeOutput
    requires_attachment = "image"

    def _run(self, ctx: ToolExecutionContext, args: VisionAnalyzeInput) -> ToolResult:
        image_bytes = ctx.attachments.get(args.attachment_id)
        if not image_bytes:
            raise ToolError(f"no image bytes at attachment id {args.attachment_id!r}")

        try:
            from app.vision_local.analyze import analyze_image_bytes
        except Exception as exc:
            raise ToolError(f"vision_analyze unavailable: {exc}") from exc

        try:
            raw = analyze_image_bytes(bytes(image_bytes))
        except Exception as exc:
            raise ToolError(f"analyze_image_bytes failed: {exc}") from exc

        out = VisionAnalyzeOutput(
            label=str(raw.get("label", "unknown")),
            confidence=float(raw.get("confidence", 0.0)),
            raw=raw,
        )
        return ToolResult(
            summary=f"label={out.label} confidence={out.confidence:.2f}",
            data=out.model_dump(),
            confidence=out.confidence,
        )
