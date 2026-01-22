"""
Face emotion prediction module.
"""
class FaceEmotionModelNotTrainedError(Exception):
    pass

def predict_face_emotion(image_bytes: bytes, filename: str, top_k: int = 3) -> dict:
    # Mock implementation
    return {
        "filename": filename,
        "emotion": "happy",
        "confidence": 0.9,
        "top_k": [{"label": "happy", "prob": 0.9}, {"label": "neutral", "prob": 0.1}]
    }