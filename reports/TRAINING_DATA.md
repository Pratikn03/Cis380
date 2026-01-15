# Training Data Audit

- Generated: 2026-01-15 04:01:43 UTC

## Required (production training)

- **Fraud (creditcard.csv)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/fraud/creditcard.csv` — **ok**
  - size: 143.84 MB
  - schema: ok
  - columns: 31
  - columns_sample: Time, V1, V2, V3, V4, V5, V6, V7
- **Cyber (UNSW_NB15_training-set.csv)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/cyber/UNSW_NB15_training-set.csv` — **ok**
  - size: 14.67 MB
  - schema: ok
  - columns: 45
  - columns_sample: id, dur, proto, service, state, spkts, dpkts, sbytes
- **Behavior (online_shoppers_intention.csv)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/behavior/online_shoppers_intention.csv` — **ok**
  - size: 1.02 MB
  - schema: ok
  - columns: 18
  - columns_sample: Administrative, Administrative_Duration, Informational, Informational_Duration, ProductRelated, ProductRelated_Duration, BounceRates, ExitRates
- **Voice emotion (wav folders)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/voice` — **ok**
  - happy: 1863 wav, probe=ok
  - sad: 1863 wav, probe=ok
  - angry: 1863 wav, probe=ok
  - neutral: 1775 wav, probe=ok
- **Brand (LogoDet-3K raw)** — `['/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/brand/LogoDet-3K', '/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/brand/logodet3k']` — **ok**
- **Brand (prepared YOLO dataset)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/processed/brand_yolo/brands.yaml` — **ok**
  - note: prepared dataset present
  - train_images: 5000 (capped)
  - val_images: 5000 (capped)
  - yaml: train=/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/processed/brand_yolo/images/train, val=/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/processed/brand_yolo/images/val, names=1

## Optional (extended training)

- **Vision real/fake (raw)** — `['/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/vision/train_real', '/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/vision/train_fake']` — **ok**
  - real_images: 5000 (capped)
  - fake_images: 5000 (capped)
- **Celeb_V2 (deepfake)** — `['/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/Celeb_V2/Train', '/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/Celeb_V2/Val']` — **ok**
  - train_images: 5000 (capped)
  - val_images: 5000 (capped)
- **Face emotion (image)** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/vision/face_emotion` — **ok**
  - image_count: 5000 (capped)
- **Video temporal (real/fake)** — `['/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/vision/video/real', '/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/vision/video/fake']` — **ok**
  - real_videos: 890
  - fake_videos: 2000 (capped)
- **MovieLens recommender** — `/Users/pratik_n/Desktop/MyComputer/universal-anomaly-intelligence-v2/data/raw/recommendation/movielens.csv` — **ok**
  - size: 658.37 MB
  - schema: ok
  - columns: 4
  - columns_sample: userId, movieId, rating, timestamp