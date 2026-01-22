"""
Temporal deepfake detection model.
"""
import torch
import torch.nn as nn

class TemporalDeepfakeLSTM(nn.Module):
    def __init__(self, hidden: int = 256, backbone: str = "mobilenet_v3_small", freeze_backbone: bool = True):
        super().__init__()
        self.backbone = nn.Identity() # Mock backbone
        self.lstm = nn.LSTM(input_size=10, hidden_size=hidden, batch_first=True) # Mock input size
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        # x shape: (batch, frames, channels, height, width)
        # Mock forward pass
        batch_size = x.size(0)
        return torch.zeros(batch_size, 1)