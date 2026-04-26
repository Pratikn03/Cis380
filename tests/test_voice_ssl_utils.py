from scripts.voice.ssl_utils import resolve_audio_path


def test_resolve_audio_path_falls_back_to_audio_wav_basename() -> None:
    resolved = resolve_audio_path("/stale/root/data/raw/voice/angry/1001_DFA_ANG_XX.wav")

    assert resolved.as_posix() == "data/raw/voice/AudioWAV/1001_DFA_ANG_XX.wav"
