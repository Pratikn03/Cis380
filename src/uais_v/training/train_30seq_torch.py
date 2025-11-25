"""PyTorch training loop for the multi-sequence TCN classifier."""
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from uais_v.evaluation.metrics import classification_metrics
from uais_v.models.multi_sequence_30_torch import MultiSequenceTCNClassifier
from uais_v.utils.seed import set_global_seed


class Sequence30Dataset(Dataset):
    def __init__(self, X_tensor: torch.Tensor, y: np.ndarray):
        self.X = X_tensor  # shape (N, 30, seq_len, feat)
        self.y = torch.tensor(y, dtype=torch.long)

    def __len__(self):  # pragma: no cover - trivial
        return self.X.shape[0]

    def __getitem__(self, idx):  # pragma: no cover - trivial
        return self.X[idx], self.y[idx]


def dict_to_tensor(X_dict: Dict[str, np.ndarray], device: torch.device) -> torch.Tensor:
    keys = sorted(X_dict.keys())
    arrays = [torch.tensor(X_dict[k], dtype=torch.float32) for k in keys]
    stacked = torch.stack(arrays, dim=1)  # (N, 30, seq_len, feat)
    return stacked.to(device)


def train_torch_30seq(
    X_dict: Dict[str, np.ndarray],
    y: np.ndarray,
    batch_size: int = 32,
    epochs: int = 10,
    lr: float = 1e-3,
    latent_dim: int = 64,
    num_outputs: int = 2,
) -> Tuple[MultiSequenceTCNClassifier, Dict[str, float]]:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X_tensor = dict_to_tensor(X_dict, device)
    dataset = Sequence30Dataset(X_tensor, y)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = MultiSequenceTCNClassifier(
        seq_len=X_tensor.shape[2],
        n_features=X_tensor.shape[3],
        latent_dim=latent_dim,
        num_outputs=num_outputs,
    ).to(device)

    if num_outputs == 1:
        criterion = nn.BCEWithLogitsLoss()
    else:
        criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            logits = model(batch_x)
            if num_outputs == 1:
                labels = batch_y.float()
                loss = criterion(logits, labels)
                probs = torch.sigmoid(logits)
            else:
                loss = criterion(logits, batch_y)
                probs = torch.softmax(logits, dim=1)[:, 1]
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(batch_y)
        epoch_loss /= len(dataset)
        print(f"[Torch 30seq] epoch {epoch+1}/{epochs} loss {epoch_loss:.4f}")

    model.eval()
    with torch.no_grad():
        logits = model(X_tensor)
        if num_outputs == 1:
            probs = torch.sigmoid(logits).cpu().numpy()
        else:
            probs = torch.softmax(logits, dim=1)[:, 1].cpu().numpy()
    metrics = classification_metrics(y, probs, threshold=0.5)
    metrics["train_loss"] = float(epoch_loss)
    return model, metrics


def save_torch_model(model: nn.Module, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), path)


__all__ = ["train_torch_30seq", "save_torch_model", "dict_to_tensor", "Sequence30Dataset"]
