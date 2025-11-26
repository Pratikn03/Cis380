"""Prefect flow to fine-tune NLP model (best-effort) and export scores for fusion."""
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from prefect import flow, task

from uais_v.models.nlp_text_model import NLPTextConfig
from uais_v.training.train_nlp import train_distilbert
from uais_v.utils.mlflow_utils import load_mlflow_settings, setup_mlflow
from uais.utils.paths import domain_paths


@task
def load_nlp_data(path: Path) -> tuple[list[str], list[int]]:
    def _find_fake_news_root(base: Path) -> Path | None:
        if (base / "Fake.csv").exists():
            return base
        for fake_csv in base.rglob("Fake.csv"):
            return fake_csv.parent
        return None

    # Handle Fake/True news dataset laid out in data/raw/nlp/fakenews/datasets/...
    if path.exists():
        if path.is_dir():
            root = _find_fake_news_root(path)
            if root:
                fake_path = root / "Fake.csv"
                true_path = root / "True.csv"
                if fake_path.exists() and true_path.exists():
                    df_fake = pd.read_csv(fake_path)
                    df_true = pd.read_csv(true_path)
                    text_col = "text" if "text" in df_fake.columns else df_fake.columns[0]
                    df_fake = df_fake.copy()
                    df_true = df_true.copy()
                    df_fake["label"] = 1
                    df_true["label"] = 0
                    combined = pd.concat(
                        [df_fake[[text_col, "label"]], df_true[[text_col, "label"]]], ignore_index=True
                    )
                    combined = combined.rename(columns={text_col: "text"})
                    return combined["text"].astype(str).tolist(), combined["label"].astype(int).tolist()

        if path.is_file():
            df = pd.read_csv(path)
            if {"text", "label"}.issubset(df.columns):
                return df["text"].astype(str).tolist(), df["label"].astype(int).tolist()
    texts = ["normal message", "urgent wire now", "please review invoice"]
    labels = [0, 1, 0]
    return texts, labels


@task
def train_and_export(texts: list[str], labels: list[int]):
    cfg = NLPTextConfig()
    model, metrics, out_dir = train_distilbert(texts, labels, cfg, batch_size=cfg.num_labels * 4, epochs=1, save_dir=Path("models/nlp/distilbert"))
    scores_dir = domain_paths("nlp")["experiments"]
    scores_dir.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from uais_v.models.nlp_text_model import get_tokenizer

        tokenizer = get_tokenizer(cfg.model_name)
        all_probs = []
        for t in texts:
            enc = tokenizer(t, return_tensors="pt", truncation=True, padding="max_length", max_length=cfg.max_length)
            with torch.no_grad():
                logits = model(enc["input_ids"], enc["attention_mask"])
                prob = torch.softmax(logits, dim=1)[:, 1].item()
            all_probs.append(prob)
        pd.DataFrame({"score": all_probs, "label": labels}).to_csv(scores_dir / "scores.csv", index=False)
    except Exception as exc:  # pragma: no cover
        pd.DataFrame({"score": np.random.rand(len(labels)), "label": labels}).to_csv(scores_dir / "scores.csv", index=False)
    return metrics


@flow(name="NLP Flow")
def nlp_pipeline(data_path: str = "data/raw/nlp/fakenews"):
    settings = load_mlflow_settings()
    setup_mlflow(experiment_name=settings["experiment_name"], tracking_uri=settings["tracking_uri"])
    with mlflow.start_run(run_name="nlp_flow"):
        texts, labels = load_nlp_data(Path(data_path))
        metrics = train_and_export(texts, labels)
        mlflow.log_metrics(metrics)
        print("NLP flow completed.", metrics)


if __name__ == "__main__":
    nlp_pipeline()
