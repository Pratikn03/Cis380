from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.stt.whisper_stt import WhisperSTT  # noqa: E402
from scripts.stt.stt_utils import compute_cer, compute_wer, normalize_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate STT with WER/CER.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/raw/stt/manifest.with_splits.csv"),
        help="Manifest CSV with transcripts.",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        help="Split to evaluate (requires split column).",
    )
    parser.add_argument("--limit", type=int, default=0, help="Limit number of samples.")
    parser.add_argument("--language", type=str, default="en", help="Language code.")
    parser.add_argument(
        "--model-size",
        type=str,
        default="",
        help="Override Whisper model size (sets WHISPER_MODEL).",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Normalize reference and hypothesis text.",
    )
    parser.add_argument(
        "--by-sentence-code",
        action="store_true",
        help="Evaluate by sentence code using a few samples per code (fast).",
    )
    parser.add_argument(
        "--samples-per-code",
        type=int,
        default=2,
        help="Number of samples to transcribe per sentence code.",
    )
    parser.add_argument(
        "--sentence-code-field",
        type=str,
        default="sentence_code",
        help="Manifest column used for sentence code grouping.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("reports/stt_eval.json"),
        help="Output summary JSON.",
    )
    parser.add_argument(
        "--predictions",
        type=Path,
        default=Path("reports/stt_eval_predictions.jsonl"),
        help="Output per-sample predictions JSONL.",
    )
    return parser.parse_args()


def load_manifest(path: Path, split: str | None) -> List[Dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    rows: List[Dict[str, str]] = []
    if split and split.lower() in {"all", "*", "none"}:
        split = None
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if split and row.get("split") and row.get("split") != split:
                continue
            rows.append(row)
    return rows


def main() -> None:
    args = parse_args()
    if args.model_size:
        os.environ["WHISPER_MODEL"] = args.model_size

    rows = load_manifest(args.manifest, args.split)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]
    if not rows:
        raise SystemExit("No rows found for evaluation.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.predictions.parent.mkdir(parents=True, exist_ok=True)

    total_wer = 0.0
    total_cer = 0.0
    total_latency = 0.0
    total = 0
    errors = 0

    with args.predictions.open("w", encoding="utf-8") as pred_handle:
        if args.by_sentence_code:
            code_field = args.sentence_code_field
            grouped: Dict[str, List[Dict[str, str]]] = {}
            for row in rows:
                code = row.get(code_field) or "unknown"
                grouped.setdefault(code, []).append(row)

            for code, group_rows in grouped.items():
                sample_rows = group_rows[: max(1, args.samples_per_code)]
                code_wer = []
                code_cer = []
                code_latency = []
                for row in sample_rows:
                    audio_path = row.get("audio_path") or ""
                    ref_text = (row.get("text") or "").strip()
                    if args.normalize:
                        ref_text = normalize_text(ref_text)
                    if not audio_path:
                        errors += 1
                        continue
                    start = time.perf_counter()
                    try:
                        result = WhisperSTT.transcribe_file(audio_path, language=args.language)
                        hyp_text = (result.get("text") or "").strip()
                        if args.normalize:
                            hyp_text = normalize_text(hyp_text)
                        latency = time.perf_counter() - start
                        sample_wer = compute_wer(ref_text, hyp_text)
                        sample_cer = compute_cer(ref_text, hyp_text)
                        code_wer.append(sample_wer)
                        code_cer.append(sample_cer)
                        code_latency.append(latency)
                        pred_handle.write(
                            json.dumps(
                                {
                                    "audio_path": audio_path,
                                    "reference": ref_text,
                                    "hypothesis": hyp_text,
                                    "wer": sample_wer,
                                    "cer": sample_cer,
                                    "latency_sec": latency,
                                    "sentence_code": code,
                                },
                                ensure_ascii=True,
                            )
                            + "\n"
                        )
                    except Exception as exc:
                        errors += 1
                        pred_handle.write(
                            json.dumps(
                                {"audio_path": audio_path, "error": str(exc)},
                                ensure_ascii=True,
                            )
                            + "\n"
                        )

                if code_wer:
                    weight = len(group_rows)
                    avg_code_wer = sum(code_wer) / len(code_wer)
                    avg_code_cer = sum(code_cer) / len(code_cer)
                    avg_code_latency = sum(code_latency) / len(code_latency)
                    total_wer += avg_code_wer * weight
                    total_cer += avg_code_cer * weight
                    total_latency += avg_code_latency * weight
                    total += weight
        else:
            for row in rows:
                audio_path = row.get("audio_path") or ""
                ref_text = (row.get("text") or "").strip()
                if args.normalize:
                    ref_text = normalize_text(ref_text)
                if not audio_path:
                    errors += 1
                    continue
                start = time.perf_counter()
                try:
                    result = WhisperSTT.transcribe_file(audio_path, language=args.language)
                    hyp_text = (result.get("text") or "").strip()
                    if args.normalize:
                        hyp_text = normalize_text(hyp_text)
                    latency = time.perf_counter() - start
                    sample_wer = compute_wer(ref_text, hyp_text)
                    sample_cer = compute_cer(ref_text, hyp_text)
                    total_wer += sample_wer
                    total_cer += sample_cer
                    total_latency += latency
                    total += 1
                    pred_handle.write(
                        json.dumps(
                            {
                                "audio_path": audio_path,
                                "reference": ref_text,
                                "hypothesis": hyp_text,
                                "wer": sample_wer,
                                "cer": sample_cer,
                                "latency_sec": latency,
                            },
                            ensure_ascii=True,
                        )
                        + "\n"
                    )
                except Exception as exc:
                    errors += 1
                    pred_handle.write(
                        json.dumps(
                            {"audio_path": audio_path, "error": str(exc)},
                            ensure_ascii=True,
                        )
                        + "\n"
                    )

    summary = {
        "samples": total,
        "errors": errors,
        "avg_wer": (total_wer / total) if total else None,
        "avg_cer": (total_cer / total) if total else None,
        "avg_latency_sec": (total_latency / total) if total else None,
        "language": args.language,
        "model": os.getenv("WHISPER_MODEL", "base"),
        "split": args.split,
        "manifest": str(args.manifest),
        "evaluation_mode": "by_sentence_code" if args.by_sentence_code else "full",
    }

    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(f"[stt_eval] wrote summary: {args.out}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
