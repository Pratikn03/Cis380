import json
import random
import time
from datetime import datetime
from typing import Mapping

import requests

API_URL = "http://localhost:8000/api/risk/analyze"
OUTPUT = "reports/risk_simulation_log.jsonl"

SCENARIOS = [
    {"name": "normal", "transaction_amount": 100.0, "clicks": 20, "files": 2, "device_known": True},
    {"name": "step_up", "transaction_amount": 800.0, "clicks": 150, "files": 35, "device_known": False},
    {"name": "block", "transaction_amount": 5000.0, "clicks": 400, "files": 120, "device_known": False},
]

COUNTRIES = ["US", "BR", "IN", "CN", "DE", "NG"]


def build_payload(scenario: Mapping[str, object]) -> Mapping[str, object]:
    return {
        "login_country": random.choice(COUNTRIES),
        "device_known": scenario["device_known"],
        "login_time": datetime.utcnow().strftime("%H:%M"),
        "clicks_per_minute": scenario["clicks"],
        "files_accessed": scenario["files"],
        "transaction_amount": scenario["transaction_amount"],
    }


def simulate(count: int = 10, pause: float = 0.5) -> None:
    with open(OUTPUT, "a", encoding="utf-8") as out:
        for i in range(count):
            scenario = random.choice(SCENARIOS)
            payload = build_payload(scenario)
            resp = requests.post(API_URL, json=payload, timeout=10)
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "scenario": scenario["name"],
                "payload": payload,
                "response": resp.json(),
            }
            out.write(json.dumps(entry) + "\n")
            print(f"[Simulate] #{i+1} {scenario['name']} -> decision {entry['response'].get('decision')}")
            time.sleep(pause)


if __name__ == "__main__":
    simulate()
