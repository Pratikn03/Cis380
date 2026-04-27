"""RAG search over the indexed corpus."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.agent.tools._base import Tool, ToolError, ToolExecutionContext, ToolResult


class RagSearchInput(BaseModel):
    query: str = Field(..., description="Natural-language question to search the corpus for.", min_length=1)
    top_k: int = Field(5, ge=1, le=20, description="Number of source chunks to retrieve.")


class RagSearchOutput(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    chunks: list[dict[str, Any]]
    confidence: float


class RagSearchTool(Tool):
    name = "rag_search"
    description = (
        "Search the indexed knowledge base and return a concise answer with citations. "
        "Use for policy/manual/document questions, looking up procedures, or finding "
        "definitions in the corpus."
    )
    input_schema = RagSearchInput
    output_schema = RagSearchOutput

    def _run(self, ctx: ToolExecutionContext, args: RagSearchInput) -> ToolResult:
        try:
            from app.rag.dsa_pipeline import answer_query
        except Exception as exc:  # pragma: no cover - optional dep
            raise ToolError(f"rag_search unavailable: {exc}") from exc

        try:
            result = answer_query(args.query, top_k=args.top_k)
        except Exception as exc:
            raise ToolError(f"rag_search failed: {exc}") from exc

        chunks = [
            {
                "source": chunk.get("source"),
                "score": chunk.get("hybrid_score", chunk.get("score")),
                "chunk_id": chunk.get("chunk_id"),
                "page": chunk.get("page"),
                "text": (chunk.get("text") or "")[:500],
            }
            for chunk in result.get("sources", [])
        ]
        out = RagSearchOutput(
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            chunks=chunks,
            confidence=float(result.get("confidence", 0.0)),
        )
        summary = f"Retrieved {len(chunks)} chunks (confidence={out.confidence:.2f})."
        return ToolResult(
            summary=summary,
            data=out.model_dump(),
            confidence=out.confidence,
            citations=out.citations,
        )
