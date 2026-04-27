from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.rag.config import settings
from app.rag.loaders import load_document, scan_documents
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

    source_map: dict[str, list[str]] = {}
    for path in scan_documents(settings.docs_dir):
        doc = load_document(path)
        if not doc:
            continue
        ids = [doc.doc_id]
        for page in doc.pages:
            # Index chunk IDs are deterministic per document/page/chunk order.
            ids.append(f"{doc.doc_id}:{page.page_num}:0")
        source_map[str(path)] = ids
        source_map[path.name] = ids

    qrel_map = {}
    for row in qrels:
        qid = row.get("query_id")
        rel = row.get("relevant_ids") or row.get("relevant_doc_ids") or []
        rel_sources = row.get("relevant_sources") or []
        if rel_sources:
            for src in rel_sources:
                doc_ids = source_map.get(str(src)) or source_map.get(Path(str(src)).name)
                if doc_ids:
                    rel.extend(doc_ids)
        if qid:
            qrel_map[qid] = sorted({str(item) for item in rel})

    metrics = RetrievalMetrics(k_values=[1, 3, 5, 10])
    for row in queries:
        qid = row.get("query_id")
        text = row.get("query") or row.get("text")
        if not qid or not text:
            continue
        results = retrieve_context(text, top_k=10)
        retrieved_ids = []
        for result in results:
            doc_id = result.get("doc_id")
            chunk_id = result.get("chunk_id")
            if doc_id is not None:
                retrieved_ids.append(str(doc_id))
            if chunk_id is not None:
                retrieved_ids.append(str(chunk_id))
        metrics.add_result(
            query_id=qid,
            query_text=text,
            retrieved_ids=retrieved_ids,
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
