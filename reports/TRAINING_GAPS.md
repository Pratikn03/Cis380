# Training Gap Analysis

- Generated: 2026-01-15 04:07:13 UTC

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
- `models/recommender/recommender_meta.joblib` — **missing**
- `models/recommender/movielens_model.pkl` — **ok**
- `models/recommender/movielens_meta.joblib` — **ok**
- `models/vision/resnet/model.pt` — **ok**
- `models/vision/resnet/classes.txt` — **ok**
- `models/vision/face_emotion/model.pt` — **ok**
- `models/vision/face_emotion/classes.txt` — **ok**
- `artifacts/vision_temporal/temporal_lstm.pt` — **missing**
- `artifacts/brand/yolo_logo_det.pt` — **ok**
- `models/fusion/fusion_meta_model.pkl` — **ok**

## Missing artifacts (must train/build)

- `models/recommender/recommender_meta.joblib` (recommender_meta)
- `artifacts/vision_temporal/temporal_lstm.pt` (vision_temporal)

## DSA RAG index

- `data/dsa_embeddings/` ready: **True**

## DVC status

- `dvc.yaml` present: **True**
- `dvc.lock` present: **False**

## Accuracy + training recommendations

- **Vision temporal**: train `artifacts/vision_temporal/temporal_lstm.pt` with `python -m src.train.train_video_temporal`.
- **Recommender meta**: generate `models/recommender/recommender_meta.joblib` or adjust legacy paths; missing meta limits feature-name output.
- **Behavior model**: if accuracy is low, add CERT r4.2 LDAP or engineer more features; dataset is small.
- **Voice emotion**: consider augmentation or more data for higher robustness (noise tests exist in `tests/test_voice_noise.py`).
- **Brand YOLO**: current model is single-class (`logo`); multi-class car-brand needs a new dataset + retrain.