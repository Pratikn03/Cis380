import argparse, sys
from pathlib import Path

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
AUD_EXT = {".wav", ".mp3", ".flac", ".ogg"}
DOC_EXT = {".pdf", ".txt", ".md", ".docx"}
TAB_EXT = {".csv"}


def die(msg: str, code: int = 2):
    print(f"[DATA VALIDATION ERROR] {msg}", file=sys.stderr)
    sys.exit(code)


def count_files(p: Path, allowed_ext=None):
    if not p.exists():
        return 0
    if allowed_ext is None:
        return sum(1 for x in p.rglob("*") if x.is_file())
    return sum(1 for x in p.rglob("*") if x.is_file() and x.suffix.lower() in allowed_ext)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["tabular", "vision", "audio", "docs"])
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--root", default="data/raw")
    ap.add_argument("--path", default=None, help="Override dataset path (file or directory).")
    args = ap.parse_args()

    if args.path:
        root = Path(args.path)
    else:
        root = Path(args.root) / args.task / args.dataset
    if not root.exists():
        die(f"Missing dataset folder: {root}")

    if args.task == "tabular":
        if root.is_file():
            if root.suffix.lower() not in TAB_EXT:
                die(f"Expected a .csv file for tabular data: {root}")
            if root.stat().st_size == 0:
                die(f"CSV file is empty: {root}")
            print(f"[OK] tabular={args.dataset} csv_files=1")
            return
        n = count_files(root, TAB_EXT)
        if n == 0:
            die(f"No .csv found under {root}")
        print(f"[OK] tabular={args.dataset} csv_files={n}")
    elif args.task == "vision":
        n = count_files(root, IMG_EXT)
        if n == 0:
            die(f"No images found under {root}")
        print(f"[OK] vision={args.dataset} images={n}")
    elif args.task == "audio":
        n = count_files(root, AUD_EXT)
        if n == 0:
            die(f"No audio found under {root}")
        print(f"[OK] audio={args.dataset} audio_files={n}")
    else:
        n = count_files(root, DOC_EXT)
        if n == 0:
            die(f"No docs found under {root}")
        print(f"[OK] docs={args.dataset} docs={n}")


if __name__ == "__main__":
    main()
