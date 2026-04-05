# Dataset Download Checklist

This repo does not ship training datasets. Use this checklist to download the
missing datasets and place them in the expected paths.

Prereqs (for Kaggle downloads):
- Install Kaggle CLI: `pip install kaggle`
- Add `~/.kaggle/kaggle.json` (API token) and `chmod 600 ~/.kaggle/kaggle.json`
- Quick re-download script: `bash scripts/redownload_kaggle_datasets.sh`

---

## Required (production training)

1) Fraud - Credit Card Fraud Detection
- Source: Kaggle (mlg-ulb/creditcardfraud)
- Download:
  `kaggle datasets download -d mlg-ulb/creditcardfraud -p data/raw/fraud --unzip`
- Expected file: `data/raw/fraud/creditcard.csv`

2) Cyber - UNSW-NB15
- Source: UNSW-NB15 dataset (Kaggle or UNSW official mirror)
- Download (example Kaggle search): `kaggle datasets list -s unsw-nb15`
- Expected file: `data/raw/cyber/UNSW_NB15_training-set.csv`
- Note: If the filename differs, rename it to `UNSW_NB15_training-set.csv`.

3) Behavior - Online Shoppers Intention
- Source: UCI ML Repository (Online Shoppers Purchasing Intention Dataset)
- Download: https://archive.ics.uci.edu/ml/datasets/Online+Shoppers+Purchasing+Intention+Dataset
- Expected file: `data/raw/behavior/online_shoppers_intention.csv`
- Note: Convert the UCI `online_shoppers_intention.csv` if needed.

4) Voice emotion - WAV folders by class
- Source: Any labeled emotion audio set (CREMA-D recommended)
- Download: https://github.com/CheyneyComputerScience/CREMA-D
- Expected folders:
  - `data/raw/voice/happy/*.wav`
  - `data/raw/voice/sad/*.wav`
  - `data/raw/voice/angry/*.wav`
  - `data/raw/voice/neutral/*.wav`
- Helper script (CREMA-D): `python scripts/prepare_crema_d_av.py`

5) Speech-to-Text (STT)
- Source: Any audio + transcript corpus (English)
- Bootstrap (offline Whisper) from local audio:
  - `python scripts/stt/bootstrap_transcripts.py --audio-root data/raw/voice/AudioWAV --out data/raw/stt/transcripts.jsonl --language en --limit 200`
  - `python scripts/stt/build_manifest.py --transcripts data/raw/stt/transcripts.jsonl --out data/raw/stt/manifest.csv --normalize --require-text`
  - `python scripts/stt/split_manifest.py --manifest data/raw/stt/manifest.csv --group-by speaker_id`
  - `python scripts/stt/validate_manifest.py --manifest data/raw/stt/manifest.with_splits.csv`

6) Brand/logo - LogoDet-3K
- Source: LogoDet-3K (paper + dataset)
- Download: https://github.com/Wangjing1567/LogoDet-3K
- Expected raw: `data/raw/brand/logodet3k/` (or `data/raw/brand/LogoDet-3K/`)
- Prepare YOLO: `python scripts/prepare_brand_data.py`
- Expected prepared: `data/processed/brand_yolo/brands.yaml`

---

## Optional (extended training)

7) Vision real/fake (images)
- Source: Any labeled real-vs-fake image dataset
- Place raw under: `data/raw/vision/datasets/<dataset_name>/`
- Prepare splits:
  `python scripts/prepare_vision_data.py --src data/raw/vision/datasets/<dataset_name>`
- Expected output:
  - `data/raw/vision/train_real/`
  - `data/raw/vision/train_fake/`

8) Deepfake (Celeb-DF v2)
- Source: Celeb-DF v2
- Download: https://github.com/yuezunli/celeb-deepfakeforensics
- Expected path: `data/Celeb_V2/Train` and `data/Celeb_V2/Val`

9) Face emotion (images)
- Source: FER2013 (Kaggle)
- Download: https://www.kaggle.com/c/challenges-in-representation-learning-facial-expression-recognition-challenge
- Expected layout:
  `data/raw/vision/face_emotion/train/<emotion>/`
  `data/raw/vision/face_emotion/val/<emotion>/`
- Emotions: angry, disgust, fear, happy, sad, surprise, neutral
- Train: `python -m src.train.train_face_emotion --data-dir data/raw/vision/face_emotion`

10) Video temporal (real/fake)
- Source: Any real-vs-fake video dataset (FaceForensics++, DFDC, etc.)
- Expected folders:
  - `data/raw/vision/video/real/`
  - `data/raw/vision/video/fake/`

11) Recommender - MovieLens 20M
- Source: Kaggle (grouplens/movielens-20m-dataset)
- Download script: `python scripts/download_movielens.py`
- Expected file: `data/raw/recommendation/movielens.csv`

12) DAGM 2007 (YOLO defect detection)
- Source: Kaggle (mhskjelvareid/dagm-2007-competition-dataset)
- Download script: `python download_kaggle_data.py`
- Expected path: `dataset/` with `images/train|val` and `labels/train|val`

---

## Verify after download

Run the audit to confirm everything is in place:
`python scripts/training_data_audit.py`

Outputs:
- `reports/TRAINING_DATA.md`
- `reports/TRAINING_DATA.json`
