"""
Verify the voice emotion pipeline by generating dummy data, training, and inferencing.
"""
import os
import sys
import numpy as np
import soundfile as sf
from pathlib import Path
import subprocess
import io

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def create_dummy_data():
    data_dir = ROOT / "data/raw/voice"
    emotions = ["happy", "sad", "angry", "neutral"]
    
    print(f"Creating dummy audio data in {data_dir}...")
    
    for i, emo in enumerate(emotions):
        emo_dir = data_dir / emo
        emo_dir.mkdir(parents=True, exist_ok=True)
        # Create 5 dummy wav files per emotion
        for j in range(5):
            path = emo_dir / f"sample_{j}.wav"
            if not path.exists():
                # Generate 1 second of tone
                sr = 16000
                t = np.linspace(0, 1.0, sr)
                freq = 440 + (i * 100) # Different freq per emotion
                y = 0.5 * np.sin(2 * np.pi * freq * t)
                sf.write(str(path), y, sr)

def run_training():
    print("Running training script...")
    # Ensure ROOT is in PYTHONPATH so the subprocess can import 'app'
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    
    cmd = [
        sys.executable, 
        "app/models/voice/emotion_train.py",
        "--limit-per-class", "5",
        "--out-model", "models/voice_emotion.pkl"
    ]
    subprocess.run(cmd, cwd=str(ROOT), check=True, env=env)

def verify_inference():
    print("Verifying inference...")
    from app.models.voice.emotion_predict import predict_emotion
    
    # Create dummy bytes
    sr = 16000
    t = np.linspace(0, 1.0, sr)
    y = 0.5 * np.sin(2 * np.pi * 440 * t)
    
    buf = io.BytesIO()
    sf.write(buf, y, sr, format='WAV')
    audio_bytes = buf.getvalue()
    
    result = predict_emotion(audio_bytes)
    print("Prediction result:", result)
    if "error" in result:
        raise RuntimeError(f"Inference failed: {result['error']}")

if __name__ == "__main__":
    create_dummy_data()
    run_training()
    verify_inference()
    print("\n✅ Voice pipeline verification passed!")