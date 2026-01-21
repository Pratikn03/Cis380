from __future__ import annotations

import argparse
import json

from app.rag.dsa_pipeline import answer_query, ingest_documents


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentifargo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    rag = sub.add_parser("rag", help="Document Search Assistant commands")
    rag_sub = rag.add_subparsers(dest="rag_command", required=True)

    idx = rag_sub.add_parser("index", help="Build or rebuild the DSA index")
    idx.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch")

    query = rag_sub.add_parser("query", help="Query the DSA index")
    query.add_argument("text", help="Query text")
    query.add_argument("--top-k", type=int, default=6, help="Top-K chunks to use")

    args = parser.parse_args()

    if args.command == "rag" and args.rag_command == "index":
        stats = ingest_documents(rebuild=args.rebuild)
        print(json.dumps(stats, indent=2))
        return

    if args.command == "rag" and args.rag_command == "query":
        result = answer_query(args.text, top_k=args.top_k)
        print(json.dumps(result, indent=2))
        return


if __name__ == "__main__":
    main()
