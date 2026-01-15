# Training Gap Analysis

- Generated: 2026-01-15 18:08:56 UTC

## Data readiness (from TRAINING_DATA.json)

### Required datasets

- **Fraud (creditcard.csv)** — **ok**
- **Cyber (UNSW_NB15_training-set.csv)** — **ok**
- **Behavior (online_shoppers_intention.csv)** — **ok**
- **Voice emotion (wav folders)** — **ok**
- **Brand (LogoDet-3K raw)** — **ok**
- **Brand (prepared YOLO dataset)** — **ok**

### Optional datasets

- **Vision real/fake (raw)** — **ok**
- **Celeb_V2 (deepfake)** — **ok**
- **Face emotion (image)** — **ok**
- **Video temporal (real/fake)** — **ok**
- **MovieLens recommender** — **ok**

## Model artifact readiness

- `models/fraud/supervised/fraud_model.pkl` — **ok**
- `models/cyber/supervised/cyber_model.pkl` — **ok**
- `models/behavior/behavior_supervised.pkl` — **ok**
- `models/behavior/behavior_lof.pkl` — **ok**
- `models/voice_emotion.pkl` — **ok**
- `models/recommender/recommender_model.pkl` — **ok**
- `models/recommender/recommender_meta.joblib` — **ok**
- `models/recommender/movielens_model.pkl` — **ok**
- `models/recommender/movielens_meta.joblib` — **ok**
- `models/vision/resnet/model.pt` — **ok**
- `models/vision/resnet/classes.txt` — **ok**
- `models/vision/face_emotion/model.pt` — **ok**
- `models/vision/face_emotion/classes.txt` — **ok**
- `models/vision/video_temporal_model.pkl` — **ok**
- `artifacts/vision_temporal/temporal_lstm.pt` — **ok**
- `artifacts/brand/yolo_logo_det.pt` — **ok**
- `models/fusion/fusion_meta_model.pkl` — **ok**

## Missing artifacts (must train/build)

- None

## DSA RAG index

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/dsa_embeddings` ready: **True**

## DVC status

- `dvc.yaml` present: **True**
- `dvc.lock` present: **True**

## Accuracy + training recommendations

- Video temporal: retrain if new real/fake videos are added; monitor LSTM drift.
- Behavior model: add more insider-style patterns if false positives remain high.
- Voice emotion: augment with noise if `tests/test_voice_noise.py` fails.
- Brand YOLO: current model is single-class (`logo`); multi-class car-brand needs new dataset + retrain.
- DSA RAG: expand docs beyond arrays/search/linked-lists/stack-queue as coverage grows.
