#!/bin/bash
# Script to train the elite recommender model and push changes to GitHub

# Stop on error
set -e

# 0. Environment Setup & Sanity Check
export GRPC_ENABLE_FORK_SUPPORT=0
export GRPC_POLL_STRATEGY=poll
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export WANDB_DISABLED=true
export HF_HUB_DISABLE_TELEMETRY=1

echo "🏥 Running Sanity Check..."
python scripts/sanity_check.py

# 1. Train the model
echo "🧠 Starting Elite Recommender Training..."
echo "   Scanning data/raw/ for all available datasets..."
python train_recommender.py
echo "   ℹ️  Logs saved to recommender_training.log"

# 2. Git operations
echo "📦 Staging changes..."
git add .

echo "💾 Committing changes..."
git commit -m "feat: Train elite multi-domain recommender model" || echo "⚠️ No changes to commit"

echo "🚀 Pushing to GitHub..."
git push