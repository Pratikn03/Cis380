"""FastAPI gateway placeholder for OmniChatX."""
from fastapi import FastAPI
from api.routes import chat, rag, recommend, behavior, fraud, cyber

app = FastAPI(title="OmniChatX API", version="0.1")

app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(recommend.router)
app.include_router(behavior.router)
app.include_router(fraud.router)
app.include_router(cyber.router)


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
