import importlib
import os
import tempfile
from typing import Any, Dict, Optional

import numpy as np


class WhisperSTT:
    """
    Offline STT using faster-whisper.
    """

    _model: Optional[Any] = None
    _model_cls: Optional[type] = None
    _decode_audio: Optional[Any] = None

    @staticmethod
    def _bool_env(name: str, default: str = "false") -> bool:
        return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}

    @classmethod
    def _get_model_cls(cls):
        if cls._model_cls is None:
            try:
                module = importlib.import_module("faster_whisper")
            except ImportError as exc:
                raise RuntimeError(
                    "`faster_whisper` is not installed in this environment."
                ) from exc
            cls._model_cls = getattr(module, "WhisperModel")
        return cls._model_cls

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            size = os.getenv("WHISPER_MODEL") or os.getenv("STT_MODEL_SIZE", "small")
            device = os.getenv("STT_DEVICE", "cpu")
            compute_type = os.getenv("STT_COMPUTE_TYPE")
            if not compute_type:
                device_lower = device.lower()
                if device_lower.startswith("cuda") or device_lower.startswith("gpu"):
                    compute_type = "float16"
                else:
                    compute_type = "int8"
            cls._model = cls._get_model_cls()(size, device=device, compute_type=compute_type)
        return cls._model

    @classmethod
    def _get_audio_decoder(cls):
        if cls._decode_audio is None:
            try:
                module = importlib.import_module("faster_whisper.audio")
            except ImportError as exc:
                raise RuntimeError(
                    "`faster_whisper` audio utilities are not available."
                ) from exc
            cls._decode_audio = getattr(module, "decode_audio")
        return cls._decode_audio

    @staticmethod
    def _normalize_audio(audio: np.ndarray) -> np.ndarray:
        if audio.size == 0:
            return audio.astype("float32", copy=False)
        audio = np.nan_to_num(audio, nan=0.0, posinf=0.0, neginf=0.0)
        peak = float(np.max(np.abs(audio)))
        target = float(os.getenv("STT_NORMALIZE_PEAK", "0.99"))
        if peak > 0 and peak > target:
            audio = audio * (target / peak)
        audio = np.clip(audio, -1.0, 1.0)
        return audio.astype("float32", copy=False)

    @classmethod
    def transcribe_file(cls, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        model = cls._get_model()
        normalize_audio = cls._bool_env("STT_NORMALIZE_AUDIO", "true")
        use_vad = cls._bool_env("STT_VAD_FILTER", "true")
        min_vad_sec = float(os.getenv("STT_VAD_MIN_DURATION_SEC", "1.0"))
        suppress_warnings = cls._bool_env("STT_SUPPRESS_NUMPY_WARNINGS", "true")

        def _run_transcribe(audio_input):
            return model.transcribe(
                audio_input,
                language=language,
                vad_filter=use_vad,
                vad_parameters={"min_silence_duration_ms": 400} if use_vad else None,
            )

        if normalize_audio:
            decode_audio = cls._get_audio_decoder()
            audio = decode_audio(audio_path, sampling_rate=16000)
            audio = cls._normalize_audio(np.asarray(audio))
            duration_sec = float(audio.shape[0]) / 16000.0 if audio.size else 0.0
            if duration_sec and duration_sec < min_vad_sec:
                use_vad = False
            if suppress_warnings:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    segments, info = _run_transcribe(audio)
            else:
                segments, info = _run_transcribe(audio)
        else:
            if suppress_warnings:
                with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
                    segments, info = _run_transcribe(audio_path)
            else:
                segments, info = _run_transcribe(audio_path)
        seg_out = []
        text_parts = []
        for s in segments:
            seg_out.append({"start": float(s.start), "end": float(s.end), "text": s.text})
            text_parts.append(s.text)
        return {
            "text": (" ".join(text_parts)).strip(),
            "segments": seg_out,
            "language": getattr(info, "language", None),
        }

    @classmethod
    def transcribe_bytes(
        cls, audio_bytes: bytes, suffix: str = ".wav", language: Optional[str] = None
    ) -> Dict[str, Any]:
        with tempfile.NamedTemporaryFile(delete=True, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            return cls.transcribe_file(tmp.name, language=language)
