from __future__ import annotations

from functools import lru_cache
from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, model_validator

router = APIRouter()


class ChatRequest(BaseModel):
    text: str | None = None
    message: str | None = None
    user_id: str = "anon"
    use_rag: Optional[bool] = True
    attachments: Optional[Dict[str, object]] = None

    @model_validator(mode="after")
    def _require_text(self) -> "ChatRequest":
        if not (self.text or self.message):
            raise ValueError("Provide 'text' or 'message'.")
        return self

    def resolved_text(self) -> str:
        return (self.text or self.message or "").strip()


@lru_cache(maxsize=1)
def _get_orchestrator():
    from app.agent.memory import MemoryStore
    from app.agent.orchestrator import SentifargoOrchestrator
    from app.utils import LLMStub

    return SentifargoOrchestrator(llm_client=LLMStub(), memory_store=MemoryStore.from_env())


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> Dict[str, object]:
    orchestrator = _get_orchestrator()
    return orchestrator.handle(
        payload.resolved_text(),
        payload.user_id,
        use_rag=payload.use_rag if payload.use_rag is not None else True,
        attachments=payload.attachments,
    )
