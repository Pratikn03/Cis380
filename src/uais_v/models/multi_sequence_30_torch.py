"""Multi-sequence TCN classifier in PyTorch (faster CPU/GPU alternative)."""
from typing import Dict

import torch
from torch import nn


class TCNEncoder(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2, kernel_size: int = 3):
        super().__init__()
        layers = []
        in_ch = input_dim
        for i in range(num_layers):
            dilation = 2 ** i
            padding = (kernel_size - 1) * dilation
            conv = nn.Conv1d(in_ch, hidden_dim, kernel_size, padding=padding, dilation=dilation)
            layers += [conv, nn.ReLU(), nn.BatchNorm1d(hidden_dim)]
            in_ch = hidden_dim
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, seq_len, feat)
        x = x.transpose(1, 2)  # (batch, feat, seq_len)
        out = self.net(x)
        # remove right-side padding to original length
        out = out[..., : x.shape[-1]]
        pooled = out.mean(dim=2)  # global average pool over time -> (batch, hidden_dim)
        return pooled


class MultiSequenceTCNClassifier(nn.Module):
    def __init__(
        self,
        seq_len: int = 30,
        n_features: int = 16,
        latent_dim: int = 64,
        num_outputs: int = 2,
    ):
        super().__init__()
        self.num_sequences = 30
        self.num_outputs = num_outputs
        self.encoder = TCNEncoder(n_features, hidden_dim=latent_dim, num_layers=2)
        merged_dim = latent_dim * self.num_sequences

        self.head = nn.Sequential(
            nn.Linear(merged_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
        )
        self.out = nn.Linear(128, num_outputs)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (batch, num_seq, seq_len, feat)
        batch_size = x.size(0)
        encodings = []
        for i in range(self.num_sequences):
            enc = self.encoder(x[:, i, :, :])  # (batch, latent_dim)
            encodings.append(enc)
        merged = torch.cat(encodings, dim=1)  # (batch, latent_dim * num_seq)
        feats = self.head(merged)
        logits = self.out(feats)
        if self.num_outputs == 1:
            logits = logits.squeeze(-1)
        return logits


__all__ = ["MultiSequenceTCNClassifier", "TCNEncoder"]
