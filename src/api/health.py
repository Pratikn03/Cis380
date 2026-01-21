from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/ready")
def ready():
    # Extend: check model registry, RAG index existence, DB connectivity
    return {"ready": True}
