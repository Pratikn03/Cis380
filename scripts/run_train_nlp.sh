#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
from pathlib import Path
import pandas as pd

from uais_v.models.nlp_text_model import NLPTextConfig
from uais_v.training.train_nlp import train_distilbert

cfg = NLPTextConfig()
path = Path('data/processed/nlp/enron_emails.csv')
if not path.exists():
    texts = ["this is normal", "urgent wire transfer now", "please review invoice"]
    labels = [0, 1, 0]
else:
    df = pd.read_csv(path)
    texts = df['text'].astype(str).tolist()
    labels = df['label'].astype(int).tolist()

save_dir = Path('models/nlp/distilbert')
model, metrics, out_dir = train_distilbert(texts, labels, cfg, batch_size=cfg.num_labels * 4, epochs=1, save_dir=save_dir)
print('NLP metrics:', metrics)
PY
