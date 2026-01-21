from fastapi import APIRouter, UploadFile, File
router = APIRouter(prefix="/api/audio", tags=["audio"])

@router.post("/emotion")
def emotion(file: UploadFile = File(...)):
    # TODO: call AudioService
    return {"route": "audio", "answer": "stub", "metadata": {"filename": file.filename}, "error": None}
