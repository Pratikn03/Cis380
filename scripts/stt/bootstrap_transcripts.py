from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.stt.whisper_stt import WhisperSTT  # noqa: E402

from scripts.stt.stt_utils import (  # noqa: E402
    SUPPORTED_AUDIO_EXTS,
    audio_duration_and_rate,
    iter_audio_files,
    parse_cremad_sentence_code,
    parse_cremad_speaker_id,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap STT transcripts with Whisper (offline)."
    )
    parser.add_argument(
        "--audio-root",
        type=Path,
        default=Path("data/raw/voice/AudioWAV"),
        help="Root directory containing audio files.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/raw/stt/transcripts.jsonl"),
        help="Output JSONL file.",
    )
    parser.add_argument("--language", type=str, default="en", help="Language code (default: en).")
    parser.add_argument("--limit", type=int, default=0, help="Max files to transcribe (0 = all).")
    parser.add_argument(
        "--include-segments", action="store_true", help="Include segment timestamps."
    )
    parser.add_argument(
        "--model-size",
        type=str,
        default="",
        help="Override Whisper model size (sets WHISPER_MODEL).",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip if transcript already exists in output file.",
    )
    parser.add_argument(
        "--errors",
        type=Path,
        default=Path("data/raw/stt/transcripts.errors.jsonl"),
        help="Error output JSONL file.",
    )
    parser.add_argument(
        "--by-sentence-code",
        action="store_true",
        help="Transcribe one sample per CREMA-D sentence code and reuse for all files.",
    )
    parser.add_argument(
        "--sentence-map-out",
        type=Path,
        default=Path("data/raw/stt/sentence_map.json"),
        help="Output JSON mapping for sentence code -> transcript.",
    )
    parser.add_argument(
        "--sentence-map-in",
        type=Path,
        default=None,
        help="Optional JSON mapping for sentence code -> transcript.",
    )
    parser.add_argument(
        "--samples-per-code",
        type=int,
        default=1,
        help="Number of samples to transcribe per sentence code when using --by-sentence-code.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output files instead of appending.",
    )
    return parser.parse_args()


def load_existing_paths(path: Path) -> set[str]:
    if not path.exists():
        return set()
    existing = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            audio_path = record.get("audio_path")
            if audio_path:
                existing.add(audio_path)
    return existing


def main() -> None:
    args = parse_args()
    audio_root = args.audio_root.resolve()
    out_path = args.out
    error_path = args.errors
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.model_size:
        os.environ["WHISPER_MODEL"] = args.model_size

    if not audio_root.exists():
        raise SystemExit(f"Audio root not found: {audio_root}")

    existing = load_existing_paths(out_path) if args.skip_existing else set()

    files = [p for p in iter_audio_files(audio_root, SUPPORTED_AUDIO_EXTS)]
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    output_mode = "w" if args.overwrite else "a"
    error_mode = "w" if args.overwrite else "a"

    with (
        out_path.open(output_mode, encoding="utf-8") as out_handle,
        error_path.open(error_mode, encoding="utf-8") as err_handle,
    ):
        if args.by_sentence_code:
            sentence_map = {}
            if args.sentence_map_in and args.sentence_map_in.exists():
                sentence_map = json.loads(args.sentence_map_in.read_text(encoding="utf-8"))
            else:
                code_samples: dict[str, list[Path]] = {}
                for path in files:
                    code = parse_cremad_sentence_code(path.name)
                    if not code:
                        continue
                    code_samples.setdefault(code, []).append(path)

                for code, sample_paths in code_samples.items():
                    texts = []
                    for sample in sample_paths[: max(1, args.samples_per_code)]:
                        try:
                            result = WhisperSTT.transcribe_file(str(sample), language=args.language)
                            text = (result.get("text") or "").strip()
                            if text:
                                texts.append(text)
                        except Exception:
                            continue
                    if texts:
                        text_choice = max(set(texts), key=texts.count)
                        sentence_map[code] = text_choice

                if args.sentence_map_out:
                    args.sentence_map_out.parent.mkdir(parents=True, exist_ok=True)
                    args.sentence_map_out.write_text(
                        json.dumps(sentence_map, indent=2), encoding="utf-8"
                    )

            for idx, path in enumerate(files, start=1):
                abs_path = path.resolve()
                try:
                    rel_path = str(abs_path.relative_to(PROJECT_ROOT))
                except ValueError:
                    rel_path = str(abs_path)
                if rel_path in existing:
                    continue
                code = parse_cremad_sentence_code(path.name)
                if not code or code not in sentence_map:
                    continue
                duration, sample_rate = audio_duration_and_rate(path)
                record = {
                    "audio_path": rel_path,
                    "text": sentence_map[code],
                    "language": args.language,
                    "speaker_id": parse_cremad_speaker_id(path.name),
                    "duration_sec": duration,
                    "sample_rate": sample_rate,
                    "source": "bootstrap_sentence_code",
                    "dataset": "crema_d",
                    "sentence_code": code,
                }
                out_handle.write(json.dumps(record, ensure_ascii=True) + "\n")
                if idx % 200 == 0:
                    print(f"[bootstrap] processed {idx}/{len(files)}")
            print(f"[bootstrap] wrote transcripts: {out_path}")
            return

        for idx, path in enumerate(files, start=1):
            abs_path = path.resolve()
            try:
                rel_path = str(abs_path.relative_to(PROJECT_ROOT))
            except ValueError:
                rel_path = str(abs_path)
            if rel_path in existing:
                continue
            try:
                result = WhisperSTT.transcribe_file(str(path), language=args.language)
                duration, sample_rate = audio_duration_and_rate(path)
                record = {
                    "audio_path": rel_path,
                    "text": (result.get("text") or "").strip(),
                    "language": result.get("language") or args.language,
                    "speaker_id": parse_cremad_speaker_id(path.name),
                    "duration_sec": duration,
                    "sample_rate": sample_rate,
                    "source": "bootstrap_whisper",
                    "dataset": "crema_d",
                }
                if args.include_segments:
                    record["segments"] = result.get("segments", [])
                out_handle.write(json.dumps(record, ensure_ascii=True) + "\n")
                out_handle.flush()
                if idx % 50 == 0:
                    print(f"[bootstrap] processed {idx}/{len(files)}")
            except Exception as exc:
                err = {
                    "audio_path": rel_path,
                    "error": str(exc),
                }
                err_handle.write(json.dumps(err, ensure_ascii=True) + "\n")
                err_handle.flush()

    print(f"[bootstrap] wrote transcripts: {out_path}")


if __name__ == "__main__":
    main()
