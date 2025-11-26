from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(req: ChatRequest):
    # Placeholder: integrate LLM + router to call models/RAG
    return {"reply": f"Demo echo: {req.message}", "info": "Hook LLM/RAG here"}
