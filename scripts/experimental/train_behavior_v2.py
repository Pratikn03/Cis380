#!/usr/bin/env python3
"""Experimental: enhanced behavior model training script (target 98% accuracy).

This is not part of the canonical training pipeline. See `scripts/train_all.py`.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path
import joblib
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
import warnings

warnings.filterwarnings("ignore")

print("=" * 60)
print("  TRAINING BEHAVIOR MODEL")
print("  Target: 98% accuracy (current: 86.86%)")
print("=" * 60)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BEHAVIOR_DIR = PROJECT_ROOT / "data/raw/behavior"
MODEL_DIR = PROJECT_ROOT / "models/behavior"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Try different data sources
data_sources = [
    BEHAVIOR_DIR / "online_shoppers_intention.csv",
    BEHAVIOR_DIR / "r4.2" / "logon.csv",
    PROJECT_ROOT / "data/processed/behavior_cert.csv",
]

print("\n📂 Looking for behavior data...")

df = None
for source in data_sources:
    if source.exists():
        print(f"  Found: {source.name}")
        try:
            df = pd.read_csv(source, nrows=50000)  # Limit rows
            print(f"  Loaded: {len(df)} rows, {len(df.columns)} columns")
            break
        except Exception as e:
            print(f"  Error loading {source.name}: {e}")
            continue

if df is None:
    print("❌ No behavior data found!")
    exit(1)

# Determine target column
print(f"\n📊 Columns: {list(df.columns)}")

# Try common target columns
target_cols = ["Revenue", "label", "Label", "target", "anomaly", "class", "insider"]
target_col = None
for col in target_cols:
    if col in df.columns:
        target_col = col
        break

if target_col is None:
    # Use last column or create synthetic target
    if df.columns[-1] in df.select_dtypes(include=["object", "bool"]).columns:
        target_col = df.columns[-1]
    else:
        print("⚠️ No target column found, creating synthetic anomaly labels")
        # Create anomaly detection based on statistical outliers
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 0:
            # Z-score based anomaly
            z_scores = np.abs((numeric_df - numeric_df.mean()) / numeric_df.std())
            df["anomaly"] = (z_scores > 3).any(axis=1).astype(int)
            target_col = "anomaly"

print(f"   Target column: {target_col}")

# Prepare features
X = df.drop(columns=[target_col], errors="ignore")
y = df[target_col]

# Handle categorical columns
categorical_cols = X.select_dtypes(include=["object", "category"]).columns
for col in categorical_cols:
    if X[col].nunique() < 50:  # Only encode if reasonable cardinality
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
    else:
        X = X.drop(columns=[col])

# Handle missing values
X = X.fillna(0)

# Convert target to numeric
if y.dtype == "object" or y.dtype == "bool":
    le_target = LabelEncoder()
    y = le_target.fit_transform(y.astype(str))
else:
    y = y.values

print(f"\n📊 Dataset shape: {X.shape}")
print(f"   Class distribution: {pd.Series(y).value_counts().to_dict()}")

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_val, y_train, y_val = train_test_split(
    X_scaled, y, test_size=0.2, stratify=y, random_state=42
)
print(f"   Train: {len(X_train)}, Val: {len(X_val)}")

# PyTorch training
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"   Device: {device}")

train_dataset = TensorDataset(
    torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long)
)
val_dataset = TensorDataset(
    torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long)
)

train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=256)


# Neural Network Model
class BehaviorNet(nn.Module):
    def __init__(self, input_size, num_classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_classes),
        )

    def forward(self, x):
        return self.net(x)


input_size = X_scaled.shape[1]
num_classes = len(np.unique(y))

model = BehaviorNet(input_size, num_classes).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)

print("\n🚀 Training Behavior Neural Network...")

best_acc = 0
epochs = 50

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
    scheduler.step(1 - val_acc / 100)

    if val_acc > best_acc:
        best_acc = val_acc
        torch.save(
            {
                "model_state": model.state_dict(),
                "scaler": scaler,
                "input_size": input_size,
                "num_classes": num_classes,
                "feature_names": list(X.columns),
            },
            MODEL_DIR / "behavior_nn.pt",
        )

    if (epoch + 1) % 10 == 0 or epoch == 0:
        print(
            f"  Epoch {epoch+1}/{epochs} - Loss: {train_loss/len(train_loader):.4f}, Val Acc: {val_acc:.2f}%"
        )

    # Early stopping if we hit target
    if best_acc >= 98.0:
        print(f"  🎯 Target accuracy reached at epoch {epoch+1}!")
        break

print(f"\n✅ Best Behavior NN Accuracy: {best_acc:.2f}%")

# Also train ensemble models
print("\n📦 Training ensemble models...")

# Gradient Boosting
print("  Training GradientBoosting...")
gb = GradientBoostingClassifier(n_estimators=200, max_depth=8, random_state=42)
gb.fit(X_train, y_train)
gb_acc = gb.score(X_val, y_val) * 100
print(f"  GradientBoosting Accuracy: {gb_acc:.2f}%")

# Random Forest
print("  Training RandomForest...")
rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_acc = rf.score(X_val, y_val) * 100
print(f"  RandomForest Accuracy: {rf_acc:.2f}%")

# Save best model
best_model_acc = max(best_acc, gb_acc, rf_acc)
if gb_acc == best_model_acc:
    joblib.dump(
        {"model": gb, "scaler": scaler, "feature_names": list(X.columns)},
        MODEL_DIR / "behavior_best.pkl",
    )
    print("✅ Saved GradientBoosting as best model")
elif rf_acc == best_model_acc:
    joblib.dump(
        {"model": rf, "scaler": scaler, "feature_names": list(X.columns)},
        MODEL_DIR / "behavior_best.pkl",
    )
    print("✅ Saved RandomForest as best model")
else:
    print("✅ Neural Network is best model")

# Also save for backward compatibility
joblib.dump({"model": gb, "scaler": scaler}, MODEL_DIR / "behavior_gb.pkl")
joblib.dump({"model": rf, "scaler": scaler}, MODEL_DIR / "behavior_rf.pkl")

print("\n" + "=" * 60)
print("  BEHAVIOR MODEL TRAINING COMPLETE!")
print(f"  Neural Net: {best_acc:.2f}%")
print(f"  GradientBoosting: {gb_acc:.2f}%")
print(f"  RandomForest: {rf_acc:.2f}%")
print(f"  BEST: {max(best_acc, gb_acc, rf_acc):.2f}%")
print("=" * 60)
