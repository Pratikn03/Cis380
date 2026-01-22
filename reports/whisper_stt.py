"""
Whisper STT service module.
"""

from typing import Any, Dict, Optional


class WhisperSTT:
    @staticmethod
    def transcribe_bytes(
        audio_bytes: bytes, suffix: str = ".wav", language: Optional[str] = None
    ) -> Dict[str, Any]:
        # Mock implementation
        return {
            "text": "This is a simulated transcription of the audio.",
            "segments": [
                {
                    "start": 0.0,
                    "end": 1.0,
                    "text": "This is a simulated transcription of the audio.",
                }
            ],
            "language": language or "en",
        }
