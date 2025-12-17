from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset


class VideoClipDataset(Dataset):
    def __init__(self, root: str, clip_len: int = 16, size: int = 224):
        self.root = Path(root)
        self.clip_len = clip_len
        self.size = size
        self.items = self._collect()

    def _collect(self) -> List[Tuple[str, int]]:
        results: List[Tuple[str, int]] = []
        for label, sub in ((0, "real"), (1, "fake")):
            dir_path = self.root / sub
            if not dir_path.exists():
                continue
            for file_path in dir_path.rglob("*.mp4"):
                results.append((str(file_path), label))
        return results

    def _read_frames(self, path: str) -> List[np.ndarray]:
        cap = cv2.VideoCapture(path)
        frames: List[np.ndarray] = []
        while len(frames) < self.clip_len:
            ret, frame = cap.read()
            if not ret or frame is None:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (self.size, self.size))
            frame = frame.astype(np.float32) / 255.0
            frames.append(frame)
        cap.release()
        return frames

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        path, label = self.items[idx]
        frames = self._read_frames(path)
        if not frames:
            frames = [np.zeros((self.size, self.size, 3), dtype=np.float32)] * self.clip_len
        while len(frames) < self.clip_len:
            frames.append(frames[-1])
        clip = np.stack(frames[: self.clip_len])
        clip_tensor = torch.from_numpy(clip).permute(0, 3, 1, 2)
        return clip_tensor, torch.tensor([label], dtype=torch.float32)
