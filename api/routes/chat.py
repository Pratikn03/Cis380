import asyncio
import os
import requests
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.orchestrator import OmniChatXOrchestrator
from api.deps import require_auth, check_token_query

router = APIRouter(prefix="/api/chat", tags=["chat"], dependencies=[Depends(require_auth)])
agent = OmniChatXOrchestrator()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(req: ChatRequest):
    reply = agent.route(req.message)
    return {"reply": reply}


@router.get("/stream")
async def chat_stream(message: str, token: str | None = None):
    """SSE-style streaming endpoint.

    If OPENAI_API_KEY is set, streams LLM tokens from OpenAI.
    Otherwise, falls back to word-chunk streaming of orchestrator reply.
    """
    check_token_query(token)

    async def event_gen_llm():
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_KEY}"}
        payload = {
            "model": "gpt-3.5-turbo",  # adjust here if you change providers/models
            "stream": True,
            "messages": [{"role": "user", "content": message}],
        }
        # simple retry/backoff for 429
        for attempt in range(3):
            try:
                with requests.post(url, headers=headers, json=payload, stream=True, timeout=30) as resp:
                    if resp.status_code == 429 and attempt < 2:
                        await asyncio.sleep(2 ** attempt)  # backoff
                        continue
                    resp.raise_for_status()
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line or not line.startswith("data:"):
                            continue
                        data = line.removeprefix("data:").strip()
                        if data == "[DONE]":
                            yield "data: [DONE]\\n\\n"
                            return
                        try:
                            chunk = requests.compat.json.loads(data)
                            delta = chunk["choices"][0]["delta"].get("content")
                            if delta:
                                yield f"data: {delta}\\n\\n"
                        except Exception:
                            continue
                break
            except requests.HTTPError as exc:
                if resp.status_code == 429 and attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                yield f"data: [ERROR] {exc}\\n\\n"
                return

    async def event_gen_fallback():
        try:
            reply = agent.route(message)
            for word in reply.split():
                yield f"data: {word}\\n\\n"
                await asyncio.sleep(0.01)
            yield "data: [DONE]\\n\\n"
        except Exception as exc:
            yield f"data: [ERROR] {exc}\\n\\n"

    gen = event_gen_llm() if OPENAI_KEY else event_gen_fallback()
    return StreamingResponse(gen, media_type="text/event-stream")
