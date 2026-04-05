"use client";

import { useState } from "react";
import { useMediaAnalyze } from "@/lib/hooks/useMediaAnalyze";

export function AnalyzerWorkbench() {
  const [fileName, setFileName] = useState("");
  const [mediaUrl, setMediaUrl] = useState("");
  const { snapshot, error, run, loading } = useMediaAnalyze();

  return (
    <section className="card panel-grid">
      <div className="sf-panel-heading">Analyzer Workbench</div>
      <input className="input" value={fileName} placeholder="File name (optional)" onChange={(e) => setFileName(e.target.value)} />
      <input className="input" value={mediaUrl} placeholder="Media URL (optional)" onChange={(e) => setMediaUrl(e.target.value)} />
      <div className="sf-action-strip">
        <button className="sf-strip-btn strip-purple" type="button" onClick={() => run("voice", { fileName, mediaUrl })}>Voice Emotion</button>
        <button className="sf-strip-btn strip-orange" type="button" onClick={() => run("video", { fileName, mediaUrl })}>Video Emotion</button>
        <button className="sf-strip-btn strip-blue" type="button" onClick={() => run("deepfake", { fileName, mediaUrl })}>Deepfake</button>
        <button className="sf-strip-btn strip-gold" type="button" onClick={() => run("brand", { fileName, mediaUrl })}>Brand Logos</button>
      </div>
      {loading && <div className="muted">Processing analysis...</div>}
      {error && <div className="muted">Error: {error}</div>}
      <pre className="sf-pretty-pre">{JSON.stringify(snapshot, null, 2)}</pre>
    </section>
  );
}
