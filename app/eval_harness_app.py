from __future__ import annotations

from fastapi import FastAPI, File, Query, UploadFile
from pydantic import BaseModel

app = FastAPI(title="Sentifargo Evaluation Harness", version="1.0")


class ChatRequest(BaseModel):
    text: str
    use_rag: bool | None = None


class FraudRequest(BaseModel):
    features: list[float]


class RiskRequest(BaseModel):
    login_country: str
    device_known: bool
    login_time: float
    clicks_per_minute: float
    files_accessed: int
    transaction_amount: float


class RagAskRequest(BaseModel):
    query: str


class RagIngestRequest(BaseModel):
    filename: str
    content: str


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "sentifargo-eval-harness", "status": "ok"}


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "evaluation_harness"}


@app.post("/api/chat")
def chat(payload: ChatRequest) -> dict[str, object]:
    return {
        "route": "chat",
        "answer": f"harness-response:{payload.text[:64]}",
        "meta": {"mode": "evaluation_harness", "use_rag": bool(payload.use_rag)},
    }


@app.post("/api/fraud")
def fraud(payload: FraudRequest) -> dict[str, object]:
    score = min(0.99, max(0.01, len(payload.features) / 100.0))
    return {"fraud_probability": score, "mode": "evaluation_harness"}


@app.post("/api/risk/analyze")
def risk(payload: RiskRequest) -> dict[str, object]:
    risk_score = round(min(1.0, payload.transaction_amount / 1000.0), 4)
    return {"risk_score": risk_score, "label": "medium", "mode": "evaluation_harness"}


@app.post("/api/voice/emotion")
async def voice_emotion(file: UploadFile = File(...)) -> dict[str, object]:
    _ = await file.read()
    return {"emotion": "neutral", "confidence": 0.5, "mode": "evaluation_harness"}


@app.post("/api/vision/brand/predict")
async def brand_predict(
    file: UploadFile = File(...),
    kind: str = Query(default="logo"),
) -> dict[str, object]:
    _ = await file.read()
    return {"kind": kind, "detections": [], "mode": "evaluation_harness"}


@app.post("/api/vision/face_emotion/predict")
async def face_emotion(file: UploadFile = File(...)) -> dict[str, object]:
    _ = await file.read()
    return {"emotion": "neutral", "mode": "evaluation_harness"}


@app.post("/api/rag/ingest")
def rag_ingest(payload: RagIngestRequest) -> dict[str, object]:
    return {"status": "ingested", "filename": payload.filename, "mode": "evaluation_harness"}


@app.post("/api/rag/ask")
def rag_ask(payload: RagAskRequest) -> dict[str, object]:
    return {
        "answer": f"harness-answer:{payload.query[:48]}",
        "citations": ["harness-doc"],
        "mode": "evaluation_harness",
    }


@app.get("/api/monitor/summary")
def monitor_summary() -> dict[str, object]:
    return {"events": 0, "mode": "evaluation_harness"}


@app.get("/api/monitor/drift")
def monitor_drift() -> dict[str, object]:
    return {"drift_detected": False, "mode": "evaluation_harness"}


@app.get("/api/monitor/risk_summary")
def risk_summary() -> dict[str, object]:
    return {"risk_level": "low", "mode": "evaluation_harness"}
