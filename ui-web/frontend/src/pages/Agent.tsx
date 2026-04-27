import { useMemo, useState, type ChangeEvent } from "react";
import {
  CitationPanel,
  ConfidencePill,
  ErrorState,
  PageShell,
  Panel,
  PrimaryButton,
  SecondaryButton,
  TextArea,
  ToolSteps,
} from "../components/DashboardPrimitives";
import { fetchAgentStream, type AgentStreamEvent } from "../services/api";
import { agentEscalate } from "../services/endpoints";

type Message = {
  role: "user" | "assistant";
  content: string;
  confidence?: number;
};

export default function Agent() {
  const [message, setMessage] = useState("");
  const [uploads, setUploads] = useState<File[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [steps, setSteps] = useState<Array<Record<string, unknown>>>([]);
  const [citations, setCitations] = useState<unknown[]>([]);
  const [finalMeta, setFinalMeta] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const confidence = useMemo(() => {
    if (!finalMeta) return undefined;
    // /api/v1/agent/run envelope shape
    if (typeof finalMeta.confidence === "number") return finalMeta.confidence as number;
    if (typeof finalMeta.intent_confidence === "number") return finalMeta.intent_confidence as number;
    // legacy /api/agent/stream shape
    const result = finalMeta?.result as Record<string, unknown> | undefined;
    const intent = result?.intent_confidence as Record<string, unknown> | undefined;
    return typeof intent?.confidence === "number" ? intent.confidence : undefined;
  }, [finalMeta]);

  const handleFile = (event: ChangeEvent<HTMLInputElement>) => {
    setUploads(Array.from(event.target.files || []));
    event.target.value = "";
  };

  const appendAssistantToken = (text: string) => {
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      if (last?.role === "assistant") {
        next[next.length - 1] = { ...last, content: last.content + text };
      } else {
        next.push({ role: "assistant", content: text });
      }
      return next;
    });
  };

  const handleEvent = (event: AgentStreamEvent) => {
    // /api/v1/agent/run events
    if (event.type === "triage") {
      setSteps((prev) => [...prev, { kind: "triage", ...event.data }]);
      return;
    }
    if (event.type === "thinking_delta") {
      appendAssistantToken(String(event.data.text || ""));
      return;
    }
    if (event.type === "tool_call") {
      setSteps((prev) => [...prev, { kind: "tool_call", ...event.data }]);
      return;
    }
    if (event.type === "tool_result") {
      setSteps((prev) => [...prev, { kind: "tool_result", ...event.data }]);
      return;
    }
    if (event.type === "tool_error") {
      setSteps((prev) => [...prev, { kind: "tool_error", ...event.data }]);
      return;
    }
    if (event.type === "safety_blocked") {
      setError(`Output blocked by safety classifier: ${event.data.reason || "unknown"}`);
      return;
    }
    if (event.type === "final_envelope") {
      const envelope = (event.data.envelope as Record<string, unknown>) || event.data;
      setFinalMeta(envelope);
      const answer = String(envelope.answer || "");
      if (answer) appendAssistantToken(answer);
      const cites = (envelope.citations as unknown[]) || [];
      if (cites.length) setCitations(cites);
      return;
    }
    if (event.type === "trace_start" || event.type === "usage" || event.type === "trace_end" || event.type === "final_message") {
      return;
    }
    if (event.type === "error") {
      setError(String((event.data as Record<string, unknown>).message || "Agent request failed"));
      return;
    }
    // legacy /api/agent/stream events still supported
    if (event.type === "step") setSteps((prev) => [...prev, event.data]);
    if (event.type === "token") appendAssistantToken(String(event.data.text || ""));
    if (event.type === "citation") setCitations((prev) => [...prev, event.data.citation]);
    if (event.type === "final") setFinalMeta(event.data);
  };

  const submit = async () => {
    if ((!message.trim() && uploads.length === 0) || isStreaming) return;
    setError(null);
    setSteps([]);
    setCitations([]);
    setFinalMeta(null);
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content:
          message ||
          `Analyze ${uploads.map((item) => item.name).join(", ")}`,
      },
    ]);
    setIsStreaming(true);
    const payload = new FormData();
    payload.append("message", message);
    for (const upload of uploads) {
      const key = upload.type.startsWith("image/")
        ? "image"
        : upload.type.startsWith("audio/")
          ? "audio"
          : upload.type.startsWith("video/")
            ? "video"
            : "document";
      payload.append(key, upload);
    }
    try {
      await fetchAgentStream(payload, handleEvent);
      setMessage("");
      setUploads([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Agent stream failed");
    } finally {
      setIsStreaming(false);
    }
  };

  const escalate = async () => {
    const last = messages[messages.length - 1];
    await agentEscalate({
      message: last?.content || message || "Agent escalation",
      route: "agent",
      severity: "medium",
      evidence: { steps, citations },
      user_id: "web_user",
    });
    setError("Escalation recorded for analyst review.");
  };

  return (
    <PageShell
      title="Agent"
      eyebrow="Primary Surface"
      actions={confidence !== undefined ? <ConfidencePill value={confidence} /> : undefined}
    >
      <div className="grid gap-4 lg:grid-cols-[1fr_22rem]">
        <Panel title="Streaming Chat">
          <div className="mb-4 h-[28rem] overflow-auto rounded-lg border border-line bg-white p-4">
            {messages.length === 0 && (
              <p className="text-sm text-fog">Ask the agent or attach image, audio, video, or document evidence.</p>
            )}
            {messages.map((item, index) => (
              <div key={index} className={`mb-3 flex ${item.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${item.role === "user" ? "bg-moss text-white" : "bg-sand text-ink"}`}>
                  {item.content}
                </div>
              </div>
            ))}
          </div>
          <div className="space-y-3">
            <TextArea
              rows={3}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Ask about a transaction, alert, document, recommendation, or uploaded media."
            />
            <input
              type="file"
              onChange={handleFile}
              multiple
              aria-label="Upload agent evidence"
              accept="image/*,audio/*,video/*,.pdf,.txt,.md,.json,.csv"
              className="block w-full text-sm text-fog"
            />
            {uploads.length > 0 && (
              <p className="text-xs text-fog">
                Attached: {uploads.map((item) => item.name).join(", ")}
              </p>
            )}
            <div className="flex flex-wrap gap-2">
              <PrimaryButton onClick={submit} disabled={isStreaming}>
                {isStreaming ? "Streaming..." : "Send"}
              </PrimaryButton>
              <SecondaryButton onClick={escalate} disabled={messages.length === 0}>
                Escalate
              </SecondaryButton>
            </div>
            <ErrorState message={error} />
          </div>
        </Panel>
        <div className="space-y-4">
          <Panel title="Tool Steps">
            <ToolSteps steps={steps} />
          </Panel>
          <Panel title="Citations">
            <CitationPanel citations={citations} />
          </Panel>
        </div>
      </div>
    </PageShell>
  );
}
