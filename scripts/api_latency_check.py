#!/usr/bin/env python
"""Simple API latency checker for UAIS-V FastAPI endpoints."""
import json
import time
import argparse
import requests


def time_endpoint(url: str, payload: dict, n_runs: int = 5):
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        resp = requests.post(url, json=payload)
        elapsed = time.perf_counter() - t0
        times.append(elapsed)
        if resp.status_code != 200:
            print(f"Error {resp.status_code}: {resp.text}")
            break
    return times


def main():
    parser = argparse.ArgumentParser(description="Check latency of UAIS-V API endpoints")
    parser.add_argument("--host", default="http://localhost:8000", help="Base URL of API")
    parser.add_argument("--runs", type=int, default=5, help="Number of runs per endpoint")
    args = parser.parse_args()

    base = args.host.rstrip("/")
    endpoints = {
        "predict_fraud": {"url": f"{base}/predict_fraud", "payload": {"features": [0.1] * 30}},
        "predict_cyber": {"url": f"{base}/predict_cyber", "payload": {"features": [0.1] * 30}},
        "predict_fusion": {"url": f"{base}/predict_fusion", "payload": {"scores": {"fraud": 0.1, "cyber": 0.2, "behavior": 0.3}}},
    }
    for name, info in endpoints.items():
        print(f"\n{name} -> {info['url']}")
        times = time_endpoint(info["url"], info["payload"], n_runs=args.runs)
        if times:
            print(f"mean {sum(times)/len(times):.4f}s, min {min(times):.4f}s, max {max(times):.4f}s")


if __name__ == "__main__":
    main()
