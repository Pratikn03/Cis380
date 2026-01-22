"""
Verify face emotion prediction with a dummy image.
"""
import io
import sys
from pathlib import Path
from PIL import Image

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main():
    try:
        from app.models.vision.face_emotion_predict import predict_face_emotion, MODEL_PATH
    except ImportError as e:
        print(f"Error importing module: {e}")
        return

    print(f"Checking model at: {MODEL_PATH.resolve()}")
    print("Generating dummy image...")
    img = Image.new('RGB', (224, 224), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    image_bytes = buf.getvalue()

    print("Testing prediction...")
    result = predict_face_emotion(image_bytes, filename="test.jpg")
    
    print("\nPrediction Result:")
    print(result)

    if "error" in result:
        print("\n❌ Prediction failed (expected if model not trained).")
        print("To train the model, run:")
        print("  python -m src.train.train_face_emotion")
    else:
        print("\n✅ Prediction successful.")

if __name__ == "__main__":
    main()