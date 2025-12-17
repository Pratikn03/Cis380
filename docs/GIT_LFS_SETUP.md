# Git LFS Setup Guide for OmniChatX

## Overview

This project contains ~300MB of machine learning model files that should be tracked with Git LFS (Large File Storage) for optimal repository performance.

## Current Model Files

Total size: ~335 MB across 20+ files

**Largest files:**
- `models/voice_emotion.pkl` - 102 MB
- `models/cyber/supervised/cyber_model.pkl` - 58 MB
- `models/vision/resnet/model.pt` - 43 MB
- `models/vision/resnet_smoke/model.pt` - 43 MB
- `models/behavior/behavior_supervised.pkl` - 28 MB
- `yolov8s.pt` - 22 MB

## Installation

### Option 1: Homebrew (macOS - requires Homebrew)

```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Git LFS
brew install git-lfs

# Initialize Git LFS
git lfs install
```

### Option 2: Conda (if you have Anaconda/Miniconda)

```bash
# Create a separate environment to avoid conflicts
conda create -n gitlfs git-lfs -c conda-forge -y
conda activate gitlfs
git lfs install

# Or install in base (may have conflicts)
# conda install -c conda-forge git-lfs -y
```

### Option 3: Manual Download (macOS)

```bash
# Download from GitHub
curl -LO https://github.com/git-lfs/git-lfs/releases/download/v3.7.1/git-lfs-darwin-arm64-v3.7.1.tar.gz

# Extract
tar -xzf git-lfs-darwin-arm64-v3.7.1.tar.gz

# Install
sudo bash install.sh

# Initialize
git lfs install
```

## Setup Steps

### 1. Install Git LFS (see above)

### 2. Initialize in Repository

```bash
cd /path/to/universal-anomaly-intelligence-v2
git lfs install
```

### 3. Verify .gitattributes

The `.gitattributes` file is already configured with patterns for:
- PyTorch models (*.pt, *.pth)
- Pickle files (*.pkl, *.pickle)
- Keras/TensorFlow (*.h5, *.hdf5)
- ONNX models (*.onnx)
- Other model formats

### 4. Migrate Existing Files

```bash
# Track all existing model files
git lfs migrate import --include="*.pt,*.pkl,*.h5,*.onnx,*.pth,*.weights" --everything

# Or for a safer approach (only current branch)
git lfs migrate import --include="*.pt,*.pkl,*.h5,*.onnx,*.pth,*.weights"
```

### 5. Verify Setup

```bash
# Check which files are tracked
git lfs ls-files

# Check LFS status
git lfs status

# Verify a specific file
git lfs ls-files | grep voice_emotion.pkl
```

## Usage

After setup, Git LFS works automatically:

```bash
# Normal git operations work as usual
git add models/
git commit -m "Add new model"
git push
```

### Checking LFS Storage

```bash
# See how much storage you're using
git lfs ls-files -s

# Get detailed info about LFS objects
git lfs fsck
```

## Benefits

1. **Faster Clones**: Download model pointers initially, fetch actual files on demand
2. **Reduced Repository Size**: Keep git operations fast
3. **Bandwidth Savings**: Only download models you need
4. **History Management**: Better handling of large binary file changes

## Current Status

- ✅ `.gitattributes` file created with LFS patterns
- ⏳ Git LFS installation required
- ⏳ Existing files need migration
- ⏳ Need to push LFS objects to remote

## Next Steps

1. Install Git LFS using one of the methods above
2. Run `git lfs install` in the repository
3. Migrate existing model files with `git lfs migrate import`
4. Commit and push changes
5. Verify with `git lfs ls-files`

## Troubleshooting

### "git: 'lfs' is not a git command"

Git LFS is not installed. Follow installation steps above.

### "This exceeds GitHub's file size limit of 100 MB"

This error occurs if LFS isn't set up before committing large files.

```bash
# Remove file from Git history
git rm --cached path/to/large/file.pkl

# Set up LFS
git lfs track "*.pkl"

# Re-add the file
git add path/to/large/file.pkl
git add .gitattributes
git commit -m "Track model files with LFS"
```

### Conda Installation Conflicts

If conda installation fails due to dependency conflicts:
1. Use manual download method
2. Or create separate conda environment specifically for git-lfs

## References

- [Git LFS Official Site](https://git-lfs.github.com/)
- [Git LFS Tutorial](https://github.com/git-lfs/git-lfs/wiki/Tutorial)
- [GitHub LFS Documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files)
