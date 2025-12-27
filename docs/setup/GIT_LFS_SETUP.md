# Git LFS (Recommended)

SentinelForge keeps **datasets** and most **training outputs** out of git (see `.gitignore`).
Some small, runtime-critical artifacts may be versioned via **Git LFS** (see `.gitattributes`).

If you want to use any included LFS-tracked artifacts, install Git LFS and pull the files.

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

## Download LFS Artifacts

```bash
git lfs pull
```

## Notes
- This repo already tracks common model formats in `.gitattributes`; you should not need to run `git lfs track` unless you add new patterns.
- Prefer distributing large, frequently-updated weights via **GitHub Releases** or external artifact storage when possible.
