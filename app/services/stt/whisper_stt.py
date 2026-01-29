import importlib
import os
import tempfile
from typing import Dict, Any, Optional


class WhisperSTT:
    """
    Offline STT using faster-whisper.
    """

    _model: Optional[Any] = None
    _model_cls: Optional[type] = None

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
            compute_type = os.getenv("STT_COMPUTE_TYPE", "int8")
            cls._model = cls._get_model_cls()(size, device=device, compute_type=compute_type)
        return cls._model

    @classmethod
    def transcribe_file(cls, audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        model = cls._get_model()
        segments, info = model.transcribe(
            audio_path,
            language=language,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 400},
        )
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
