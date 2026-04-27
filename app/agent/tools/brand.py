"""Brand-logo detection on uploaded images."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class BrandDetectInput(BaseModel):
    attachment_id: str = Field("image", description="Attachment key holding the image bytes.")
    confidence: float = Field(0.25, ge=0.0, le=1.0, description="Detection confidence threshold.")


class BrandDetectOutput(BaseModel):
    brands: list[str]
    detections: list[dict[str, Any]]


class BrandDetectTool(Tool):
    name = "brand_detect"
    description = (
        "Detect brand logos in an uploaded image. Returns the unique brands "
        "found and per-detection bounding boxes."
    )
    input_schema = BrandDetectInput
    output_schema = BrandDetectOutput
    requires_attachment = "image"

    def _run(self, ctx: ToolExecutionContext, args: BrandDetectInput) -> ToolResult:
        image_bytes = ctx.attachments.get(args.attachment_id)
        if not image_bytes:
            raise ToolError(f"no image bytes at attachment id {args.attachment_id!r}")

        try:
            from src.vision.brand.recognizer import predict_image_bytes
        except Exception as exc:
            raise ToolError(f"brand_detect unavailable: {exc}") from exc

        try:
            detections = predict_image_bytes(bytes(image_bytes), conf=args.confidence) or []
        except Exception as exc:
            raise ToolError(f"predict_image_bytes failed: {exc}") from exc

        brands = sorted({d.get("brand", "") for d in detections if d.get("brand")})
        out = BrandDetectOutput(brands=brands, detections=detections)
        return ToolResult(
            summary=f"brands={brands or '[]'} detections={len(detections)}",
            data=out.model_dump(),
        )
