import json
from pathlib import Path
from typing import List, Dict, Any, Union


def read_last_n_jsonl(path: Path, n: int) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    data = []
    try:
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines[-n:]:
                if line.strip():
                    data.append(json.loads(line))
    except Exception:
        pass
    return data


def append_jsonl(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data) + "\n")


def safe_write_json(path: Path, data: Union[Dict, List]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
