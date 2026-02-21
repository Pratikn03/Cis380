# Training Gap Analysis

- Generated: 2026-02-20 17:46:48 UTC

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

## Pipeline contract checks

- Voice pipeline contract: **ok**
- `trainer_supports_out_model_arg` (`app/models/voice/emotion_train.py`): **ok**
- `verify_script_uses_out_model_arg` (`scripts/verify_voice_pipeline.py`): **ok**
- `verify_script_uses_keyword_audio_bytes` (`scripts/verify_voice_pipeline.py`): **ok**
- `predict_api_keyword_only_audio_bytes` (`app/models/voice/emotion_predict.py`): **ok**

## Report freshness (stale threshold: 48h)

- `reports/TRAINING_DATA.json` — **fresh** (updated: 2026-02-20 17:46:43 UTC, age_h: 0.0)
- `reports/TRAINING_DATA.md` — **fresh** (updated: 2026-02-20 17:46:44 UTC, age_h: 0.0)
- `reports/TRAINING_GAPS.json` — **stale** (updated: 2026-01-22 05:37:40 UTC, age_h: 708.15)
- `reports/TRAINING_GAPS.md` — **stale** (updated: 2026-01-22 05:37:40 UTC, age_h: 708.15)
- `reports/PROJECT_AUDIT.json` — **stale** (updated: 2026-01-22 05:37:40 UTC, age_h: 708.15)
- `reports/PROJECT_AUDIT.md` — **stale** (updated: 2026-01-22 05:37:40 UTC, age_h: 708.15)

## DSA RAG index

- `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/dsa_embeddings` ready: **True**
- Docs: **43**
- Topics: README.md, arrays, bit_manipulation, dp, graphs, greedy, hashing, heaps, linked_lists, recursion_backtracking, searching_sorting, stack_queue, strings, trees

## DVC status

- `dvc.yaml` present: **True**
- `dvc.lock` present: **True**

## Recommendations (current state)

- Refresh stale audit artifacts: reports/TRAINING_GAPS.json, reports/TRAINING_GAPS.md, reports/PROJECT_AUDIT.json, reports/PROJECT_AUDIT.md.
- Keep extending advanced DSA topics (tries, segment trees, suffix arrays).
