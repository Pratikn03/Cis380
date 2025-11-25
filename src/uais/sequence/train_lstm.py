"""Lightweight LSTM classifier for sequence anomalies."""
from typing import Dict, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


class SequenceDataset(Dataset):
    def __init__(self, sequences: np.ndarray, mask: np.ndarray, labels: np.ndarray):
        self.sequences = torch.tensor(sequences, dtype=torch.float32)
        self.mask = torch.tensor(mask, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self) -> int:  # pragma: no cover - simple pass-through
        return len(self.labels)

    def __getitem__(self, idx):
        return self.sequences[idx], self.mask[idx], self.labels[idx]


class LSTMClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x, mask):
        lengths = mask.sum(dim=1).long()
        packed_output, (h_n, _) = self.lstm(x)
        last_hidden = h_n[-1]
        logits = self.fc(last_hidden).squeeze(-1)
        return logits


def train_lstm_classifier(
    sequences: np.ndarray,
    mask: np.ndarray,
    labels: np.ndarray,
    config: Dict,
) -> Tuple[LSTMClassifier, float]:
    input_dim = sequences.shape[-1]
    hidden_dim = config.get("sequence", {}).get("hidden_dim", 32)
    batch_size = config.get("sequence", {}).get("batch_size", 32)
    epochs = config.get("sequence", {}).get("epochs", 5)
    lr = config.get("sequence", {}).get("lr", 1e-3)

    dataset = SequenceDataset(sequences, mask, labels)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = LSTMClassifier(input_dim, hidden_dim)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_mask, batch_y in loader:
            optimizer.zero_grad()
            logits = model(batch_x, batch_mask)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(batch_y)
        logger.info("LSTM epoch %s loss %.4f", epoch + 1, epoch_loss / len(dataset))
    return model, epoch_loss / len(dataset)


def predict_lstm(model: LSTMClassifier, sequences: np.ndarray, mask: np.ndarray) -> np.ndarray:
    model.eval()
    with torch.no_grad():
        logits = model(torch.tensor(sequences, dtype=torch.float32), torch.tensor(mask, dtype=torch.float32))
        probs = torch.sigmoid(logits).numpy()
    return probs


__all__ = ["train_lstm_classifier", "predict_lstm", "LSTMClassifier"]
