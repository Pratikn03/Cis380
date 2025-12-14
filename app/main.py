from __future__ import annotations

from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.fraud import router as fraud_router
from app.api.health import router as health_router
from app.api.monitor import router as monitor_router
from app.api.rag import router as rag_router
from app.api.recommender import router as recommender_router
from app.api.voice import router as voice_router

app = FastAPI(title="OmniChatX API")
app.include_router(chat_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(recommender_router, prefix="/api")
app.include_router(fraud_router, prefix="/api")
app.include_router(monitor_router, prefix="/api")
app.include_router(health_router)
app.include_router(voice_router, prefix="/api")
