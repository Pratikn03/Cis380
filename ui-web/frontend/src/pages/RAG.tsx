import { useEffect, useState, type ChangeEvent } from "react";
import { CitationPanel, ErrorState, JsonBlock, PageShell, Panel, PrimaryButton, TextArea, TextInput } from "../components/DashboardPrimitives";
import { ragAsk, ragIndex, ragStatus, ragUpload } from "../services/endpoints";

export default function RAG() {
  const [file, setFile] = useState<File | null>(null);
  const [question, setQuestion] = useState("What does this document say?");
  const [status, setStatus] = useState<Record<string, unknown> | null>(null);
  const [answer, setAnswer] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ragStatus().then((res) => setStatus(res.data)).catch(() => setStatus({ status: "unavailable" }));
  }, []);

  const onFile = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] || null);
    event.target.value = "";
  };

  const upload = async () => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setError(null);
    try {
      await ragUpload(form);
      const { data } = await ragIndex(false);
      setStatus(data);
      setFile(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  const ask = async () => {
    setError(null);
    try {
      const { data } = await ragAsk({ query: question });
      setAnswer(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <PageShell title="RAG" eyebrow="Upload + Citations">
      <div className="grid gap-4 lg:grid-cols-[22rem_1fr]">
        <Panel title="Ingest">
          <input
            type="file"
            aria-label="Upload RAG document"
            onChange={onFile}
            className="text-sm"
          />
          <PrimaryButton onClick={upload} disabled={!file} className="mt-3">
            Upload + Index
          </PrimaryButton>
          <JsonBlock value={status || {}} />
        </Panel>
        <Panel title="Ask">
          <TextInput value={question} onChange={(event) => setQuestion(event.target.value)} />
          <PrimaryButton onClick={ask} className="mt-3">
            Ask
          </PrimaryButton>
          <ErrorState message={error} />
          {answer && (
            <div className="mt-4 space-y-4">
              <TextArea readOnly rows={6} value={answer.answer || ""} />
              <CitationPanel citations={answer.citations || answer.sources || []} />
            </div>
          )}
        </Panel>
      </div>
    </PageShell>
  );
}
