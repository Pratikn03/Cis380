"""CLI entrypoint for UAIS-V operations."""
import argparse

from ..data.build_30seq_dataset import build_30seq_arrays
from ..training.train_30seq import main as train_30seq_main


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="UAIS-V command line")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build-30seq", help="Build 30-sequence dataset (behavior or synthetic fallback)")
    sub.add_parser("train-30seq", help="Train the 30-sequence TensorFlow model")

    return parser


def main():  # pragma: no cover - CLI entrypoint
    parser = get_parser()
    args = parser.parse_args()

    if args.command == "build-30seq":
        build_30seq_arrays()
    elif args.command == "train-30seq":
        train_30seq_main()
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover
    main()
