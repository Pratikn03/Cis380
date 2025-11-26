"""Fine-tune DistilBERT on email/text anomalies.

Takes raw texts/labels, tokenizes, trains for a few epochs, and optionally
saves model/tokenizer to disk. Metrics are computed on the training set
for quick feedback (not a full validation pipeline).
"""
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset
from transformers import AdamW, get_linear_schedule_with_warmup

from uais_v.models.nlp_text_model import DistilBERTClassifier, NLPTextConfig, get_tokenizer
from uais_v.utils.seed import set_global_seed
from uais_v.evaluation.metrics import classification_metrics


class TextDataset(Dataset):
    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):  # pragma: no cover - trivial
        return len(self.texts)

    def __getitem__(self, idx):  # pragma: no cover - trivial
        enc = self.tokenizer(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in enc.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def train_distilbert(
    texts: List[str],
    labels: List[int],
    cfg: NLPTextConfig,
    batch_size: int = 8,
    epochs: int = 1,
    lr: float = 5e-5,
    save_dir: Path | None = None,
) -> tuple[DistilBERTClassifier, dict, Path | None]:
    set_global_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = get_tokenizer(cfg.model_name)

    dataset = TextDataset(texts, labels, tokenizer, cfg.max_length)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = DistilBERTClassifier(cfg.model_name, cfg.num_labels).to(device)
    optimizer = AdamW(model.parameters(), lr=lr)
    total_steps = len(loader) * epochs
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=0, num_training_steps=total_steps)
    if cfg.num_labels == 1:
        criterion = nn.BCEWithLogitsLoss()
    else:
        criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch in loader:
            optimizer.zero_grad()
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels_t = batch["labels"].to(device)
            logits = model(input_ids, attention_mask)
            if cfg.num_labels == 1:
                loss = criterion(logits.squeeze(-1), labels_t.float())
            else:
                loss = criterion(logits, labels_t)
            loss.backward()
            optimizer.step()
            scheduler.step()
            epoch_loss += loss.item() * len(labels_t)
        epoch_loss /= len(dataset)
        print(f"[NLP] epoch {epoch+1}/{epochs} loss {epoch_loss:.4f}")

    # simple eval on train set
    model.eval()
    all_logits = []
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(input_ids, attention_mask)
            all_logits.append(logits.cpu())
    logits = torch.cat(all_logits)
    if cfg.num_labels == 1:
        probs = torch.sigmoid(logits).numpy().ravel()
    else:
        probs = torch.softmax(logits, dim=1)[:, 1].numpy()

    metrics = classification_metrics(np.array(labels), probs, threshold=0.5)
    metrics["train_loss"] = float(epoch_loss)

    out_dir = None
    if save_dir is not None:
        out_dir = Path(save_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save(model.state_dict(), out_dir / "model.pt")
        tokenizer.save_pretrained(out_dir)
        print(f"Saved NLP model + tokenizer to {out_dir}")

    return model, metrics, out_dir


__all__ = ["train_distilbert", "TextDataset"]
