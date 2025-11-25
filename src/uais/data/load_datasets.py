from pathlib import Path
import pandas as pd

def load_fraud_data(path="data/raw/fraud/creditcard.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Fraud dataset not found: {p}")
    print(f"✅ Loading fraud dataset: {p}")
    return pd.read_csv(p)

def load_cyber_data(path="data/raw/cyber/UNSW-NB15.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Cyber dataset not found: {p}")
    print(f"✅ Loading cyber dataset: {p}")
    return pd.read_csv(p)

def load_behavior_data(path="data/raw/behavior/r4.2/logon.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Behavior dataset not found: {p}")
    print(f"✅ Loading CERT behavior dataset: {p}")
    return pd.read_csv(p)

def load_nlp_data(path="data/raw/nlp/enron_emails.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"NLP dataset not found: {p}")
    print(f"✅ Loading NLP dataset: {p}")
    return pd.read_csv(p)

def load_vision_data(path="data/raw/vision/deepfake_real.csv"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Vision dataset not found: {p}")
    print(f"✅ Loading Vision dataset: {p}")
    return pd.read_csv(p)
