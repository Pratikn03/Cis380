from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass
class AudioBatch:
    input_values: list[list[float]]
    labels: list[int]


def load_manifest(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"path", "label"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"manifest missing columns: {sorted(missing)}")
    return df


def build_label_maps(df: pd.DataFrame) -> tuple[dict[str, int], dict[int, str]]:
    labels = sorted({str(v) for v in df["label"].unique()})
    label2id = {label: i for i, label in enumerate(labels)}
    id2label = {i: label for label, i in label2id.items()}
    return label2id, id2label


def _read_existing_label2id(path: Path) -> dict[str, int] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"could not read SSL voice label map: {path}: {exc}") from exc
    raw = payload.get("label2id")
    if not isinstance(raw, dict):
        return None
    try:
        return {str(label): int(idx) for label, idx in raw.items()}
    except Exception as exc:
        raise SystemExit(f"invalid SSL voice label map: {path}: {exc}") from exc


def ensure_compatible_label_map(
    output_dir: Path,
    expected_label2id: dict[str, int],
    *,
    resume_from_checkpoint: str | None,
) -> None:
    """Reject stale SSL output dirs before mixing incompatible artifacts.

    Interrupted runs can leave a fresh run_config.json beside an old label_map.json
    and model checkpoint. That makes evaluation/prediction fail later in a less
    obvious way, so fail early unless the existing labels exactly match the new run.
    """

    expected = {str(label): int(idx) for label, idx in expected_label2id.items()}
    label_sources = [output_dir / "label_map.json", output_dir / "config.json"]
    for source in label_sources:
        existing = _read_existing_label2id(source)
        if existing is None or existing == expected:
            continue
        missing = sorted(set(expected) - set(existing))
        extra = sorted(set(existing) - set(expected))
        resume_hint = (
            f" resume_from_checkpoint={resume_from_checkpoint!r} was provided,"
            if resume_from_checkpoint
            else ""
        )
        raise SystemExit(
            "stale SSL voice output directory: "
            f"{output_dir}.{resume_hint} Existing labels do not match this run. "
            f"missing={missing} extra={extra}. "
            "Use a fresh --output-dir or remove the stale SSL artifact first."
        )


def resolve_trainer_eval_sampler(trainer: Any, eval_dataset: Any) -> Any:
    sampler_fn = getattr(trainer, "get_eval_sampler", None)
    if sampler_fn is None:
        sampler_fn = getattr(trainer, "_get_eval_sampler", None)
    if sampler_fn is None:
        return None
    return sampler_fn(eval_dataset)


def _resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return audio
    try:
        import torchaudio
        import torch

        waveform = torch.from_numpy(audio.astype(np.float32)).unsqueeze(0)
        resampled = torchaudio.functional.resample(waveform, orig_sr, target_sr)
        return resampled.squeeze(0).cpu().numpy()
    except Exception:
        pass
    try:
        import librosa  # type: ignore

        return librosa.resample(audio, orig_sr=orig_sr, target_sr=target_sr)
    except Exception as exc:
        raise SystemExit(
            "Resampling requires torchaudio or librosa. "
            "Install one of them or provide already-resampled audio."
        ) from exc


def resolve_audio_path(path: str) -> Path:
    """Resolve stale manifest paths against the local voice audio directory."""
    candidate = Path(path)
    if candidate.exists():
        return candidate

    basename = candidate.name
    local_audio = Path("data/raw/voice/AudioWAV") / basename
    if local_audio.exists():
        return local_audio

    matches = list(Path("data/raw/voice").glob(f"**/{basename}"))
    if matches:
        return matches[0]

    return candidate


def load_audio(path: str, target_sr: int) -> np.ndarray:
    try:
        import soundfile as sf
    except Exception as exc:
        raise SystemExit("soundfile is required for SSL voice training.") from exc

    audio_path = resolve_audio_path(path)
    audio, sr = sf.read(audio_path)
    if audio.ndim > 1:
        audio = np.mean(audio, axis=1)
    audio = audio.astype(np.float32)
    audio = _resample_audio(audio, sr, target_sr)
    return audio


def prepare_dataset(
    df: pd.DataFrame, feature_extractor: Any, label2id: dict[str, int], num_workers: int
):
    import datasets

    target_sr = int(getattr(feature_extractor, "sampling_rate", 16000))
    df = df.copy()
    df["label_id"] = df["label"].map(label2id)
    if df["label_id"].isna().any():
        missing = sorted({str(v) for v in df[df["label_id"].isna()]["label"].unique()})
        raise SystemExit(f"labels missing from label2id: {missing}")
    dataset = datasets.Dataset.from_pandas(df)

    def _prepare(batch):
        audio = load_audio(batch["path"], target_sr)
        inputs = feature_extractor(audio, sampling_rate=target_sr)
        batch["input_values"] = inputs["input_values"][0]
        batch["labels"] = int(batch["label_id"])
        return batch

    columns = dataset.column_names
    dataset = dataset.map(_prepare, remove_columns=columns, num_proc=max(1, int(num_workers)))
    return dataset


class AudioDataCollator:
    def __init__(self, feature_extractor: Any):
        self.feature_extractor = feature_extractor

    def __call__(self, features: list[dict[str, Any]]):
        import torch

        input_features = [{"input_values": f["input_values"]} for f in features]
        batch = self.feature_extractor.pad(input_features, return_tensors="pt")
        labels = torch.tensor([int(f["labels"]) for f in features], dtype=torch.long)
        batch["labels"] = labels
        return batch
