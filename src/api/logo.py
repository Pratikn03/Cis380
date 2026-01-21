from fastapi import APIRouter, UploadFile, File
router = APIRouter(prefix="/api/logo", tags=["logo"])

@router.post("/predict")
def predict(file: UploadFile = File(...)):
    # TODO: call LogoService
    return {"route": "logo", "answer": "stub", "metadata": {"filename": file.filename}, "error": None}
