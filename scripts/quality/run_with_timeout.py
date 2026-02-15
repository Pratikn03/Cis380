#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import subprocess
import sys
import time
from typing import Sequence


def _terminate_process_tree(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except Exception:
        try:
            process.terminate()
        except Exception:
            return

    time.sleep(2.0)
    if process.poll() is not None:
        return

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except Exception:
        try:
            process.kill()
        except Exception:
            return


def run_with_timeout(name: str, timeout_seconds: int, command: Sequence[str]) -> int:
    print(f"[run_with_timeout] starting {name}: {' '.join(command)}")
    started = time.monotonic()

    preexec_fn = os.setsid if hasattr(os, "setsid") else None
    process = subprocess.Popen(command, preexec_fn=preexec_fn)

    try:
        return_code = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        print(
            f"[run_with_timeout] timeout after {elapsed:.1f}s "
            f"(limit={timeout_seconds}s) for {name}",
            file=sys.stderr,
        )
        _terminate_process_tree(process)
        return 124

    elapsed = time.monotonic() - started
    print(
        f"[run_with_timeout] finished {name} in {elapsed:.1f}s with exit code {return_code}",
    )
    return return_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a command with a hard timeout and fail fast if it hangs.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        required=True,
        help="Timeout in seconds.",
    )
    parser.add_argument(
        "--name",
        default="command",
        help="Logical name shown in logs.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to execute. Use '--' before the command.",
    )
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("No command provided. Example: --timeout 180 -- npm run test:ci")
    if args.timeout <= 0:
        parser.error("--timeout must be > 0")
    return args


def main() -> int:
    args = parse_args()
    return run_with_timeout(args.name, args.timeout, args.command)


if __name__ == "__main__":
    raise SystemExit(main())
