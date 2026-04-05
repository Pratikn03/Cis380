#!/bin/bash
# Script to train the elite vision model (YOLO)

# Stop on error
set -e

echo "👁️  Starting Elite Vision Training..."

# 1. Setup Data
echo "   Generating/Verifying dataset and configuration..."
python setup_dummy_data.py

# 2. Train
echo "   🚀 Starting YOLOv8 training..."
python train_yolo.py

# 3. Show Metrics
echo "   📊 Training complete. Fetching metrics..."
python scripts/show_model_metrics.py

echo "🎉 Vision model training pipeline finished."