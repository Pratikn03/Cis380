from __future__ import annotations

from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent import MemoryStore, SentifargoOrchestrator
from app.utils import LLMStub

router = APIRouter()
orchestrator = SentifargoOrchestrator(llm_client=LLMStub(), memory_store=MemoryStore.from_env())


class ChatRequest(BaseModel):
    text: str
    user_id: str = "anon"
    use_rag: Optional[bool] = True
    attachments: Optional[Dict[str, object]] = None


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest) -> Dict[str, object]:
    return orchestrator.handle(
        payload.text,
        payload.user_id,
        use_rag=payload.use_rag if payload.use_rag is not None else True,
        attachments=payload.attachments,
    )
