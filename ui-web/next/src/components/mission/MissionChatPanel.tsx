"use client";

import { useState } from "react";
import { useMissionChat } from "@/lib/hooks/useMissionChat";

export function MissionChatPanel() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<"chat" | "rag" | "movies" | "clothes">("chat");
  const { ask, lastResult, lastError, loading } = useMissionChat();

  return (
    <section className="card panel-grid">
      <div className="sf-panel-heading">Mission Console</div>
      <div className="sf-tab-row">
        <button type="button" className={`sf-tab ${mode === "chat" ? "sf-tab-active" : ""}`} onClick={() => setMode("chat")}>Mission Chat</button>
        <button type="button" className={`sf-tab ${mode === "rag" ? "sf-tab-active" : ""}`} onClick={() => setMode("rag")}>RAG</button>
        <button type="button" className={`sf-tab ${mode === "movies" ? "sf-tab-active" : ""}`} onClick={() => setMode("movies")}>Movies</button>
        <button type="button" className={`sf-tab ${mode === "clothes" ? "sf-tab-active" : ""}`} onClick={() => setMode("clothes")}>Clothes</button>
      </div>
      <input className="input" placeholder="Ask mission chat, movie, clothes, or docs..." value={query} onChange={(e) => setQuery(e.target.value)} />
      <button className="pill-btn" onClick={() => ask(query, mode)}>{loading ? "Running..." : "Run"}</button>
      {lastError && <div className="muted">Error: {lastError}</div>}
      <pre className="sf-pretty-pre">{JSON.stringify(lastResult ?? { status: "idle" }, null, 2)}</pre>
    </section>
  );
}
