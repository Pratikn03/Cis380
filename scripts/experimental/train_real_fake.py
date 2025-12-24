#!/usr/bin/env python3
"""
Train Real/Fake Image Classifier
Dataset: ~90,000 images (45k real + 45k fake)
Model: ResNet18 with transfer learning
"""

import sys
import time
from pathlib import Path
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms, models
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RealFakeDataset(Dataset):
    """Dataset for Real/Fake image classification."""
    
    def __init__(self, data, transform):
        self.data = data
        self.transform = transform
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        path, label = self.data[idx]
        try:
            img = Image.open(path).convert('RGB')
            img = self.transform(img)
            return img, label
        except Exception:
            return torch.zeros(3, 224, 224), label


def print_header(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60 + "\n")


def train_real_fake_classifier(max_images_per_class=40000, epochs=3, batch_size=32):
    """Train Real vs Fake Image Classifier."""
    print_header("REAL vs FAKE IMAGE CLASSIFIER")
    
    # Data directories
    real_dir = PROJECT_ROOT / "data/raw/vision/train_real/train"
    fake_dir = PROJECT_ROOT / "data/raw/vision/train_fake/train"
    
    if not real_dir.exists() or not fake_dir.exists():
        print("❌ Data directories not found!")
        print(f"   Expected: {real_dir}")
        print(f"   Expected: {fake_dir}")
        return None
    
    # Collect images
    print("📦 Loading image paths...")
    real_images = sorted(real_dir.glob("*.*"))[:max_images_per_class]
    fake_images = sorted(fake_dir.glob("*.*"))[:max_images_per_class]
    
    print(f"   Real images: {len(real_images)}")
    print(f"   Fake images: {len(fake_images)}")
    print(f"   Total: {len(real_images) + len(fake_images)}")
    
    # Create dataset
    all_images = [(str(p), 0) for p in real_images] + [(str(p), 1) for p in fake_images]
    train_data, val_data = train_test_split(
        all_images, 
        test_size=0.2, 
        random_state=42, 
        stratify=[x[1] for x in all_images]
    )
    
    print(f"\n   Train samples: {len(train_data)}")
    print(f"   Val samples: {len(val_data)}")
    
    # Transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    train_dataset = RealFakeDataset(train_data, transform)
    val_dataset = RealFakeDataset(val_data, transform)
    
    # Use num_workers=0 to avoid multiprocessing pickle issues
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)
    
    # Model setup
    print("\n📦 Loading ResNet18 model...")
    
    # Device selection
    if torch.backends.mps.is_available():
        device = torch.device("mps")
        print("   Using: Apple Silicon (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print("   Using: NVIDIA GPU (CUDA)")
    else:
        device = torch.device("cpu")
        print("   Using: CPU")
    
    model = models.resnet18(weights='IMAGENET1K_V1')
    model.fc = nn.Linear(model.fc.in_features, 2)  # 2 classes: real/fake
    model = model.to(device)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.7)
    
    print(f"\n🚀 Starting training ({epochs} epochs)...")
    print(f"   Batches per epoch: {len(train_loader)}")
    start_time = time.time()
    
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_correct = 0
        train_total = 0
        train_loss = 0.0
        
        for batch_idx, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
            
            if batch_idx % 200 == 0:
                acc = 100. * train_correct / train_total
                print(f"   Epoch {epoch+1}/{epochs} | Batch {batch_idx}/{len(train_loader)} | Acc: {acc:.1f}%")
        
        # Validation phase
        model.eval()
        val_correct = 0
        val_total = 0
        val_loss = 0.0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        train_acc = 100. * train_correct / train_total
        val_acc = 100. * val_correct / val_total
        
        print(f"\n   📊 Epoch {epoch+1}/{epochs} Results:")
        print(f"      Train Acc: {train_acc:.2f}% | Loss: {train_loss/len(train_loader):.4f}")
        print(f"      Val Acc: {val_acc:.2f}% | Loss: {val_loss/len(val_loader):.4f}")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            model_dir = PROJECT_ROOT / "models/vision"
            model_dir.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), model_dir / "real_fake_classifier.pt")
            print(f"      ✅ New best model saved! (Val Acc: {val_acc:.2f}%)")
        
        scheduler.step()
    
    elapsed = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"  ✅ TRAINING COMPLETE")
    print(f"=" * 60)
    print(f"\n   Total time: {elapsed/60:.1f} minutes")
    print(f"   Best validation accuracy: {best_val_acc:.2f}%")
    print(f"   Model saved: models/vision/real_fake_classifier.pt")
    
    # Save class names
    classes_file = PROJECT_ROOT / "models/vision/real_fake_classes.txt"
    with open(classes_file, 'w') as f:
        f.write("real\nfake\n")
    print(f"   Classes saved: models/vision/real_fake_classes.txt")
    
    return best_val_acc


if __name__ == "__main__":
    # Parse command line args for customization
    import argparse
    parser = argparse.ArgumentParser(description="Train Real/Fake Image Classifier")
    parser.add_argument("--max-images", type=int, default=40000, help="Max images per class")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    args = parser.parse_args()
    
    train_real_fake_classifier(
        max_images_per_class=args.max_images,
        epochs=args.epochs,
        batch_size=args.batch_size
    )
