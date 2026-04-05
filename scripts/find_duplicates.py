import csv
import hashlib
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

INCLUDE_EXT = {
    ".csv",
    ".parquet",
    ".json",
    ".jsonl",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".wav",
    ".mp3",
    ".flac",
    ".m4a",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".zip",
    ".tar",
    ".gz",
    ".tgz",
    ".7z",
}


def sha256_file(path: Path, chunk=1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def should_include(p: Path) -> bool:
    if p.is_symlink():
        return False
    if not p.is_file():
        return False
    ext = p.suffix.lower()
    return ext in INCLUDE_EXT


def main():
    roots = sys.argv[1:] or ["data"]
    paths = []
    for r in roots:
        rp = Path(r)
        if not rp.exists():
            continue
        for p in rp.rglob("*"):
            if should_include(p):
                paths.append(p)
    if not paths:
        print("No files found to scan under:", roots)
        return
    by_size = defaultdict(list)
    for p in paths:
        try:
            by_size[p.stat().st_size].append(p)
        except Exception:
            pass
    dup_groups = []
    total_files = 0
    hashed_files = 0
    for size, plist in by_size.items():
        if len(plist) < 2:
            continue
        by_hash = defaultdict(list)
        for p in plist:
            total_files += 1
            try:
                h = sha256_file(p)
                hashed_files += 1
                by_hash[h].append(p)
            except Exception:
                continue
        for h, hs in by_hash.items():
            if len(hs) > 1:
                dup_groups.append((size, h, hs))
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_json = Path(f"reports/duplicates_{ts}.json")
    out_csv = Path(f"reports/duplicates_{ts}.csv")
    out_mv = Path(f"reports/duplicates_move_{ts}.sh")
    data = []
    for size, h, hs in dup_groups:
        keep = str(hs[0])
        dups = [str(x) for x in hs[1:]]
        data.append(
            {"size_bytes": size, "sha256": h, "keep": keep, "duplicates": dups, "count": len(hs)}
        )
    out_json.write_text(
        json.dumps(
            {"scanned_roots": roots, "included_ext": sorted(INCLUDE_EXT), "duplicate_groups": data},
            indent=2,
        ),
        encoding="utf-8",
    )
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group_size_bytes", "sha256", "keep_path", "duplicate_path"])
        for g in data:
            for d in g["duplicates"]:
                w.writerow([g["size_bytes"], g["sha256"], g["keep"], d])
    out_mv.write_text("#!/usr/bin/env bash\nset -euo pipefail\n", encoding="utf-8")
    out_mv.write_text(
        out_mv.read_text(encoding="utf-8") + "TS=$(date +%Y%m%d_%H%M%S)\n", encoding="utf-8"
    )
    out_mv.write_text(
        out_mv.read_text(encoding="utf-8")
        + 'TRASH="data/_duplicates_trash/$TS"\nmkdir -p "$TRASH"\n\n',
        encoding="utf-8",
    )
    for g in data:
        for d in g["duplicates"]:
            dp = Path(d)
            try:
                rel = dp.relative_to("data")
                dest_dir = f"$TRASH/{rel.parent.as_posix()}"
                cmd = f'mkdir -p "{dest_dir}"\n' f'mv -n "{dp.as_posix()}" "{dest_dir}/"\n'
            except Exception:
                cmd = f'mv -n "{dp.as_posix()}" "$TRASH/"\n'
            out_mv.write_text(out_mv.read_text(encoding="utf-8") + cmd, encoding="utf-8")
    os.chmod(out_mv, 0o755)
    dup_file_count = sum(len(g["duplicates"]) for g in data)
    dup_group_count = len(data)
    print(f"✅ Duplicate groups found: {dup_group_count}")
    print(f"✅ Duplicate files (movable): {dup_file_count}")
    print(f"📄 JSON report: {out_json}")
    print(f"📄 CSV report : {out_csv}")
    print(f"🧹 Move script: {out_mv}")
    print("")
    print("Next:")
    print(f"  - Dry-run review: open {out_csv}")
    print(f"  - To MOVE duplicates into trash: bash {out_mv}")


if __name__ == "__main__":
    main()
