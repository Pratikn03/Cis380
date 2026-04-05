#!/usr/bin/env python3
"""Build a deterministic balanced voice dataset view under data/processed/voice_balanced.

Raw source data stays untouched. This script copies a deterministic subset for
majority classes and generates deterministic augmentations for minority classes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import wave
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

SUPPORTED = ["happy", "sad", "angry", "neutral", "fearful"]
AUGMENT_MODES = ("gain_up", "gain_down", "noise", "shift")


@dataclass
class ClassSummary:
    cls: str
    source_count: int
    target_count: int
    copied: int
    augmented: int


def _stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("::".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _read_wav_mono(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path), "rb") as handle:
        n_channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        n_frames = handle.getnframes()
        raw = handle.readframes(n_frames)

    if sample_width == 2:
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 1:
        audio = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        raise ValueError(f"unsupported sample width: {sample_width} bytes")

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)
    return sample_rate, audio


def _write_wav_mono(path: Path, sample_rate: int, audio: np.ndarray) -> None:
    clipped = np.clip(audio, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(pcm.tobytes())


def _augment(audio: np.ndarray, sample_rate: int, mode: str, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if mode == "gain_up":
        return np.clip(audio * 1.08, -1.0, 1.0)
    if mode == "gain_down":
        return np.clip(audio * 0.92, -1.0, 1.0)
    if mode == "noise":
        noise = rng.normal(0.0, 0.003, size=audio.shape[0]).astype(np.float32)
        return np.clip(audio + noise, -1.0, 1.0)
    if mode == "shift":
        max_shift = max(1, int(0.03 * sample_rate))
        shift = int(rng.integers(1, max_shift + 1))
        return np.roll(audio, shift)
    return audio


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_balanced_dataset(
    src_root: Path,
    dst_root: Path,
    *,
    target_per_class: int | None = None,
    seed: int = 42,
    clean: bool = True,
) -> dict[str, object]:
    class_files: dict[str, list[Path]] = {}
    for cls in SUPPORTED:
        src_dir = src_root / cls
        class_files[cls] = sorted(src_dir.glob("*.wav")) if src_dir.exists() else []

    available_counts = [len(paths) for paths in class_files.values() if paths]
    if not available_counts:
        raise FileNotFoundError(f"no wav files found under {src_root}")

    target = int(target_per_class) if target_per_class and target_per_class > 0 else max(available_counts)

    if clean and dst_root.exists():
        for cls in SUPPORTED:
            cls_dir = dst_root / cls
            if cls_dir.exists():
                shutil.rmtree(cls_dir)

    summaries: list[ClassSummary] = []
    for cls in SUPPORTED:
        src_files = class_files[cls]
        dst_dir = dst_root / cls
        dst_dir.mkdir(parents=True, exist_ok=True)

        copied = 0
        augmented = 0
        if not src_files:
            summaries.append(
                ClassSummary(
                    cls=cls,
                    source_count=0,
                    target_count=target,
                    copied=0,
                    augmented=0,
                )
            )
            continue

        # Deterministic downsampling for majority classes.
        ordered = sorted(
            src_files,
            key=lambda p: (hashlib.sha256(f"{seed}:{p.name}".encode("utf-8")).hexdigest(), p.name),
        )
        selected = ordered[:target]
        for src in selected:
            _copy_file(src, dst_dir / src.name)
            copied += 1

        deficit = target - copied
        for idx in range(max(0, deficit)):
            base = selected[idx % len(selected)]
            sample_rate, audio = _read_wav_mono(base)
            mode = AUGMENT_MODES[idx % len(AUGMENT_MODES)]
            aug_seed = _stable_seed(str(seed), cls, base.name, str(idx), mode)
            aug_audio = _augment(audio, sample_rate, mode, aug_seed)
            out_name = f"{base.stem}__aug_{idx:04d}_{mode}.wav"
            _write_wav_mono(dst_dir / out_name, sample_rate, aug_audio)
            augmented += 1

        summaries.append(
            ClassSummary(
                cls=cls,
                source_count=len(src_files),
                target_count=target,
                copied=copied,
                augmented=augmented,
            )
        )

    per_class = {row.cls: row.target_count for row in summaries}
    min_count = min(per_class.values()) if per_class else 0
    max_count = max(per_class.values()) if per_class else 0
    imbalance = round(max_count / min_count, 3) if min_count > 0 else None
    return {
        "generated_from": str(src_root),
        "generated_to": str(dst_root),
        "source_root_raw": str(src_root),
        "source_root_balanced": str(dst_root),
        "voice_source_resolution": "processed_balanced",
        "readiness_status": "ready",
        "status_vocabulary": {
            "canonical": ["ready", "degraded", "blocked", "advisory"],
            "legacy": ["ok", "warn", "missing"],
        },
        "seed": seed,
        "target_per_class": target,
        "summary": [asdict(row) for row in summaries],
        "class_balance": {
            "per_class": per_class,
            "missing_classes": [row.cls for row in summaries if row.target_count == 0],
            "imbalance_ratio_max_to_min_nonzero": imbalance,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic balanced voice dataset view.")
    parser.add_argument("--src-root", type=Path, default=Path("data/raw/voice"))
    parser.add_argument("--dst-root", type=Path, default=Path("data/processed/voice_balanced"))
    parser.add_argument(
        "--target-per-class",
        type=int,
        default=0,
        help="Target samples per class (0 -> max class size in source).",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Do not clean destination class folders before generating outputs.",
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("reports/voice_balanced_manifest.json"),
    )
    args = parser.parse_args()

    result = build_balanced_dataset(
        src_root=args.src_root,
        dst_root=args.dst_root,
        target_per_class=int(args.target_per_class) if int(args.target_per_class) > 0 else None,
        seed=int(args.seed),
        clean=not bool(args.no_clean),
    )
    args.report_path.parent.mkdir(parents=True, exist_ok=True)
    args.report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"[voice_balance] wrote {args.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
