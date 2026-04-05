"use client";

import { useMutation, useSubscription } from "@apollo/client";
import { useState } from "react";
import { AnalyzerWorkbench } from "@/components/media/AnalyzerWorkbench";
import { OfflineBanner } from "@/components/dashboard/OfflineBanner";
import { CREATE_UPLOAD_SESSION, FINALIZE_UPLOAD, INFERENCE_TRACE } from "@/lib/gateway-graphql";

export default function LiveMediaPage() {
  const [file, setFile] = useState<File | null>(null);
  const [tool, setTool] = useState("vision");
  const [correlationId, setCorrelationId] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  const [createSession, { loading: creating }] = useMutation(CREATE_UPLOAD_SESSION);
  const [finalizeUpload, { loading: finalizing }] = useMutation(FINALIZE_UPLOAD);

  const { data: traceData, error: traceError } = useSubscription(INFERENCE_TRACE, {
    skip: !correlationId,
    variables: { correlationId },
  });

  const onUpload = async () => {
    if (!file) return;
    setError("");
    try {
      const sessionRes = await createSession({
        variables: {
          input: {
            fileName: file.name,
            contentType: file.type || "application/octet-stream",
            maxBytes: file.size,
          },
        },
      });

      const session = sessionRes.data?.createUploadSession;
      if (!session?.uploadUrl || !session?.objectKey) {
        throw new Error("Upload session creation failed.");
      }

      const put = await fetch(session.uploadUrl, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": file.type || "application/octet-stream",
        },
      });
      if (!put.ok) {
        throw new Error(`Direct upload failed with status ${put.status}`);
      }

      const cid = crypto.randomUUID();
      setCorrelationId(cid);

      const finalizeRes = await finalizeUpload({
        variables: {
          input: {
            objectKey: session.objectKey,
            tool,
            correlationId: cid,
          },
        },
      });

      setResult(finalizeRes.data?.finalizeUpload ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="sf-page-stack">
      <section className="sf-page-head card">
        <div>
          <h1 className="sf-page-title">Media Studio</h1>
          <p className="muted">Voice emotion, video emotion, deepfake, and brand/logo analysis workspace.</p>
        </div>
        <div className="sf-tab-row">
          <button className="sf-tab sf-tab-active" type="button">Upload</button>
          <button className="sf-tab" type="button">Analyze</button>
          <button className="sf-tab" type="button">Trace</button>
        </div>
      </section>

      {traceError && (
        <OfflineBanner title="Trace stream unavailable:" subtitle="you can still submit uploads and run analysis actions." />
      )}

      <section className="sf-two-col">
        <article className="card panel-grid">
          <div className="sf-panel-heading">Pre-Signed Upload</div>
          <select className="input" value={tool} onChange={(e) => setTool(e.target.value)}>
            <option value="vision">Vision</option>
            <option value="voice">Voice</option>
            <option value="video">Video</option>
            <option value="brand">Brand</option>
            <option value="rag">RAG Docs</option>
          </select>
          <input className="input" type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          <button className="pill-btn" onClick={onUpload}>{creating || finalizing ? "Processing..." : "Upload + Finalize"}</button>
          {error && <p className="muted">Error: {error}</p>}
          <pre className="sf-pretty-pre">{JSON.stringify(result ?? { status: "waiting" }, null, 2)}</pre>
        </article>

        <article className="card panel-grid">
          <div className="sf-panel-heading">Inference Trace</div>
          <pre className="sf-pretty-pre">
            {traceData?.inferenceTrace
              ? JSON.stringify(traceData.inferenceTrace, null, 2)
              : "Waiting for trace events..."}
          </pre>
        </article>
      </section>

      <AnalyzerWorkbench />
    </div>
  );
}
