"""Tool primitives used by the multi-agent planner.

A tool wraps an existing internal handler and exposes:

  - ``name``: unique snake_case identifier the LLM will call.
  - ``description``: short prompt-facing description.
  - ``input_schema`` / ``output_schema``: Pydantic models. We send the
    Anthropic API the JSON Schema of ``input_schema`` so the model emits
    structured tool calls; the executor parses tool args back into the
    Pydantic input and returns a Pydantic output.
  - ``run(ctx, args)``: synchronous in-process call. We deliberately avoid
    async here because the underlying handlers are mostly sync NumPy /
    sklearn / requests code; the planner driver runs them in a thread pool
    when needed.

Binary attachments (image/audio/video bytes) are not transported through
tool args. Instead the orchestrator stashes them in
``ToolExecutionContext.attachments`` keyed by an opaque string and tools
look the bytes up by ID. This keeps tool args JSON-friendly and small.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, Mapping, Type, TypeVar

from pydantic import BaseModel, ValidationError


_log = logging.getLogger("Sentifargo.agent.tools")


class ToolError(RuntimeError):
    """Raised when a tool cannot run. Caught by the planner and surfaced
    to the model as a tool_result with ``is_error=True``."""


@dataclass
class SessionAttachments:
    """Binary attachments uploaded with a request, looked up by tools.

    The orchestrator builds this from the inbound request once; tools
    receive a reference to it via ``ToolExecutionContext`` and pull bytes
    by attachment id (``image``, ``audio``, ``video``, or any custom key).
    """

    items: dict[str, bytes] = field(default_factory=dict)

    def get(self, key: str) -> bytes | None:
        return self.items.get(key)

    def has(self, key: str) -> bool:
        return key in self.items and bool(self.items[key])


@dataclass
class ToolExecutionContext:
    """Request-scoped state passed to every tool invocation."""

    session_id: str
    user_id: str
    trace_id: str
    attachments: SessionAttachments = field(default_factory=SessionAttachments)
    blackboard: dict[str, Any] = field(default_factory=dict)


class ToolResult(BaseModel):
    """Wrapper around a tool's structured output. The planner sees the
    JSON of ``data`` plus a short ``summary`` line that goes back to the
    model as the tool_result text content.
    """

    summary: str
    data: dict[str, Any]
    confidence: float | None = None
    citations: list[dict[str, Any]] | None = None


InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class Tool(Generic[InputT, OutputT]):
    """Base class for in-process tools. Subclasses must set name,
    description, input_schema, output_schema and implement
    ``_run(ctx, args)``.
    """

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    input_schema: ClassVar[Type[BaseModel]] = BaseModel
    output_schema: ClassVar[Type[BaseModel]] = BaseModel
    requires_attachment: ClassVar[str | None] = None  # e.g. "image", "audio"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.name:
            raise TypeError(f"{cls.__name__} must set a non-empty name")
        if cls.input_schema is BaseModel or cls.output_schema is BaseModel:
            raise TypeError(f"{cls.__name__} must set input_schema and output_schema")

    def to_anthropic_schema(self) -> dict[str, Any]:
        """JSON-schema dict to feed into Anthropic's ``tools=[]`` parameter."""
        return {
            "name": self.name,
            "description": self.description.strip(),
            "input_schema": self._json_schema(),
        }

    def _json_schema(self) -> dict[str, Any]:
        schema = self.input_schema.model_json_schema()
        # Anthropic prefers ``object`` schemas at the top level. Pydantic emits
        # a dict shape already; we strip ``$defs`` keys we won't use here for
        # cleanliness but keep them if subschemas are referenced.
        schema.pop("title", None)
        return schema

    def run(self, ctx: ToolExecutionContext, raw_args: Mapping[str, Any]) -> ToolResult:
        """Validate args, execute, and return a ToolResult.

        Errors are converted into ToolError for the planner driver to wrap
        as an error tool_result.
        """
        try:
            args = self.input_schema.model_validate(dict(raw_args))
        except ValidationError as exc:
            raise ToolError(f"{self.name}: invalid arguments: {exc.errors()}") from exc

        if self.requires_attachment and not ctx.attachments.has(self.requires_attachment):
            raise ToolError(
                f"{self.name}: requires attachment {self.requires_attachment!r} but none was uploaded"
            )

        _log.debug("running tool", extra={"tool": self.name, "trace_id": ctx.trace_id})
        return self._run(ctx, args)  # type: ignore[arg-type]

    def _run(self, ctx: ToolExecutionContext, args: InputT) -> ToolResult:  # noqa: D401
        raise NotImplementedError
