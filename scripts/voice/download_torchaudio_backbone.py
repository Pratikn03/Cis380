from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torchaudio


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Download torchaudio SSL backbone locally.")
    ap.add_argument("--bundle", type=str, default="WAVLM_BASE_PLUS")
    ap.add_argument("--out-dir", type=Path, default=Path("models/torchaudio_backbones"))
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    if not hasattr(torchaudio.pipelines, args.bundle):
        raise SystemExit(f"Unknown torchaudio bundle: {args.bundle}")

    bundle = getattr(torchaudio.pipelines, args.bundle)
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = getattr(bundle, "_path", None)
    if not filename:
        raise SystemExit("Bundle missing checkpoint path.")
    target = out_dir / filename

    if target.exists():
        print(f"[download] already exists: {target}")
        return

    # Use bundle download to the requested directory.
    state_dict = bundle._get_state_dict(  # noqa: SLF001
        {
            "model_dir": str(out_dir),
            "file_name": filename,
            "check_hash": True,
            "progress": True,
        }
    )
    torch.save(state_dict, target)
    print(f"[download] saved: {target}")


if __name__ == "__main__":
    main()
