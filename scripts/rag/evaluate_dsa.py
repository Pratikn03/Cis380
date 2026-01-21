from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.rag.config import settings
from app.rag.metrics import RetrievalMetrics
from app.rag.retriever import retrieve_context


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def main() -> None:
    eval_dir = Path("eval")
    queries_path = eval_dir / "queries.jsonl"
    qrels_path = eval_dir / "qrels.jsonl"
    queries = _read_jsonl(queries_path)
    qrels = _read_jsonl(qrels_path)
    if not queries or not qrels:
        print("[dsa-eval] Missing eval data. Expected eval/queries.jsonl and eval/qrels.jsonl")
        return

    qrel_map = {}
    for row in qrels:
        qid = row.get("query_id")
        rel = row.get("relevant_ids") or row.get("relevant_doc_ids") or []
        if qid:
            qrel_map[qid] = rel

    metrics = RetrievalMetrics(k_values=[1, 3, 5, 10])
    for row in queries:
        qid = row.get("query_id")
        text = row.get("query") or row.get("text")
        if not qid or not text:
            continue
        results = retrieve_context(text, top_k=10)
        retrieved_ids = [r.get("doc_id") or r.get("chunk_id") for r in results]
        metrics.add_result(
            query_id=qid,
            query_text=text,
            retrieved_ids=[str(x) for x in retrieved_ids if x is not None],
            relevant_ids=[str(x) for x in qrel_map.get(qid, [])],
        )

    report = metrics.evaluate()
    metrics_dir = Path("metrics")
    reports_dir = Path("reports")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    (metrics_dir / "rag_eval.json").write_text(
        json.dumps(report.to_dict(), indent=2), encoding="utf-8"
    )
    (reports_dir / "rag_eval.md").write_text(report.summary(), encoding="utf-8")
    print(report.summary())


if __name__ == "__main__":
    main()
