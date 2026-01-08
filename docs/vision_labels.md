# 📷 Vision Intelligence Label Schema

**Author:** Pratik Niroula  
**Project:** SentinelForge - Universal Anomaly Intelligence System  
**Last Updated:** January 7, 2026

---

## 📋 Overview

This document defines the unified label schema for all vision-related models in SentinelForge. Consistent labeling ensures seamless integration across different model outputs and simplifies downstream processing.

---

## 🎭 Face Emotion Recognition

### Primary Emotions (Ekman's Basic Emotions)

| Label ID | Label Name | Description | Confidence Threshold |
|----------|------------|-------------|---------------------|
| 0 | `neutral` | No strong emotional expression | 0.5 |
| 1 | `happy` | Joy, pleasure, contentment | 0.6 |
| 2 | `sad` | Sorrow, grief, disappointment | 0.6 |
| 3 | `angry` | Anger, frustration, hostility | 0.65 |
| 4 | `fearful` | Fear, anxiety, apprehension | 0.6 |
| 5 | `surprised` | Surprise, astonishment | 0.55 |
| 6 | `disgusted` | Disgust, contempt | 0.6 |

### Extended Emotions (Optional)

| Label ID | Label Name | Description |
|----------|------------|-------------|
| 7 | `contempt` | Disdain, superiority |
| 8 | `confused` | Uncertainty, bewilderment |
| 9 | `calm` | Relaxed, serene |

### Output Schema

```json
{
  "emotion": {
    "primary": "happy",
    "primary_id": 1,
    "confidence": 0.87,
    "all_scores": {
      "neutral": 0.05,
      "happy": 0.87,
      "sad": 0.02,
      "angry": 0.01,
      "fearful": 0.02,
      "surprised": 0.02,
      "disgusted": 0.01
    }
  }
}
```

---

## 🎭 Deepfake / Real-Fake Detection

### Binary Classification

| Label ID | Label Name | Description |
|----------|------------|-------------|
| 0 | `fake` | AI-generated, manipulated, or synthetic |
| 1 | `real` | Authentic, unmanipulated content |

### Manipulation Types (Multi-label)

| Label | Description | Examples |
|-------|-------------|----------|
| `face_swap` | Face replacement | DeepFaceLab, FaceSwap |
| `face_reenact` | Expression/pose transfer | First Order Motion |
| `lip_sync` | Audio-driven lip movement | Wav2Lip |
| `full_synthesis` | Fully generated face | StyleGAN, This Person Does Not Exist |
| `attribute_edit` | Age, hair, expression changes | FaceApp |
| `background_edit` | Scene manipulation | - |

### Confidence Levels

| Level | Range | Action |
|-------|-------|--------|
| `high_confidence_real` | 0.9 - 1.0 | Trusted |
| `likely_real` | 0.7 - 0.9 | Monitor |
| `uncertain` | 0.3 - 0.7 | Manual review |
| `likely_fake` | 0.1 - 0.3 | Flag |
| `high_confidence_fake` | 0.0 - 0.1 | Block/Alert |

### Output Schema

```json
{
  "authenticity": {
    "label": "fake",
    "label_id": 0,
    "confidence": 0.92,
    "manipulation_types": ["face_swap"],
    "explanation": "Inconsistent lighting on face boundary",
    "artifacts": [
      {"type": "boundary_blur", "location": [120, 80, 200, 160], "severity": 0.8}
    ]
  }
}
```

---

## 🏷️ Brand Recognition

### Detection Output

| Field | Type | Description |
|-------|------|-------------|
| `brand_name` | string | Recognized brand |
| `brand_id` | string | Unique identifier |
| `category` | string | Product category |
| `confidence` | float | Detection confidence |
| `bbox` | array | Bounding box [x, y, w, h] |

### Brand Categories

| Category ID | Category Name | Examples |
|-------------|---------------|----------|
| `apparel` | Clothing & Fashion | Nike, Adidas, Gucci |
| `electronics` | Tech & Electronics | Apple, Samsung, Sony |
| `automotive` | Vehicles & Parts | BMW, Tesla, Toyota |
| `food_beverage` | Food & Drinks | Coca-Cola, McDonald's |
| `luxury` | Luxury Goods | Louis Vuitton, Rolex |
| `sports` | Sports Equipment | Under Armour, Puma |
| `other` | Miscellaneous | - |

### Output Schema

```json
{
  "brands": [
    {
      "brand_name": "Nike",
      "brand_id": "nike_swoosh",
      "category": "apparel",
      "confidence": 0.95,
      "bbox": [100, 200, 50, 30],
      "variant": "swoosh_logo"
    }
  ],
  "total_brands": 1
}
```

---

## 🔍 Object Detection (YOLO)

### Standard COCO Classes (80 classes)

<details>
<summary>Click to expand full class list</summary>

| ID | Class | ID | Class | ID | Class | ID | Class |
|----|-------|----|-------|----|-------|----|-------|
| 0 | person | 20 | elephant | 40 | wine glass | 60 | dining table |
| 1 | bicycle | 21 | bear | 41 | cup | 61 | toilet |
| 2 | car | 22 | zebra | 42 | fork | 62 | tv |
| 3 | motorcycle | 23 | giraffe | 43 | knife | 63 | laptop |
| 4 | airplane | 24 | backpack | 44 | spoon | 64 | mouse |
| 5 | bus | 25 | umbrella | 45 | bowl | 65 | remote |
| 6 | train | 26 | handbag | 46 | banana | 66 | keyboard |
| 7 | truck | 27 | tie | 47 | apple | 67 | cell phone |
| 8 | boat | 28 | suitcase | 48 | sandwich | 68 | microwave |
| 9 | traffic light | 29 | frisbee | 49 | orange | 69 | oven |
| 10 | fire hydrant | 30 | skis | 50 | broccoli | 70 | toaster |
| 11 | stop sign | 31 | snowboard | 51 | carrot | 71 | sink |
| 12 | parking meter | 32 | sports ball | 52 | hot dog | 72 | refrigerator |
| 13 | bench | 33 | kite | 53 | pizza | 73 | book |
| 14 | bird | 34 | baseball bat | 54 | donut | 74 | clock |
| 15 | cat | 35 | baseball glove | 55 | cake | 75 | vase |
| 16 | dog | 36 | skateboard | 56 | chair | 76 | scissors |
| 17 | horse | 37 | surfboard | 57 | couch | 77 | teddy bear |
| 18 | sheep | 38 | tennis racket | 58 | potted plant | 78 | hair drier |
| 19 | cow | 39 | bottle | 59 | bed | 79 | toothbrush |

</details>

### Custom Security Classes

| ID | Class | Description |
|----|-------|-------------|
| 100 | `weapon` | Firearms, knives |
| 101 | `suspicious_package` | Unattended bags |
| 102 | `face_covered` | Masks, balaclavas |
| 103 | `uniform` | Security, police |

### Output Schema

```json
{
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.92,
      "bbox": [100, 150, 200, 400],
      "attributes": {
        "pose": "standing",
        "facing": "camera"
      }
    }
  ],
  "frame_id": 42,
  "timestamp": "2026-01-07T14:30:00Z"
}
```

---

## 📊 Unified Output Format

All vision models output to this standardized format:

```json
{
  "model_id": "emotion_cnn_v2",
  "model_type": "face_emotion",
  "version": "2.0.1",
  "timestamp": "2026-01-07T14:30:00Z",
  "processing_time_ms": 45,
  "input": {
    "source": "upload",
    "filename": "image.jpg",
    "dimensions": [640, 480],
    "format": "JPEG"
  },
  "predictions": [
    {
      "label": "happy",
      "label_id": 1,
      "confidence": 0.87,
      "bbox": [120, 80, 200, 200]
    }
  ],
  "metadata": {
    "device": "cuda:0",
    "batch_size": 1
  }
}
```

---

## 🔄 Label Mapping Functions

### Python Example

```python
from enum import IntEnum

class EmotionLabel(IntEnum):
    NEUTRAL = 0
    HAPPY = 1
    SAD = 2
    ANGRY = 3
    FEARFUL = 4
    SURPRISED = 5
    DISGUSTED = 6

class AuthenticityLabel(IntEnum):
    FAKE = 0
    REAL = 1

def emotion_id_to_name(label_id: int) -> str:
    """Convert emotion ID to name."""
    return EmotionLabel(label_id).name.lower()

def authenticity_id_to_name(label_id: int) -> str:
    """Convert authenticity ID to name."""
    return AuthenticityLabel(label_id).name.lower()
```

---

## 📝 Integration Guidelines

### 1. Consistency
- Always use label IDs for storage and processing
- Use label names only for display/API responses

### 2. Confidence Thresholds
- Respect per-class confidence thresholds
- Flag low-confidence predictions for review

### 3. Multi-model Fusion
- When combining outputs, use weighted confidence
- Resolve conflicts using priority: emotion < authenticity < security

### 4. Versioning
- Include model version in all outputs
- Maintain backward compatibility for label IDs

---

## 📚 References

- [FER2013 Dataset](https://www.kaggle.com/c/challenges-in-representation-learning-facial-expression-recognition-challenge)
- [COCO Dataset Classes](https://cocodataset.org/#home)
- [FaceForensics++ Benchmark](https://github.com/ondyari/FaceForensics)

---

*Last updated: January 7, 2026*
