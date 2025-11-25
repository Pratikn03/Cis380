"""Simple Transformer and TCN sequence classifiers for behavior anomalies."""
from typing import Dict, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from uais.utils.logging_utils import setup_logging

logger = setup_logging(__name__)


class SequenceDataset(Dataset):
    def __init__(self, sequences: np.ndarray, labels: np.ndarray):
        self.sequences = torch.tensor(sequences, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self) -> int:  # pragma: no cover
        return len(self.labels)

    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


class TransformerClassifier(nn.Module):
    def __init__(self, input_dim: int, n_heads: int = 4, num_layers: int = 2, hidden_dim: int = 64):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(d_model=input_dim, nhead=n_heads, dim_feedforward=hidden_dim)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(input_dim, 1)

    def forward(self, x):
        # x shape: (batch, seq, feat); transformer expects (seq, batch, feat)
        x_t = x.transpose(0, 1)
        enc = self.encoder(x_t)
        pooled = enc.mean(dim=0)
        return self.fc(pooled).squeeze(-1)


class TCNBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int, kernel_size: int = 3, dilation: int = 1):
        super().__init__()
        padding = (kernel_size - 1) * dilation
        self.conv = nn.Conv1d(in_ch, out_ch, kernel_size, padding=padding, dilation=dilation)
        self.relu = nn.ReLU()
        self.bn = nn.BatchNorm1d(out_ch)

    def forward(self, x):
        out = self.conv(x)
        # remove padding on the right to keep length
        out = out[:, :, :-((self.conv.kernel_size[0] - 1) * self.conv.dilation[0])] if self.conv.kernel_size[0] > 1 else out
        return self.bn(self.relu(out))


class TCNClassifier(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64):
        super().__init__()
        self.block1 = TCNBlock(input_dim, hidden_dim, kernel_size=3, dilation=1)
        self.block2 = TCNBlock(hidden_dim, hidden_dim, kernel_size=3, dilation=2)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        # x shape: (batch, seq, feat) -> (batch, feat, seq)
        x = x.transpose(1, 2)
        out = self.block1(x)
        out = self.block2(out)
        pooled = self.pool(out).squeeze(-1)
        return self.fc(pooled).squeeze(-1)


def train_sequence_model(
    sequences: np.ndarray,
    labels: np.ndarray,
    config: Dict,
    model_type: str = "transformer",
) -> Tuple[nn.Module, float]:
    """Train a transformer or TCN classifier on sequence data."""
    batch_size = config.get("sequence", {}).get("batch_size", 64)
    epochs = config.get("sequence", {}).get("epochs", 5)
    lr = config.get("sequence", {}).get("lr", 1e-3)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = SequenceDataset(sequences, labels)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    input_dim = sequences.shape[-1]
    if model_type.lower() == "transformer":
        model = TransformerClassifier(input_dim)
    elif model_type.lower() == "tcn":
        model = TCNClassifier(input_dim)
    else:
        raise ValueError("model_type must be 'transformer' or 'tcn'")

    model.to(device)
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(batch_y)
        logger.info("%s epoch %s loss %.4f", model_type.upper(), epoch + 1, epoch_loss / len(dataset))
    return model, epoch_loss / len(dataset)


def predict_sequence_model(model: nn.Module, sequences: np.ndarray) -> np.ndarray:
    model.eval()
    device = next(model.parameters()).device
    with torch.no_grad():
        logits = model(torch.tensor(sequences, dtype=torch.float32, device=device))
        probs = torch.sigmoid(logits).cpu().numpy()
    return probs


__all__ = ["train_sequence_model", "predict_sequence_model", "TransformerClassifier", "TCNClassifier"]
