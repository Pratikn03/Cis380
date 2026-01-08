import { useEffect, useRef, useState, type ChangeEvent } from "react";
import axios from "axios";
import { api } from "../services/api";
import {
  behaviorScore,
  brandPredict,
  cyberScore,
  fraudScore,
  visionPredict,
  voiceEmotion,
} from "../services/endpoints";

type ToolId = "chat" | "vision" | "brand" | "audio" | "fraud" | "cyber" | "behavior";
type FileToolId = "vision" | "brand" | "audio";
type FeatureToolId = "fraud" | "cyber" | "behavior";

interface RecommendationItem {
  title: string;
  reason: string;
}

interface MessageMeta {
  items?: RecommendationItem[];
  [key: string]: unknown;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  meta?: MessageMeta;
}

type VisionTopKEntry = {
  label?: string;
  prob?: number;
};

type VisionResponse = {
  label?: string;
  confidence?: number;
  top_k?: VisionTopKEntry[];
};

type BrandDetection = {
  brand?: string;
  confidence?: number;
  bbox?: number[];
};

type BrandResponse = {
  detections?: BrandDetection[];
};

type AudioResponse = {
  emotion?: string;
  confidence?: number;
  emotion_vector?: Record<string, number>;
};

type ScoreResponse = {
  score?: number;
  input_features?: number;
  expected_features?: number | null;
};

const toolOptions: Array<{ id: ToolId; label: string; description: string }> = [
  { id: "chat", label: "AI Chat", description: "Ask questions or get recommendations." },
  { id: "vision", label: "Vision", description: "Analyze images for authenticity and labels." },
  { id: "brand", label: "Brand", description: "Detect logos and brand marks in images." },
  { id: "audio", label: "Audio", description: "Detect emotion from audio clips." },
  { id: "fraud", label: "Fraud", description: "Score transaction features for fraud risk." },
  { id: "cyber", label: "Cyber", description: "Score network features for threat risk." },
  { id: "behavior", label: "Behavior", description: "Score user behavior features for anomalies." },
];

const fileToolConfig: Record<FileToolId, { label: string; accept: string; helper: string }> = {
  vision: {
    label: "Vision analysis",
    accept: "image/*",
    helper: "JPG, PNG, WEBP, BMP up to 10MB",
  },
  brand: {
    label: "Brand detection",
    accept: "image/*",
    helper: "JPG, PNG, WEBP, BMP up to 10MB",
  },
  audio: {
    label: "Audio emotion",
    accept: "audio/*",
    helper: "WAV, MP3, M4A, AAC, OGG, FLAC, WEBM up to 25MB",
  },
};

const featureToolConfig: Record<
  FeatureToolId,
  { label: string; helper: string; sample: string }
> = {
  fraud: {
    label: "Fraud score",
    helper: "Enter comma-separated numeric features. The backend pads or trims as needed.",
    sample: "0.42, -1.15, 2.04, 0.11, 0.87, -0.23, 1.02, 0.44",
  },
  cyber: {
    label: "Cyber score",
    helper: "Enter comma-separated numeric features. The backend pads or trims as needed.",
    sample: "0.12, 1.45, 0.88, 0.05, 1.21, 0.33, 0.92, -0.18",
  },
  behavior: {
    label: "Behavior score",
    helper: "Enter comma-separated numeric features. The backend pads or trims as needed.",
    sample: "12, 0.4, 2.2, 0.8, 1.5, 0.1, 0.6, 3.1, 0.02",
  },
};

const suggestions = [
  "Recommend a movie",
  "Recommend action movies",
  "What is fraud detection?",
  "Help",
];

const normalizeConfidence = (value?: number): number | undefined => {
  if (typeof value !== "number" || Number.isNaN(value)) return undefined;
  const normalized = value <= 1 ? value * 100 : value;
  return Math.max(0, Math.min(100, Math.round(normalized)));
};

const formatBytes = (bytes: number): string => {
  if (!Number.isFinite(bytes)) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const parseFeatureList = (raw: string): number[] =>
  raw
    .split(/[\s,]+/)
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value));

const formatFeaturePreview = (values: number[]): string => {
  if (values.length === 0) return "no valid features";
  const preview = values.slice(0, 6).map((value) => value.toFixed(2));
  return values.length > preview.length
    ? `${preview.join(", ")} ... (+${values.length - preview.length} more)`
    : preview.join(", ");
};

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

const formatVisionResponse = (data: VisionResponse): string => {
  const lines = ["Vision result"];
  const label = data.label ? String(data.label) : "Unknown";
  lines.push(`Label: ${label}`);
  const confidence = normalizeConfidence(data.confidence);
  if (confidence !== undefined) {
    lines.push(`Confidence: ${confidence}%`);
  }
  const topK = Array.isArray(data.top_k) ? data.top_k : [];
  if (topK.length > 0) {
    lines.push("Top predictions:");
    topK.slice(0, 3).forEach((entry) => {
      const entryLabel = entry?.label ? String(entry.label) : "Unknown";
      const prob = normalizeConfidence(entry?.prob);
      lines.push(`- ${entryLabel}${prob !== undefined ? ` (${prob}%)` : ""}`);
    });
  }
  return lines.join("\n");
};

const formatBrandResponse = (data: BrandResponse): string => {
  const detections = Array.isArray(data.detections) ? data.detections : [];
  const lines = ["Brand detection"];
  lines.push(`Detections: ${detections.length}`);
  if (detections.length > 0) {
    lines.push("Top detections:");
    detections.slice(0, 3).forEach((det) => {
      const brand = det?.brand ? String(det.brand) : "Unknown";
      const confidence = normalizeConfidence(det?.confidence);
      lines.push(`- ${brand}${confidence !== undefined ? ` (${confidence}%)` : ""}`);
    });
  }
  return lines.join("\n");
};

const formatAudioResponse = (data: AudioResponse): string => {
  const lines = ["Audio emotion"];
  const emotion = data.emotion ? String(data.emotion) : "Unknown";
  lines.push(`Emotion: ${emotion}`);
  const confidence = normalizeConfidence(data.confidence);
  if (confidence !== undefined) {
    lines.push(`Confidence: ${confidence}%`);
  }
  const vector = data.emotion_vector;
  if (vector && typeof vector === "object") {
    const entries = Object.entries(vector).filter(
      ([, value]) => typeof value === "number"
    ) as [string, number][];
    entries.sort((a, b) => b[1] - a[1]);
    if (entries.length > 0) {
      lines.push("Top emotions:");
      entries.slice(0, 3).forEach(([label, value]) => {
        const score = normalizeConfidence(value);
        lines.push(`- ${label}${score !== undefined ? ` (${score}%)` : ""}`);
      });
    }
  }
  return lines.join("\n");
};

const formatScoreResponse = (label: string, data: ScoreResponse, provided: number): string => {
  const lines = [`${label} result`];
  if (typeof data.score === "number") {
    lines.push(`Score: ${data.score.toFixed(4)}`);
  }
  if (typeof data.expected_features === "number") {
    lines.push(`Expected features: ${data.expected_features}`);
  }
  const inputCount = typeof data.input_features === "number" ? data.input_features : provided;
  if (inputCount > 0) {
    lines.push(`Provided features: ${inputCount}`);
  }
  return lines.join("\n");
};

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [featureInput, setFeatureInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [activeTool, setActiveTool] = useState<ToolId>("chat");
  const [isLoading, setIsLoading] = useState(false);
  const [backendUrl, setBackendUrl] = useState(
    localStorage.getItem("backendUrl") || "http://localhost:8000"
  );
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    checkConnection();
  }, [backendUrl]);

  useEffect(() => {
    setSelectedFile(null);
    setFeatureInput("");
  }, [activeTool]);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/health`, { method: "GET" });
      setIsConnected(response.ok);
    } catch {
      setIsConnected(false);
    }
  };

  const updateBackendUrl = (url: string) => {
    setBackendUrl(url);
    localStorage.setItem("backendUrl", url);
    api.defaults.baseURL = url;
  };

  const appendMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  const sendChatMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    appendMessage(userMessage);
    setInput("");
    setIsLoading(true);

    try {
      const { data } = await api.post("/api/chat", {
        text: input,
        user_id: "web_user",
      });
      appendMessage({
        role: "assistant",
        content: data.answer || data.reply || "No response received",
        meta: data.meta,
      });
    } catch (error) {
      appendMessage({
        role: "assistant",
        content: `Error: ${getErrorMessage(error)}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendChatMessage();
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setSelectedFile(file);
    event.target.value = "";
  };

  const handleRunTool = async () => {
    if (isLoading) return;

    const isFileTool = activeTool === "vision" || activeTool === "brand" || activeTool === "audio";
    const isFeatureTool =
      activeTool === "fraud" || activeTool === "cyber" || activeTool === "behavior";

    if (isFileTool) {
      if (!selectedFile) {
        appendMessage({
          role: "assistant",
          content: "Please choose a file before running the analysis.",
        });
        return;
      }
      const fileLabel = fileToolConfig[activeTool].label;
      appendMessage({
        role: "user",
        content: `${fileLabel}: ${selectedFile.name}`,
      });
      setIsLoading(true);
      try {
        const payload = new FormData();
        payload.append("file", selectedFile);
        if (activeTool === "vision") {
          const { data } = await visionPredict(payload);
          appendMessage({ role: "assistant", content: formatVisionResponse(data as VisionResponse) });
        }
        if (activeTool === "brand") {
          const { data } = await brandPredict(payload);
          appendMessage({ role: "assistant", content: formatBrandResponse(data as BrandResponse) });
        }
        if (activeTool === "audio") {
          const { data } = await voiceEmotion(payload);
          appendMessage({ role: "assistant", content: formatAudioResponse(data as AudioResponse) });
        }
      } catch (error) {
        appendMessage({
          role: "assistant",
          content: `Error: ${getErrorMessage(error)}`,
        });
      } finally {
        setIsLoading(false);
      }
      return;
    }

    if (isFeatureTool) {
      const features = parseFeatureList(featureInput);
      if (features.length === 0) {
        appendMessage({
          role: "assistant",
          content: "Please enter numeric features separated by commas.",
        });
        return;
      }
      const toolLabel = featureToolConfig[activeTool].label;
      appendMessage({
        role: "user",
        content: `${toolLabel}: ${formatFeaturePreview(features)}`,
      });
      setIsLoading(true);
      try {
        if (activeTool === "fraud") {
          const { data } = await fraudScore({ features });
          appendMessage({
            role: "assistant",
            content: formatScoreResponse("Fraud", data as ScoreResponse, features.length),
          });
        }
        if (activeTool === "cyber") {
          const { data } = await cyberScore({ features });
          appendMessage({
            role: "assistant",
            content: formatScoreResponse("Cyber", data as ScoreResponse, features.length),
          });
        }
        if (activeTool === "behavior") {
          const { data } = await behaviorScore({ features });
          appendMessage({
            role: "assistant",
            content: formatScoreResponse("Behavior", data as ScoreResponse, features.length),
          });
        }
      } catch (error) {
        appendMessage({
          role: "assistant",
          content: `Error: ${getErrorMessage(error)}`,
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const activeConfig = toolOptions.find((tool) => tool.id === activeTool);
  const isFileTool = activeTool === "vision" || activeTool === "brand" || activeTool === "audio";
  const isFeatureTool =
    activeTool === "fraud" || activeTool === "cyber" || activeTool === "behavior";

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">AI Chat</h1>
          <p className="text-slate-400 mt-1">
            Unified chat with built-in vision, fraud, cyber, behavior, and audio tools.
          </p>
        </div>

        <div className="mb-4 p-4 bg-slate-800/60 rounded-xl border border-slate-700">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="text-sm text-slate-400 block mb-1">Backend URL</label>
              <input
                type="text"
                value={backendUrl}
                onChange={(event) => updateBackendUrl(event.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:border-emerald-500 focus:outline-none"
                placeholder="http://localhost:8000"
              />
            </div>
            <div className="flex items-center gap-2 pt-5">
              <div
                className={`w-3 h-3 rounded-full ${
                  isConnected ? "bg-emerald-500" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-slate-400">
                {isConnected ? "Connected" : "Disconnected"}
              </span>
              <button
                onClick={checkConnection}
                className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg"
              >
                Test
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          {toolOptions.map((tool) => (
            <button
              key={tool.id}
              onClick={() => setActiveTool(tool.id)}
              className={
                activeTool === tool.id
                  ? "rounded-xl border border-emerald-500 bg-emerald-500/20 px-4 py-3 text-emerald-200 text-sm font-semibold"
                  : "rounded-xl border border-slate-700 bg-slate-800/50 px-4 py-3 text-slate-400 text-sm font-semibold hover:border-slate-500"
              }
            >
              {tool.label}
            </button>
          ))}
        </div>

        <div className="mb-4 rounded-2xl border border-slate-700 bg-slate-800/60 p-4">
          <div className="mb-3">
            <p className="text-xs uppercase tracking-wide text-slate-500">Active Tool</p>
            <p className="text-lg font-semibold text-white">{activeConfig?.label}</p>
            <p className="text-sm text-slate-400">{activeConfig?.description}</p>
          </div>

          {isFileTool && (
            <div className="rounded-xl border border-dashed border-slate-700 bg-slate-900/60 p-4">
              <input
                key={activeTool}
                ref={fileInputRef}
                type="file"
                accept={fileToolConfig[activeTool].accept}
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-200">
                    {fileToolConfig[activeTool].label}
                  </p>
                  <p className="text-xs text-slate-500">{fileToolConfig[activeTool].helper}</p>
                  <p className="text-sm text-slate-300 mt-2">
                    {selectedFile
                      ? `${selectedFile.name} (${formatBytes(selectedFile.size)})`
                      : "No file selected yet."}
                  </p>
                </div>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 border border-slate-600 text-slate-300 rounded-lg hover:border-emerald-400 transition-all"
                  disabled={isLoading}
                >
                  Choose File
                </button>
              </div>
            </div>
          )}

          {isFeatureTool && (
            <div className="space-y-3">
              <textarea
                value={featureInput}
                onChange={(event) => setFeatureInput(event.target.value)}
                placeholder="0.5, -1.2, 3.4, 0.0, 1.8"
                className="w-full h-28 bg-slate-900 border border-slate-700 rounded-xl p-4 text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none resize-none"
              />
              <div className="flex flex-wrap gap-3 items-center">
                <button
                  onClick={() => setFeatureInput(featureToolConfig[activeTool].sample)}
                  className="px-3 py-2 text-xs border border-slate-600 text-slate-300 rounded-lg hover:border-emerald-400 transition-all"
                  disabled={isLoading}
                >
                  Use sample features
                </button>
                <p className="text-xs text-slate-500">{featureToolConfig[activeTool].helper}</p>
              </div>
            </div>
          )}

          {!isFileTool && !isFeatureTool && (
            <p className="text-sm text-slate-400">
              Use the chat input below to talk with SentinelForge or ask for recommendations.
            </p>
          )}
        </div>

        <div className="bg-slate-800/60 rounded-2xl border border-slate-700 overflow-hidden">
          <div className="h-[520px] overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && activeTool === "chat" ? (
              <div className="text-center py-12">
                <p className="text-slate-400 mb-6">Start a conversation! Try one of these:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setInput(suggestion)}
                      className="px-4 py-2 bg-slate-700 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-300 rounded-lg text-sm transition-all border border-slate-600 hover:border-emerald-500/50"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-slate-400">
                  Ready when you are. Add inputs above, then run the active tool.
                </p>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={index}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-emerald-500 text-slate-900"
                        : "bg-slate-700 text-slate-200"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.meta?.items && msg.meta.items.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-slate-600/50">
                        <p className="text-xs opacity-70 mb-2">Recommendations:</p>
                        {msg.meta.items.slice(0, 5).map((item, j) => (
                          <div key={j} className="text-sm py-1">
                            <span className="font-medium">
                              {j + 1}. {item.title}
                            </span>
                            {item.reason && (
                              <span className="opacity-70 text-xs block">{item.reason}</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-700 text-slate-200 rounded-2xl px-4 py-3">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-100" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-200" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-slate-700 p-4">
            {activeTool === "chat" ? (
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                  disabled={isLoading}
                />
                <button
                  onClick={sendChatMessage}
                  disabled={isLoading || !input.trim()}
                  className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-semibold rounded-xl transition-all"
                >
                  Send
                </button>
              </div>
            ) : (
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={handleRunTool}
                  disabled={
                    isLoading ||
                    (isFileTool && !selectedFile) ||
                    (isFeatureTool && !featureInput.trim())
                  }
                  className="px-6 py-3 bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-semibold rounded-xl transition-all"
                >
                  {isLoading ? "Running..." : "Run Analysis"}
                </button>
                <button
                  onClick={() => {
                    setFeatureInput("");
                    setSelectedFile(null);
                  }}
                  className="px-6 py-3 border border-slate-600 text-slate-300 rounded-xl hover:border-emerald-400 transition-all"
                  disabled={isLoading}
                >
                  Clear Input
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 text-center text-sm text-slate-500">
          <p>
            💡 To connect from GitHub Pages, run your backend with ngrok:{" "}
            <code className="bg-slate-800 px-2 py-1 rounded">ngrok http 8000</code>
          </p>
        </div>
      </div>
    </main>
  );
}
