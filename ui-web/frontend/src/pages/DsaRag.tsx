import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import "../styles/dsa_docs.css";

interface DsaSource {
  topic?: string;
  source?: string;
  doc_id?: string;
  chunk_id?: number;
  retrievers?: string[];
  score_dense?: number;
  score_bm25?: number;
  score_final?: number;
  snippet?: string;
}

interface DsaResponse {
  answer: string;
  sources?: DsaSource[];
  citations?: string[];
  chatgpt_link?: string;
  chatgpt_prompt?: string;
  rewritten_queries?: string[];
  retrieval_counts?: {
    dense: number;
    bm25: number;
    merged: number;
  };
}

const suggestions = [
  "Explain sliding window and when to use it",
  "How does binary search work?",
  "Compare merge sort vs quick sort",
  "What is a monotonic stack?",
];

const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (detail) {
      return typeof detail === "string" ? detail : JSON.stringify(detail);
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Request failed. Please try again.";
};

export default function DsaRag() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<DsaResponse | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem("backendUrl") || "http://localhost:8000"
  );
  const [isConnected, setIsConnected] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [noteName, setNoteName] = useState("dsa_note.md");
  const [noteBody, setNoteBody] = useState("");
  const [noteStatus, setNoteStatus] = useState<string | null>(null);

  const apiBase = useMemo(() => backendUrl.replace(/\/$/, ""), [backendUrl]);

  const testConnection = async () => {
    try {
      const res = await fetch(`${apiBase}/health`);
      setIsConnected(res.ok);
    } catch {
      setIsConnected(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, [apiBase]);

  const handleAsk = async () => {
    if (!query.trim()) return;
    setStatus("Thinking...");
    setError(null);
    try {
      const res = await fetch(`${apiBase}/api/dsa-rag/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || `Request failed (${res.status})`);
      }
      const payload = (await res.json()) as DsaResponse;
      setResponse(payload);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setStatus(null);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;
    setUploadStatus("Uploading...");
    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      const res = await fetch(`${apiBase}/api/dsa-rag/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || `Upload failed (${res.status})`);
      }
      const payload = await res.json();
      setUploadStatus(`Uploaded. Indexed ${payload.chunks || 0} chunks.`);
    } catch (err) {
      setUploadStatus(getErrorMessage(err));
    }
  };

  const handleIngestNote = async () => {
    if (!noteBody.trim()) {
      setNoteStatus("Add some text before ingesting.");
      return;
    }
    setNoteStatus("Indexing...");
    try {
      const res = await fetch(`${apiBase}/api/dsa-rag/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: noteName, content: noteBody }),
      });
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}));
        throw new Error(payload.detail || `Ingest failed (${res.status})`);
      }
      const payload = await res.json();
      setNoteStatus(`Indexed ${payload.chunks || 0} chunks.`);
    } catch (err) {
      setNoteStatus(getErrorMessage(err));
    }
  };

  const handleCopyPrompt = async () => {
    const prompt = response?.chatgpt_prompt;
    if (!prompt) return;
    try {
      await navigator.clipboard.writeText(prompt);
      setStatus("Prompt copied to clipboard.");
      setTimeout(() => setStatus(null), 2000);
    } catch {
      setStatus("Copy failed. Please copy manually.");
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-emerald-400">DSA RAG</p>
          <h1 className="text-3xl md:text-4xl font-bold text-white">DSA Study Assistant</h1>
          <p className="text-slate-300">
            Offline-first RAG pipeline with rewrite, multi-retrieve, rerank, and citations.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-5 space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-end">
            <div className="flex-1">
              <label className="text-sm text-slate-400">Backend URL</label>
              <input
                value={backendUrl}
                onChange={(event) => {
                  const value = event.target.value;
                  setBackendUrl(value);
                  localStorage.setItem("backendUrl", value);
                }}
                className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
                placeholder="http://localhost:8000"
              />
            </div>
            <button
              onClick={testConnection}
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-600"
            >
              Test
            </button>
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <span
                className={`h-2 w-2 rounded-full ${isConnected ? "bg-emerald-400" : "bg-rose-400"}`}
              />
              {isConnected ? "Connected" : "Disconnected"}
            </div>
          </div>

          <div className="space-y-3">
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-200"
              rows={4}
              placeholder="Ask a DSA question..."
            />
            <div className="flex flex-wrap gap-2">
              {suggestions.map((item) => (
                <button
                  key={item}
                  type="button"
                  onClick={() => setQuery(item)}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-1 text-xs text-slate-300 hover:border-emerald-500/60"
                >
                  {item}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                onClick={handleAsk}
                className="rounded-xl bg-emerald-500 px-5 py-2 text-sm font-semibold text-slate-900 hover:bg-emerald-400"
              >
                Ask
              </button>
              {response?.chatgpt_link && (
                <a
                  href={response.chatgpt_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-xl border border-emerald-500/60 px-5 py-2 text-sm text-emerald-200 hover:bg-emerald-500/10"
                >
                  Open ChatGPT
                </a>
              )}
              <button
                onClick={handleCopyPrompt}
                className="rounded-xl border border-slate-600 px-5 py-2 text-sm text-slate-200 hover:border-emerald-500/60"
              >
                Copy prompt
              </button>
            </div>
            {status && <p className="text-xs text-slate-400">{status}</p>}
            {error && <p className="text-xs text-rose-300">{error}</p>}
          </div>
        </section>

        <section className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-700 bg-slate-800/60 p-5 space-y-3">
            <h2 className="text-lg font-semibold text-white">Upload DSA docs</h2>
            <input
              type="file"
              accept=".md,.txt"
              onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
              className="text-sm text-slate-300"
            />
            <button
              onClick={handleUpload}
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-600"
            >
              Upload and re-index
            </button>
            {uploadStatus && <p className="text-xs text-slate-400">{uploadStatus}</p>}
          </div>

          <div className="rounded-2xl border border-slate-700 bg-slate-800/60 p-5 space-y-3">
            <h2 className="text-lg font-semibold text-white">Add a quick note</h2>
            <input
              value={noteName}
              onChange={(event) => setNoteName(event.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
              placeholder="filename.md"
            />
            <textarea
              value={noteBody}
              onChange={(event) => setNoteBody(event.target.value)}
              rows={3}
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-200"
              placeholder="Paste a short DSA note..."
            />
            <button
              onClick={handleIngestNote}
              className="rounded-lg bg-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-600"
            >
              Save and re-index
            </button>
            {noteStatus && <p className="text-xs text-slate-400">{noteStatus}</p>}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-5 space-y-4">
          <h2 className="text-lg font-semibold text-white">Answer</h2>
          <div className="dsa-docs dsa-docs--embedded">
            {response?.answer ? (
              <pre className="whitespace-pre-wrap text-sm text-slate-200">
                {response.answer}
              </pre>
            ) : (
              <p className="text-sm text-slate-400">Ask a question to see the answer.</p>
            )}
          </div>
          {response?.rewritten_queries && response.rewritten_queries.length > 0 && (
            <div className="text-xs text-slate-400">
              <span className="font-semibold text-slate-300">Rewritten queries:</span>{" "}
              {response.rewritten_queries.join(" | ")}
            </div>
          )}
          {response?.retrieval_counts && (
            <div className="text-xs text-slate-400">
              Retrieved: dense {response.retrieval_counts.dense}, bm25 {response.retrieval_counts.bm25},
              merged {response.retrieval_counts.merged}
            </div>
          )}
        </section>

        <section className="rounded-2xl border border-slate-700 bg-slate-800/60 p-5 space-y-4">
          <h2 className="text-lg font-semibold text-white">Sources</h2>
          {response?.sources && response.sources.length > 0 ? (
            <div className="space-y-3">
              {response.sources.map((src, idx) => (
                <div
                  key={`${src.source || src.doc_id}-${idx}`}
                  className="rounded-xl border border-slate-700 bg-slate-900/60 p-4"
                >
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                    <span>{src.topic || "misc"}</span>
                    <span>source: {src.source || src.doc_id}</span>
                    {typeof src.chunk_id === "number" && <span>chunk: {src.chunk_id}</span>}
                  </div>
                  <p className="mt-2 text-sm text-slate-200">{src.snippet}</p>
                  <div className="mt-2 text-xs text-slate-500">
                    retrievers: {(src.retrievers || []).join(", ") || "n/a"}
                    {typeof src.score_final === "number" && (
                      <span className="ml-3">score: {src.score_final.toFixed(3)}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No sources yet.</p>
          )}
        </section>
      </div>
    </main>
  );
}
