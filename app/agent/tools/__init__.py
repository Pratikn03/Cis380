"""Tool registry for the multi-agent planner.

Each tool wraps an existing internal handler. The planner sees only the
input/output JSON Schema; tool execution stays in-process so we don't pay
HTTP latency on every tool call.
"""

from __future__ import annotations

from app.agent.tools._base import (
    Tool,
    ToolError,
    ToolExecutionContext,
    ToolResult,
    SessionAttachments,
)
from app.agent.tools.behavior import BehaviorScoreTool
from app.agent.tools.brand import BrandDetectTool
from app.agent.tools.cyber import CyberScoreTool
from app.agent.tools.fraud import FraudScoreTool
from app.agent.tools.rag import RagSearchTool
from app.agent.tools.recommend import RecommendTool
from app.agent.tools.risk import RiskScoreTool
from app.agent.tools.transcribe import TranscribeTool
from app.agent.tools.vision import VisionAnalyzeTool
from app.agent.tools.voice import VoiceEmotionTool

ALL_TOOLS: list[Tool] = [
    RagSearchTool(),
    FraudScoreTool(),
    CyberScoreTool(),
    BehaviorScoreTool(),
    RiskScoreTool(),
    RecommendTool(),
    BrandDetectTool(),
    VisionAnalyzeTool(),
    VoiceEmotionTool(),
    TranscribeTool(),
]

TOOLS_BY_NAME: dict[str, Tool] = {tool.name: tool for tool in ALL_TOOLS}


def get_tool(name: str) -> Tool:
    """Return the tool by name or raise ToolError."""
    try:
        return TOOLS_BY_NAME[name]
    except KeyError as exc:
        raise ToolError(f"unknown tool: {name!r}") from exc


__all__ = [
    "Tool",
    "ToolError",
    "ToolExecutionContext",
    "ToolResult",
    "SessionAttachments",
    "ALL_TOOLS",
    "TOOLS_BY_NAME",
    "get_tool",
]
