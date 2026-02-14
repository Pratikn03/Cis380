# Voice Emotion Pipeline (Production Upgrade)

This folder contains scripts to audit data, build speaker‑independent splits,
train a modern SSL‑based model, and evaluate with proper metrics.

## 1) Audit dataset
```
python scripts/voice/audit_voice_dataset.py \
  --data-root data/raw/voice \
  --pattern '^(?P<speaker>\\d{4})_.*\\.wav$'
```

## 2) Build manifest
```
python scripts/voice/build_emotion_manifest.py \
  --data-root data/raw/voice \
  --out data/raw/voice/manifest.csv
```

## 3) Speaker‑independent split
```
python scripts/voice/split_manifest.py \
  --manifest data/raw/voice/manifest.csv \
  --out-dir data/raw/voice \
  --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
```

## 4) Train SSL model (Wav2Vec2 / HuBERT / WavLM)
```
python scripts/voice/train_emotion_ssl.py \
  --train-manifest data/raw/voice/manifest.train.csv \
  --val-manifest data/raw/voice/manifest.val.csv \
  --model facebook/wav2vec2-base \
  --output-dir models/voice_emotion_ssl \
  --batch-size 8 --epochs 10 --learning-rate 1e-4 \
  --freeze-feature-encoder
```

## 5) Evaluate (macro‑F1 / UAR / accuracy)
```
python scripts/voice/eval_emotion_ssl.py \
  --model-dir models/voice_emotion_ssl \
  --test-manifest data/raw/voice/manifest.test.csv
```

Notes:
- Use speaker‑independent splits to avoid leakage.
- For “crying detection,” prefer a **binary classifier** rather than 5‑class emotion.
