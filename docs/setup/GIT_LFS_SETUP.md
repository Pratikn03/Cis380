# Git LFS (Optional)

OmniChatX is designed to keep large datasets and trained model artifacts **out of git** (see `.gitignore`).

If you plan to version large binary artifacts (e.g., `.pt`, `.pkl`, `.onnx`) in the repository, use **Git LFS**.

## Install Git LFS

macOS (Homebrew):
```bash
brew install git-lfs
git lfs install
```

Linux (apt example):
```bash
sudo apt-get update
sudo apt-get install git-lfs
git lfs install
```

## Track Model Artifacts

Example patterns:
```bash
git lfs track "*.pt"
git lfs track "*.pth"
git lfs track "*.pkl"
git lfs track "*.onnx"
git add .gitattributes
```

## Notes
- Prefer distributing large trained weights via **GitHub Releases** or external artifact storage when possible.
- If you enable LFS, set it up before committing large binaries so history stays clean.

