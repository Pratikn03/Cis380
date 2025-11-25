"""Generate lightweight reports (JSON aggregation)."""
import json
from pathlib import Path
from typing import Dict

from uais.utils.logging_utils import setup_logging
from uais.utils.paths import EXPERIMENTS_DIR

logger = setup_logging(__name__)


DOMAINS = ["fraud", "cyber", "behavior", "fusion"]


def load_domain_metrics(domain: str) -> Dict:
    metrics_path = EXPERIMENTS_DIR / domain / "metrics"
    if not metrics_path.exists():
        return {}
    all_metrics = {}
    for file in metrics_path.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            all_metrics[file.stem] = json.load(f)
    return all_metrics


def main():
    report = {}
    for domain in DOMAINS:
        report[domain] = load_domain_metrics(domain)
    output_path = EXPERIMENTS_DIR / "report_summary.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("Wrote consolidated report to %s", output_path)


if __name__ == "__main__":
    main()
