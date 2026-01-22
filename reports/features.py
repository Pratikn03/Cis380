import numpy as np
import librosa

def load_audio(path: str, sr: int = 16000):
    """Load audio file using librosa."""
    try:
        y, sr = librosa.load(path, sr=sr)
        return y, sr
    except Exception:
        # Return silent audio on failure
        return np.zeros(sr), sr

def extract_mfcc(y, sr, n_mfcc=40):
    """Extract MFCC features."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.mean(mfcc.T, axis=0)

def compute_zero_crossing_rate(y):
    """Compute Zero Crossing Rate."""
    return np.mean(librosa.feature.zero_crossing_rate(y))

def compute_rms(y):
    """Compute Root Mean Square energy."""
    rms = librosa.feature.rms(y=y)
    return np.mean(rms), np.std(rms)