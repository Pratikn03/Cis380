#!/usr/bin/env python3
"""Experimental: enhanced voice emotion training script (target >80% accuracy).

This is not part of the canonical training pipeline. See `scripts/train_all.py`.
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("  TRAINING VOICE EMOTION MODEL")
print("  Target: >80% accuracy (current: 57.64%)")
print("=" * 60)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VOICE_DIR = PROJECT_ROOT / "data/raw/voice"
CREMA_DIR = PROJECT_ROOT / "data/raw/crema_d/audio_wav"

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    print("⚠️ librosa not installed, using simple features")
    HAS_LIBROSA = False
    import scipy.io.wavfile as wav

# Emotion mappings
EMOTIONS = ['angry', 'happy', 'neutral', 'sad', 'fearful']
CREMA_MAP = {'ANG': 'angry', 'HAP': 'happy', 'NEU': 'neutral', 'SAD': 'sad', 'FEA': 'fearful', 'DIS': 'angry'}

def extract_features_simple(audio_path, max_len=128):
    """Extract simple features without librosa"""
    try:
        sr, audio = wav.read(audio_path)
        audio = audio.astype(np.float32)
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)
        
        # Normalize
        audio = audio / (np.max(np.abs(audio)) + 1e-8)
        
        # Simple features
        features = []
        
        # Basic stats
        features.extend([
            np.mean(audio),
            np.std(audio),
            np.max(audio),
            np.min(audio),
            np.mean(np.abs(audio)),
        ])
        
        # Zero crossing rate
        zcr = np.sum(np.abs(np.diff(np.signbit(audio)))) / len(audio)
        features.append(zcr)
        
        # Energy
        energy = np.sum(audio**2) / len(audio)
        features.append(energy)
        
        # Segment-wise stats (divide into 10 segments)
        seg_len = len(audio) // 10
        for i in range(10):
            seg = audio[i*seg_len:(i+1)*seg_len]
            if len(seg) > 0:
                features.extend([np.mean(seg), np.std(seg), np.max(np.abs(seg))])
        
        # FFT features
        fft = np.abs(np.fft.fft(audio))[:len(audio)//2]
        fft_norm = fft / (np.max(fft) + 1e-8)
        
        # Spectral centroid approximation
        freqs = np.arange(len(fft_norm))
        spectral_centroid = np.sum(freqs * fft_norm) / (np.sum(fft_norm) + 1e-8)
        features.append(spectral_centroid / len(fft_norm))
        
        # Spectral rolloff
        cumsum = np.cumsum(fft_norm)
        rolloff = np.searchsorted(cumsum, 0.85 * cumsum[-1]) / len(fft_norm)
        features.append(rolloff)
        
        # Spectral bandwidth
        spectral_bandwidth = np.sqrt(np.sum(((freqs - spectral_centroid)**2) * fft_norm) / (np.sum(fft_norm) + 1e-8))
        features.append(spectral_bandwidth / len(fft_norm))
        
        # FFT bin stats (10 bins)
        bin_size = len(fft_norm) // 10
        for i in range(10):
            bin_data = fft_norm[i*bin_size:(i+1)*bin_size]
            if len(bin_data) > 0:
                features.extend([np.mean(bin_data), np.max(bin_data)])
        
        return np.array(features, dtype=np.float32)
    except Exception as e:
        return None


def extract_features_librosa(audio_path, max_len=128):
    """Extract features using librosa"""
    try:
        y, sr = librosa.load(audio_path, sr=22050, duration=3.0)
        
        # Mel spectrogram
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=40, fmax=8000)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        
        # Pad or truncate to fixed length
        if mel_db.shape[1] < max_len:
            mel_db = np.pad(mel_db, ((0, 0), (0, max_len - mel_db.shape[1])), mode='constant')
        else:
            mel_db = mel_db[:, :max_len]
        
        # MFCC statistics
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        mfcc_mean = np.mean(mfcc, axis=1)
        mfcc_std = np.std(mfcc, axis=1)
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Spectral features
        spec_cent = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
        spec_bw = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        spec_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        
        # Zero crossing rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(y))
        
        # RMS energy
        rms = np.mean(librosa.feature.rms(y=y))
        
        # Combine all features
        extra = np.concatenate([
            mfcc_mean, mfcc_std, chroma_mean,
            [spec_cent, spec_bw, spec_rolloff, zcr, rms]
        ])
        
        return np.concatenate([mel_db.flatten(), extra])
    except Exception as e:
        return None


extract_features = extract_features_librosa if HAS_LIBROSA else extract_features_simple

print("\n📂 Loading voice data from multiple sources...")

X = []
y = []

# 1. Load from VOICE_DIR (organized folders)
for emotion in EMOTIONS:
    folder = VOICE_DIR / emotion
    if folder.exists():
        files = list(folder.glob("*.wav"))[:500]  # Limit per class
        count = 0
        for f in files:
            feat = extract_features(f)
            if feat is not None:
                X.append(feat)
                y.append(emotion)
                count += 1
        print(f"  {emotion}: {count} files")

# 2. Load RAVDESS data
ravdess_dir = VOICE_DIR / "_ravdess"
if ravdess_dir.exists():
    ravdess_map = {'01': 'neutral', '02': 'neutral', '03': 'happy', '04': 'sad', 
                   '05': 'angry', '06': 'fearful', '07': 'angry', '08': 'happy'}
    count = 0
    for f in list(ravdess_dir.glob("**/*.wav"))[:1500]:
        try:
            parts = f.stem.split('-')
            if len(parts) >= 3:
                emotion_code = parts[2]
                if emotion_code in ravdess_map:
                    feat = extract_features(f)
                    if feat is not None:
                        X.append(feat)
                        y.append(ravdess_map[emotion_code])
                        count += 1
        except:
            continue
    print(f"  RAVDESS: {count} files")

# 3. Load TESS data  
tess_dir = VOICE_DIR / "_tess"
if tess_dir.exists():
    tess_map = {'angry': 'angry', 'happy': 'happy', 'neutral': 'neutral', 
                'sad': 'sad', 'fear': 'fearful', 'disgust': 'angry', 'ps': 'happy'}
    count = 0
    for f in list(tess_dir.glob("**/*.wav"))[:2000]:
        try:
            name_lower = f.stem.lower()
            for key, emotion in tess_map.items():
                if key in name_lower:
                    feat = extract_features(f)
                    if feat is not None:
                        X.append(feat)
                        y.append(emotion)
                        count += 1
                    break
        except:
            continue
    print(f"  TESS: {count} files")

# 4. Load CREMA-D
if CREMA_DIR.exists():
    count = 0
    for f in list(CREMA_DIR.glob("*.wav"))[:2000]:
        try:
            parts = f.stem.split('_')
            if len(parts) >= 3:
                emotion_code = parts[2]
                if emotion_code in CREMA_MAP:
                    feat = extract_features(f)
                    if feat is not None:
                        X.append(feat)
                        y.append(CREMA_MAP[emotion_code])
                        count += 1
        except:
            continue
    print(f"  CREMA-D: {count} files")

print(f"\n📊 Total samples: {len(y)}")
print(f"   Distribution: {Counter(y)}")

if len(y) < 100:
    print("❌ Not enough data!")
    exit(1)

# Convert to arrays
X = np.array(X, dtype=np.float32)

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Normalize
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split
X_train, X_val, y_train, y_val = train_test_split(X_scaled, y_encoded, test_size=0.2, stratify=y_encoded, random_state=42)

print(f"   Train: {len(X_train)}, Val: {len(X_val)}")

# PyTorch training
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
print(f"   Device: {device}")

train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train, dtype=torch.long))
val_dataset = TensorDataset(torch.tensor(X_val), torch.tensor(y_val, dtype=torch.long))

train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=64)

# Neural Network Model
class VoiceEmotionNet(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.net(x)

input_size = X_scaled.shape[1]
num_classes = len(le.classes_)

model = VoiceEmotionNet(input_size, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=3, factor=0.5)

print("\n🚀 Training Voice Emotion Neural Network...")

best_acc = 0
epochs = 30

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        optimizer.zero_grad()
        outputs = model(X_batch)
        loss = criterion(outputs, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
    
    # Validation
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            outputs = model(X_batch)
            _, predicted = torch.max(outputs, 1)
            total += y_batch.size(0)
            correct += (predicted == y_batch).sum().item()
    
    val_acc = correct / total * 100
    scheduler.step(1 - val_acc/100)
    
    if val_acc > best_acc:
        best_acc = val_acc
        # Save best model
        torch.save({
            'model_state': model.state_dict(),
            'scaler': scaler,
            'label_encoder': le,
            'input_size': input_size
        }, PROJECT_ROOT / "models/voice_emotion_nn.pt")
    
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"  Epoch {epoch+1}/{epochs} - Loss: {train_loss/len(train_loader):.4f}, Val Acc: {val_acc:.2f}%")

print(f"\n✅ Best Voice Emotion NN Accuracy: {best_acc:.2f}%")
print(f"✅ Saved: models/voice_emotion_nn.pt")

# Also train sklearn MLP for backward compatibility
print("\n📦 Training sklearn MLP backup model...")
mlp = MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=300, early_stopping=True, random_state=42)
mlp.fit(X_train, y_train)
mlp_acc = mlp.score(X_val, y_val) * 100
print(f"  MLP Accuracy: {mlp_acc:.2f}%")

# Save as pickle for compatibility
joblib.dump({
    'model': mlp,
    'scaler': scaler,
    'label_encoder': le
}, PROJECT_ROOT / "models/voice_emotion.pkl")
print(f"✅ Saved: models/voice_emotion.pkl")

print("\n" + "=" * 60)
print("  VOICE EMOTION TRAINING COMPLETE!")
print(f"  Neural Net: {best_acc:.2f}% | MLP: {mlp_acc:.2f}%")
print("=" * 60)
