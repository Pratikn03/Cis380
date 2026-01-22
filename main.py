from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import uvicorn
import os
import tempfile

# Conditional import for audio dependencies
try:
    import librosa
    import numpy as np
    from faster_whisper import WhisperModel

    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

app = FastAPI(title="Universal Anomaly Intelligence API")

# Enable CORS to allow requests from the frontend (e.g., Streamlit or ngrok)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the YOLO model.
# Note: 'yolov8n.pt' is a standard pretrained model. It will download automatically if missing.
# For specific anomaly detection, replace this with your custom trained model path (e.g., 'best.pt').
try:
    model = YOLO("yolov8n.pt")
except Exception as e:
    print(f"Warning: Failed to load YOLO model: {e}")
    model = None

# Initialize the Whisper model for audio if available
whisper_model = None
if AUDIO_AVAILABLE:
    try:
        # 'tiny' is sufficient for testing; use 'base' or 'small' for better accuracy
        whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    except Exception as e:
        print(f"Warning: Failed to load Whisper model: {e}")


@app.post("/detect-anomalies")
async def detect_anomalies(file: UploadFile = File(...)):
    """
    Accepts an image upload, runs YOLO inference, and returns detected objects/anomalies.
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        # Read image file
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Run inference
        # conf=0.25 is a common default confidence threshold
        results = model(image, conf=0.25)

        anomalies = []
        # Process results (results is a list, usually one item per image)
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                anomalies.append(
                    {"type": class_name, "confidence": round(confidence, 4), "bbox": bbox}
                )

        return {"filename": file.filename, "anomaly_count": len(anomalies), "anomalies": anomalies}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file, transcribes it, and performs basic anomaly detection (placeholder).
    """
    if not AUDIO_AVAILABLE:
        raise HTTPException(
            status_code=503, detail="Audio dependencies (faster-whisper, librosa) not installed."
        )

    if whisper_model is None:
        raise HTTPException(status_code=503, detail="Audio model not loaded.")

    try:
        # Save uploaded file to a temporary file
        suffix = os.path.splitext(file.filename)[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Transcribe audio
        segments, info = whisper_model.transcribe(tmp_path, beam_size=5)
        transcription = " ".join([segment.text for segment in segments])

        # Clean up temp file
        os.remove(tmp_path)

        return {
            "filename": file.filename,
            "language": info.language,
            "transcription": transcription,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
