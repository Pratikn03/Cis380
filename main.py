from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ultralytics import YOLO
from transformers import pipeline
from openai import OpenAI
from PIL import Image
import io
import uvicorn
import os
import tempfile
import PyPDF2

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

# Initialize Summarization model
try:
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
except Exception as e:
    print(f"Warning: Failed to load Summarization model: {e}")
    summarizer = None

# Initialize QA model
try:
    qa_model = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
except Exception as e:
    print(f"Warning: Failed to load QA model: {e}")
    qa_model = None

# Initialize Audio Emotion model
try:
    audio_emotion_classifier = pipeline("audio-classification", model="superb/wav2vec2-base-superb-er")
except Exception as e:
    print(f"Warning: Failed to load Audio Emotion model: {e}")
    audio_emotion_classifier = None

# Initialize OpenAI Client for Recommendations
try:
    # Ensure OPENAI_API_KEY is set in your environment variables
    openai_client = OpenAI()
except Exception as e:
    print(f"Warning: Failed to initialize OpenAI client: {e}")
    openai_client = None

pdf_storage = {}

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

                anomalies.append({
                    "type": class_name,
                    "confidence": round(confidence, 4),
                    "bbox": bbox
                })

        return {
            "filename": file.filename,
            "anomaly_count": len(anomalies),
            "anomalies": anomalies
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/analyze-audio")
async def analyze_audio(file: UploadFile = File(...)):
    """
    Accepts an audio file, transcribes it, and performs basic anomaly detection (placeholder).
    """
    if not AUDIO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Audio dependencies (faster-whisper, librosa) not installed.")
    
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

        # Analyze Emotion
        emotions = []
        if audio_emotion_classifier:
            try:
                # The pipeline returns a list of dicts [{'score': 0.9, 'label': 'neu'}, ...]
                emotion_results = audio_emotion_classifier(tmp_path, top_k=5)
                emotions = [{"label": res["label"], "score": res["score"]} for res in emotion_results]
            except Exception as e:
                print(f"Error analyzing audio emotion: {e}")

        # Clean up temp file
        os.remove(tmp_path)

        return {
            "filename": file.filename,
            "language": info.language,
            "transcription": transcription,
            "emotions": emotions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@app.post("/analyze-text")
async def analyze_text(file: UploadFile = File(...)):
    """
    Accepts a PDF file, extracts text, and returns it.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        contents = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(contents))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""

        # Store in memory for Q&A
        pdf_storage[file.filename] = text

        # Generate Summary
        summary = ""
        if summarizer and text:
            try:
                # Truncate text to avoid token limit issues for this example (approx 1024 chars)
                input_text = text[:1024]
                summary_result = summarizer(input_text, max_length=130, min_length=30, do_sample=False)
                summary = summary_result[0]['summary_text']
            except Exception as e:
                print(f"Error summarizing text: {e}")

        return {"filename": file.filename, "content": text, "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


class QuestionRequest(BaseModel):
    filename: str
    question: str

@app.post("/ask-pdf")
async def ask_pdf(request: QuestionRequest):
    context = pdf_storage.get(request.filename)
    if not context:
        raise HTTPException(status_code=404, detail="PDF context not found. Please upload the file again.")
    
    if not qa_model:
        raise HTTPException(status_code=503, detail="QA model not loaded.")
    
    try:
        # Limit context to avoid token length issues (naive approach for demo)
        result = qa_model(question=request.question, context=context[:15000])
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RecommendationRequest(BaseModel):
    context: str

@app.post("/recommend")
async def recommend(request: RecommendationRequest):
    if not openai_client:
        raise HTTPException(status_code=503, detail="OpenAI client not initialized. Please set OPENAI_API_KEY.")
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a versatile intelligent assistant. Provide 3 concise, relevant recommendations based on the input context. This could range from safety actions for anomalies, to styling tips for clothes, movie suggestions based on mood, or maintenance tips for vehicles. Format them as a numbered list."},
                {"role": "user", "content": f"Context: {request.context}"}
            ],
            max_tokens=200
        )
        recommendation = response.choices[0].message.content.strip()
        return {"recommendation": recommendation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)