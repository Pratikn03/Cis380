from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from pathlib import Path
from typing import Iterable, Optional, Tuple

SUPPORTED_AUDIO_EXTS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}


def iter_audio_files(root: Path, exts: Iterable[str] = SUPPORTED_AUDIO_EXTS) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in exts:
            yield path


def parse_cremad_speaker_id(filename: str) -> Optional[str]:
    # CREMA-D pattern: 1001_DFA_ANG_XX.wav -> speaker_id = 1001
    match = re.match(r"^(\d+)_", filename)
    if match:
        return match.group(1)
    return None


def parse_cremad_sentence_code(filename: str) -> Optional[str]:
    # CREMA-D pattern: 1001_DFA_ANG_XX.wav -> sentence code = DFA
    parts = filename.split("_")
    if len(parts) >= 2:
        return parts[1]
    return None


def _ffprobe_available() -> bool:
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def audio_duration_and_rate(path: Path) -> Tuple[Optional[float], Optional[int]]:
    if path.suffix.lower() == ".wav":
        try:
            import wave

            with wave.open(str(path), "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate) if rate else None
                return duration, rate
        except Exception:
            pass

    if not _ffprobe_available():
        return None, None

    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=sample_rate,duration",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return None, None
        payload = json.loads(result.stdout or "{}")
        streams = payload.get("streams") or []
        if not streams:
            return None, None
        stream = streams[0]
        duration = stream.get("duration")
        sample_rate = stream.get("sample_rate")
        return (float(duration) if duration is not None else None), (
            int(sample_rate) if sample_rate else None
        )
    except Exception:
        return None, None


def normalize_text(text: str) -> str:
    """
    Normalize transcripts for ASR training/evaluation.
    - lowercases
    - strips unicode accents
    - removes bracketed tags like [noise], (laughter), <unk>
    - normalizes symbols (& -> and)
    - removes punctuation (keeps apostrophes within words)
    """
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"\[[^\]]+\]|\([^)]+\)|<[^>]+>", " ", text)
    text = text.replace("&", " and ")
    text = text.replace("’", "'").replace("`", "'")
    # Remove punctuation except apostrophes within words.
    text = re.sub(r"[^a-z0-9'\s]", " ", text)
    # Remove standalone apostrophes.
    text = re.sub(r"\s'\s", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def levenshtein_distance(seq_a: list[str], seq_b: list[str]) -> int:
    if seq_a == seq_b:
        return 0
    if not seq_a:
        return len(seq_b)
    if not seq_b:
        return len(seq_a)
    dp = list(range(len(seq_b) + 1))
    for i, token_a in enumerate(seq_a, start=1):
        prev = dp[0]
        dp[0] = i
        for j, token_b in enumerate(seq_b, start=1):
            temp = dp[j]
            cost = 0 if token_a == token_b else 1
            dp[j] = min(
                dp[j] + 1,  # deletion
                dp[j - 1] + 1,  # insertion
                prev + cost,  # substitution
            )
            prev = temp
    return dp[-1]


def compute_wer(reference: str, hypothesis: str) -> float:
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    distance = levenshtein_distance(ref_words, hyp_words)
    return distance / len(ref_words)


def compute_cer(reference: str, hypothesis: str) -> float:
    ref_chars = list(reference)
    hyp_chars = list(hypothesis)
    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0
    distance = levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars)
