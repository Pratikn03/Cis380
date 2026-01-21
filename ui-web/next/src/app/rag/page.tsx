"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function RagPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch("/api/v1/rag/query", {
        method: "POST",
        body: JSON.stringify({ query, top_k: 6, return_chunks: false }),
      });
      setResult(data);
    } catch (err: any) {
      setError(String(err.message || err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel-grid">
      <div>
        <div className="card-title">DSA (RAG)</div>
        <h1 className="text-3xl mt-3">Document Intelligence</h1>
        <p className="muted mt-3">
          Ask grounded questions and inspect citations from your indexed knowledge base.
        </p>
      </div>
      <div className="card">
        <div className="panel-grid">
          <input
            className="input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about your docs…"
          />
          <button className="pill-btn" onClick={ask}>
            {loading ? "Querying…" : "Ask"}
          </button>
        </div>
      </div>
      {error && <div className="card">Error: {error}</div>}
      {result && (
        <div className="panel-grid">
          <div className="card">
            <div className="card-title">Answer</div>
            <pre className="mt-3 whitespace-pre-wrap text-sm">{result.answer}</pre>
          </div>
          <div className="card">
            <div className="card-title">Citations</div>
            <pre className="mt-3 whitespace-pre-wrap text-xs">
              {JSON.stringify(result.citations, null, 2)}
            </pre>
          </div>
          <div className="card">
            <div className="card-title">Retrieval</div>
            <pre className="mt-3 whitespace-pre-wrap text-xs">
              {JSON.stringify(result.retrieval, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
