import { useEffect, useRef, useState } from "react";
import clsx from "clsx";
import SectionHeader from "../components/SectionHeader";
import {
  chat,
  multimodalChat,
  riskAnalyze,
  brandPredict,
  voiceEmotion,
  fraudScore,
  cyberScore,
  behaviorScore,
  behaviorLogs,
  visionPredict,
  recommendMultimodal,
  ragQuery,
  ragUpload,
  visionVideoPredict,
} from "../services/endpoints";

type RecommendationItem = {
  title?: string;
  name?: string;
  brand?: string;
  category?: string;
  reason?: string;
  overview?: string;
  genres?: string[] | string;
  popularity?: number;
  price_usd?: number;
  url?: string;
};

type ChatResponse = {
  route?: string;
  answer?: string;
  meta?: {
    category?: string;
    items?: RecommendationItem[];
    attachments?: Record<string, any>;
  };
};

type ChatMessage = {
  role: "user" | "assistant" | "system";
  content: string;
};

const parseVector = (raw: string) =>
  raw
    .split(/[^-0-9.]+/)
    .filter(Boolean)
    .map((value) => Number(value))
    .filter((value) => !Number.isNaN(value));

const formatItemMeta = (item: RecommendationItem) => {
  const bits: string[] = [];
  if (item.brand) bits.push(`Brand: ${item.brand}`);
  if (item.category) bits.push(`Category: ${item.category}`);
  if (item.genres) {
    const genres = Array.isArray(item.genres) ? item.genres.join(", ") : item.genres;
    bits.push(`Genres: ${genres}`);
  }
  if (typeof item.popularity === "number") bits.push(`Popularity: ${item.popularity}`);
  if (typeof item.price_usd === "number") bits.push(`Price: $${item.price_usd.toFixed(0)}`);
  return bits.join(" • ");
};

const formatError = (err: any, fallback: string) =>
  err?.response?.data?.detail || err?.message || fallback;

const dataUrlToFile = (dataUrl: string, filename: string) => {
  const [header, data] = dataUrl.split(",");
  const mimeMatch = header.match(/data:(.*?);base64/);
  const mime = mimeMatch ? mimeMatch[1] : "image/jpeg";
  const binary = atob(data);
  const array = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    array[i] = binary.charCodeAt(i);
  }
  return new File([array], filename, { type: mime });
};

const audioMimeCandidates = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/aac",
  "audio/mpeg",
];

const pickAudioMimeType = () => {
  if (typeof MediaRecorder === "undefined" || !MediaRecorder.isTypeSupported) {
    return null;
  }
  return audioMimeCandidates.find((type) => MediaRecorder.isTypeSupported(type)) || null;
};

const extensionForMime = (mimeType: string | null) => {
  if (!mimeType) return "webm";
  if (mimeType.includes("mp4")) return "mp4";
  if (mimeType.includes("mpeg")) return "mp3";
  if (mimeType.includes("aac")) return "aac";
  return "webm";
};

export default function CommandCenter() {
  const defaultChatPrompt = "Show me thriller movies with smart plots.";
  const [chatText, setChatText] = useState(defaultChatPrompt);
  const [chatData, setChatData] = useState<ChatResponse | null>(null);
  const [chatError, setChatError] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Welcome to SentinelForge. Ask for movies, fraud checks, or upload media for analysis.",
    },
  ]);

  const [imageFile, setImageFile] = useState<File | null>(null);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  const [mediaError, setMediaError] = useState<string | null>(null);
  const [recordingMimeType, setRecordingMimeType] = useState<string | null>(null);

  const [brandFile, setBrandFile] = useState<File | null>(null);
  const [visionFile, setVisionFile] = useState<File | null>(null);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [voiceFile, setVoiceFile] = useState<File | null>(null);
  const [behaviorLogFile, setBehaviorLogFile] = useState<File | null>(null);
  const [recommendFile, setRecommendFile] = useState<File | null>(null);
  const [ragUploadFile, setRagUploadFile] = useState<File | null>(null);

  const [riskPayload, setRiskPayload] = useState({
    login_country: "US",
    device_known: true,
    login_time: 9,
    clicks_per_minute: 40,
    files_accessed: 12,
    transaction_amount: 120,
  });
  const [riskResult, setRiskResult] = useState<string | null>(null);
  const [brandResult, setBrandResult] = useState<string | null>(null);
  const [visionResult, setVisionResult] = useState<string | null>(null);
  const [videoResult, setVideoResult] = useState<string | null>(null);
  const [voiceResult, setVoiceResult] = useState<string | null>(null);
  const [fraudResult, setFraudResult] = useState<string | null>(null);
  const [cyberResult, setCyberResult] = useState<string | null>(null);
  const [behaviorResult, setBehaviorResult] = useState<string | null>(null);
  const [behaviorLogResult, setBehaviorLogResult] = useState<string | null>(null);
  const [recommendResult, setRecommendResult] = useState<string | null>(null);
  const [ragQueryText, setRagQueryText] = useState("What does the fraud model do?");
  const [ragResult, setRagResult] = useState<string | null>(null);
  const [ragUploadResult, setRagUploadResult] = useState<string | null>(null);

  const [fraudVector, setFraudVector] = useState("120, 0, 1, 0, 50, 0");
  const [cyberVector, setCyberVector] = useState("0.2, 0.1, 0.9, 0.3, 0.2, 0.6");
  const [behaviorVector, setBehaviorVector] = useState("0.5, 1.2, 0.2, 0.1, 0.3");
  const [recommendText, setRecommendText] = useState("streetwear sneakers for fall");
  const [videoFps, setVideoFps] = useState(1);
  const [videoMaxFrames, setVideoMaxFrames] = useState(24);
  const [busy, setBusy] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const cameraStreamRef = useRef<MediaStream | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const [cameraActive, setCameraActive] = useState(false);
  const [recording, setRecording] = useState(false);

  const riskCountries = ["US", "CA", "UK", "DE", "IN", "BR", "NG", "RU", "AE", "SG", "ZA"];
  const riskPresets = [
    {
      label: "Low Risk",
      payload: {
        login_country: "US",
        device_known: true,
        login_time: 10,
        clicks_per_minute: 30,
        files_accessed: 6,
        transaction_amount: 80,
      },
    },
    {
      label: "High Risk",
      payload: {
        login_country: "NG",
        device_known: false,
        login_time: 2,
        clicks_per_minute: 180,
        files_accessed: 120,
        transaction_amount: 4200,
      },
    },
    {
      label: "Account Takeover",
      payload: {
        login_country: "RU",
        device_known: false,
        login_time: 3,
        clicks_per_minute: 220,
        files_accessed: 240,
        transaction_amount: 8600,
      },
    },
  ];

  const moduleLinks = [
    { id: "module-chat", label: "Chat" },
    { id: "module-tools", label: "Tools" },
  ];

  useEffect(() => {
    if (!imageFile) {
      setImagePreview(null);
      return;
    }
    const url = URL.createObjectURL(imageFile);
    setImagePreview(url);
    return () => URL.revokeObjectURL(url);
  }, [imageFile]);

  useEffect(() => {
    if (!audioFile) {
      setAudioPreview(null);
      return;
    }
    const url = URL.createObjectURL(audioFile);
    setAudioPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [audioFile]);

  useEffect(() => {
    return () => {
      stopCamera();
      stopRecording();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const stopCamera = () => {
    cameraStreamRef.current?.getTracks().forEach((track) => track.stop());
    cameraStreamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
  };

  const startCamera = async () => {
    setMediaError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setMediaError("Camera access is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      cameraStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(() => undefined);
        };
      }
      setCameraActive(true);
    } catch (err: any) {
      setMediaError(err?.message || "Camera permission denied.");
    }
  };

  const capturePhoto = () => {
    if (!cameraActive || !videoRef.current) {
      setMediaError("Camera is not active. Press Start first.");
      return;
    }
    const video = videoRef.current;
    if (!video.videoWidth) {
      setMediaError("Camera not ready yet. Wait for preview, then capture.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 360;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setMediaError("Could not capture frame.");
      return;
    }
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
      (blob) => {
        if (blob) {
          const file = new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" });
          setImageFile(file);
          return;
        }
        const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
        setImageFile(dataUrlToFile(dataUrl, `capture-${Date.now()}.jpg`));
      },
      "image/jpeg",
      0.92
    );
  };

  const startRecording = async () => {
    setMediaError(null);
    if (!navigator.mediaDevices?.getUserMedia) {
      setMediaError("Microphone access is not supported in this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      const mimeType = pickAudioMimeType();
      let recorder: MediaRecorder;
      try {
        recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
      } catch (err) {
        recorder = new MediaRecorder(stream);
      }
      recorderRef.current = recorder;
      setRecordingMimeType(mimeType || recorder.mimeType || null);
      audioChunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      recorder.onstop = () => {
        const finalMime = recordingMimeType || recorder.mimeType || "audio/webm";
        const blob = new Blob(audioChunksRef.current, { type: finalMime });
        const ext = extensionForMime(finalMime);
        const file = new File([blob], `recording-${Date.now()}.${ext}`, {
          type: finalMime,
        });
        setAudioFile(file);
        audioStreamRef.current?.getTracks().forEach((track) => track.stop());
        audioStreamRef.current = null;
      };
      recorder.start();
      setRecording(true);
    } catch (err: any) {
      setMediaError(err?.message || "Microphone permission denied.");
    }
  };

  const stopRecording = () => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    setRecording(false);
  };

  const handleChat = async (overrideMessage?: string) => {
    const rawMessage = overrideMessage ?? chatText;
    const trimmed = rawMessage.trim();
    if (!trimmed && !imageFile && !audioFile) {
      return;
    }
    const shouldAutoAnalyze =
      (imageFile || audioFile) && trimmed === defaultChatPrompt;
    const message =
      shouldAutoAnalyze || !trimmed
        ? "Analyze the attached media and respond."
        : trimmed;
    if (busy === "chat") return;

    setBusy("chat");
    setChatData(null);
    setChatError(null);
    setChatText("");
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    try {
      let payload: ChatResponse;
      if (imageFile || audioFile) {
        const formData = new FormData();
        formData.append("message", message);
        formData.append("user_id", "web-ui");
        formData.append("use_rag", "true");
        if (imageFile) {
          formData.append("image", imageFile);
        }
        if (audioFile) {
          formData.append("audio", audioFile);
        }
        const res = await multimodalChat(formData);
        payload = res.data as ChatResponse;
      } else {
        const res = await chat({ message });
        payload = res.data as ChatResponse;
      }
      setChatData(payload);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: payload.answer || "" },
      ]);
      setImageFile(null);
      setAudioFile(null);
    } catch (err: any) {
      const messageText = formatError(err, "Chat request failed.");
      setChatError(messageText);
      setMessages((prev) => [...prev, { role: "system", content: messageText }]);
    } finally {
      setBusy(null);
    }
  };

  const handleRisk = async () => {
    setBusy("risk");
    setRiskResult(null);
    try {
      const res = await riskAnalyze(riskPayload);
      setRiskResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setRiskResult(formatError(err, "Risk request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleBrand = async (file: File | null) => {
    if (!file) {
      setBrandResult("Select a logo image first.");
      return;
    }
    setBusy("brand");
    setBrandResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await brandPredict(formData);
      setBrandResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setBrandResult(formatError(err, "Brand logo request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleVision = async (file: File | null) => {
    if (!file) {
      setVisionResult("Select an image for vision classification.");
      return;
    }
    setBusy("vision");
    setVisionResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await visionPredict(formData);
      setVisionResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setVisionResult(formatError(err, "Vision request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleVideo = async (file: File | null) => {
    if (!file) {
      setVideoResult("Select a video file first.");
      return;
    }
    setBusy("video");
    setVideoResult(null);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("fps", String(videoFps));
    formData.append("max_frames", String(videoMaxFrames));
    try {
      const res = await visionVideoPredict(formData);
      setVideoResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setVideoResult(formatError(err, "Video analysis failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleVoice = async (file: File | null) => {
    if (!file) {
      setVoiceResult("Select an audio clip first.");
      return;
    }
    setBusy("voice");
    setVoiceResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await voiceEmotion(formData);
      setVoiceResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setVoiceResult(formatError(err, "Voice request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleFraud = async () => {
    setBusy("fraud");
    setFraudResult(null);
    const values = parseVector(fraudVector);
    if (!values.length) {
      setFraudResult("Enter numeric features to score fraud.");
      setBusy(null);
      return;
    }
    try {
      const res = await fraudScore({ features: values });
      setFraudResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setFraudResult(formatError(err, "Fraud request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleCyber = async () => {
    setBusy("cyber");
    setCyberResult(null);
    const values = parseVector(cyberVector);
    if (!values.length) {
      setCyberResult("Enter numeric features to score cyber risk.");
      setBusy(null);
      return;
    }
    try {
      const res = await cyberScore({ features: values });
      setCyberResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setCyberResult(formatError(err, "Cyber request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleBehavior = async () => {
    setBusy("behavior");
    setBehaviorResult(null);
    const values = parseVector(behaviorVector);
    if (!values.length) {
      setBehaviorResult("Enter numeric features to score behavior risk.");
      setBusy(null);
      return;
    }
    try {
      const res = await behaviorScore({ features: values });
      setBehaviorResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setBehaviorResult(formatError(err, "Behavior request failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleBehaviorLogs = async () => {
    if (!behaviorLogFile) {
      setBehaviorLogResult("Upload a CSV log file first.");
      return;
    }
    setBusy("behaviorLogs");
    setBehaviorLogResult(null);
    const formData = new FormData();
    formData.append("file", behaviorLogFile);
    try {
      const res = await behaviorLogs(formData);
      setBehaviorLogResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setBehaviorLogResult(formatError(err, "Behavior log scoring failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleRecommend = async () => {
    const hasText = Boolean(recommendText.trim());
    const hasImage = Boolean(recommendFile || imageFile);
    if (!hasText && !hasImage) {
      setRecommendResult("Provide a text prompt or image to get recommendations.");
      return;
    }
    setBusy("recommend");
    setRecommendResult(null);
    const formData = new FormData();
    if (hasText) {
      formData.append("text", recommendText.trim());
    }
    if (hasImage) {
      formData.append("image", recommendFile || (imageFile as File));
    }
    try {
      const res = await recommendMultimodal(formData);
      setRecommendResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setRecommendResult(formatError(err, "Multimodal recommendation failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleRagQuery = async () => {
    if (!ragQueryText.trim()) {
      setRagResult("Enter a question to query your knowledge base.");
      return;
    }
    setBusy("ragQuery");
    setRagResult(null);
    try {
      const res = await ragQuery({ query: ragQueryText.trim(), top_k: 3 });
      setRagResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setRagResult(formatError(err, "RAG query failed."));
    } finally {
      setBusy(null);
    }
  };

  const handleRagUpload = async () => {
    if (!ragUploadFile) {
      setRagUploadResult("Upload a .md or .txt file first.");
      return;
    }
    setBusy("ragUpload");
    setRagUploadResult(null);
    const formData = new FormData();
    formData.append("file", ragUploadFile);
    try {
      const res = await ragUpload(formData);
      setRagUploadResult(JSON.stringify(res.data, null, 2));
    } catch (err: any) {
      setRagUploadResult(formatError(err, "RAG upload failed."));
    } finally {
      setBusy(null);
    }
  };

  const attachments = chatData?.meta?.attachments || null;
  const attachmentLines = attachments
    ? [
        attachments.vision_image
          ? `Vision label: ${attachments.vision_image.label} (confidence ${attachments.vision_image.confidence ?? "-"})`
          : null,
        attachments.face_emotion
          ? `Face emotion: ${attachments.face_emotion.emotion} (confidence ${attachments.face_emotion.confidence ?? "-"})`
          : null,
        attachments.voice
          ? `Voice emotion: ${attachments.voice.emotion} (confidence ${attachments.voice.confidence ?? "-"})`
          : null,
        attachments.image_tags && attachments.image_tags.length
          ? `Image tags: ${attachments.image_tags.join(", ")}`
          : null,
        attachments.stt?.text ? `Transcript: ${attachments.stt.text}` : null,
        attachments.voice_error ? `Voice error: ${attachments.voice_error}` : null,
        attachments.face_emotion_error
          ? `Face model error: ${attachments.face_emotion_error}`
          : null,
        attachments.vision_image_error
          ? `Vision error: ${attachments.vision_image_error}`
          : null,
        attachments.stt_error ? `Transcription error: ${attachments.stt_error}` : null,
      ].filter(Boolean)
    : [];

  return (
    <main className="px-6 py-10">
      <div className="mx-auto max-w-5xl space-y-6">
        <SectionHeader
          eyebrow="Live Console"
          title="Unified multimodal command workspace"
          description="Chat, upload media, capture live inputs, and run fraud/cyber/behavior scoring in one place."
        />
        <div className="flex flex-wrap gap-2">
          {moduleLinks.map((link) => (
            <a
              key={link.id}
              href={`#${link.id}`}
              className="rounded-full border border-line px-3 py-1 text-xs font-semibold text-fog hover:border-moss"
            >
              {link.label}
            </a>
          ))}
        </div>

        <section id="module-chat" className="card-panel flex flex-col px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-display font-semibold">Live Chat</h3>
              <p className="text-xs text-fog">POST /api/chat or /api/chat/multimodal</p>
            </div>
            <span className="tag text-fog">Session</span>
          </div>

          <div className="mt-5 flex-1 space-y-4 overflow-y-auto pr-2">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={clsx(
                  "flex",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={clsx(
                    "max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-3 text-sm",
                    message.role === "user"
                      ? "bg-moss text-white"
                      : message.role === "system"
                      ? "border border-amber-200 bg-amber-50 text-amber-900"
                      : "border border-line bg-white text-ink"
                  )}
                >
                  {message.content}
                </div>
              </div>
            ))}
            {busy === "chat" && <p className="text-xs text-fog">Thinking...</p>}
          </div>

          <div className="mt-4 border-t border-line pt-4">
            <textarea
              value={chatText}
              onChange={(event) => setChatText(event.target.value)}
              className="w-full rounded-2xl border border-line p-3 text-sm"
              rows={3}
              placeholder="Ask SentinelForge for movies, outfits, fraud scoring, or brand analysis..."
            />
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-fog">Tip: try "recommend outfits" or "analyze this logo".</p>
              <div className="flex gap-3">
                {(imageFile || audioFile) && (
                  <button
                    onClick={() =>
                      handleChat(
                        "Analyze the attached media and describe what you see or hear."
                      )
                    }
                    className="rounded-full border border-line px-4 py-2 text-sm font-semibold text-fog"
                    disabled={busy === "chat"}
                  >
                    Analyze Media
                  </button>
                )}
                <button
                  onClick={() => handleChat()}
                  className="rounded-full bg-moss px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                  disabled={busy === "chat"}
                >
                  {busy === "chat" ? "Running..." : "Send"}
                </button>
              </div>
            </div>
            {chatError && <p className="mt-3 text-xs text-amber-700">{chatError}</p>}

            <details className="mt-5 rounded-2xl border border-line bg-white p-4" open>
              <summary className="cursor-pointer text-sm font-semibold text-ink">
                Attachments and Live Capture
              </summary>
              <div className="mt-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <label className="text-xs font-semibold text-fog">
                    Attach Image
                    <input
                      type="file"
                      accept="image/*"
                      className="mt-2 block w-full text-xs"
                      onChange={(event) => setImageFile(event.target.files?.[0] || null)}
                    />
                  </label>
                  <label className="text-xs font-semibold text-fog">
                    Attach Audio
                    <input
                      type="file"
                      accept="audio/*"
                      className="mt-2 block w-full text-xs"
                      onChange={(event) => setAudioFile(event.target.files?.[0] || null)}
                    />
                  </label>
                </div>

                {(imagePreview || audioPreview) && (
                  <div className="flex flex-wrap items-center gap-3">
                    {imagePreview && (
                      <img
                        src={imagePreview}
                        alt="Attachment preview"
                        className="h-16 w-24 rounded-xl border border-line object-cover"
                      />
                    )}
                    {audioPreview && <audio controls src={audioPreview} className="h-8" />}
                    <button
                      type="button"
                      onClick={() => {
                        setImageFile(null);
                        setAudioFile(null);
                      }}
                      className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                    >
                      Clear attachments
                    </button>
                  </div>
                )}

                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-ink">Camera</p>
                      <div className="flex gap-2">
                        {!cameraActive ? (
                          <button
                            type="button"
                            className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                            onClick={startCamera}
                          >
                            Start
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                            onClick={stopCamera}
                          >
                            Stop
                          </button>
                        )}
                        <button
                          type="button"
                          className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                          onClick={capturePhoto}
                          disabled={!cameraActive}
                        >
                          Capture
                        </button>
                      </div>
                    </div>
                    <div className="mt-3 overflow-hidden rounded-2xl border border-line bg-slate-100">
                      <video ref={videoRef} className="h-40 w-full object-cover" muted playsInline />
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-ink">Microphone</p>
                      {!recording ? (
                        <button
                          type="button"
                          className="rounded-full bg-ember px-3 py-1 text-xs text-white"
                          onClick={startRecording}
                        >
                          Record
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                          onClick={stopRecording}
                        >
                          Stop
                        </button>
                      )}
                    </div>
                    {audioPreview && <audio controls src={audioPreview} className="mt-3 h-8 w-full" />}
                    {!audioPreview && (
                      <p className="mt-3 text-xs text-fog">
                        If recording fails, upload an audio file instead.
                      </p>
                    )}
                  </div>
                </div>
                {mediaError && <p className="text-xs text-amber-700">{mediaError}</p>}
              </div>
            </details>
          </div>
        </section>

        {attachmentLines.length > 0 && (
          <div className="card-panel px-6 py-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-fog">
              Multimodal Summary
            </h3>
            <ul className="mt-4 space-y-2 text-sm text-ink">
              {attachmentLines.map((line, index) => (
                <li key={`${line}-${index}`} className="rounded-xl border border-line p-3">
                  {line}
                </li>
              ))}
            </ul>
          </div>
        )}

        <section id="module-tools" className="card-panel px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-display font-semibold">Tools and Modules</h3>
              <p className="text-xs text-fog">Expand a module to run it.</p>
            </div>
          </div>

          <div className="mt-5 space-y-4">
            <details className="rounded-2xl border border-line bg-white p-4" open>
              <summary className="cursor-pointer text-sm font-semibold text-ink">Risk Simulator</summary>
              <p className="text-xs text-fog">POST /api/risk/analyze</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {riskPresets.map((preset) => (
                  <button
                    key={preset.label}
                    type="button"
                    className="rounded-full border border-line px-4 py-2 text-xs font-semibold text-fog hover:border-ember"
                    onClick={() => setRiskPayload(preset.payload)}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              <div className="mt-4 grid gap-4">
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Login Country
                  <select
                    value={riskPayload.login_country}
                    onChange={(event) =>
                      setRiskPayload({ ...riskPayload, login_country: event.target.value })
                    }
                    className="mt-2 w-full rounded-xl border border-line bg-white p-3 text-sm"
                  >
                    {riskCountries.map((country) => (
                      <option key={country} value={country}>
                        {country}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Login Time (hour)
                  <input
                    type="number"
                    min={0}
                    max={23}
                    value={riskPayload.login_time}
                    onChange={(event) =>
                      setRiskPayload({ ...riskPayload, login_time: Number(event.target.value) })
                    }
                    className="mt-2 w-full rounded-xl border border-line p-3 text-sm"
                  />
                </label>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Clicks Per Minute
                  <input
                    type="number"
                    min={0}
                    value={riskPayload.clicks_per_minute}
                    onChange={(event) =>
                      setRiskPayload({
                        ...riskPayload,
                        clicks_per_minute: Number(event.target.value),
                      })
                    }
                    className="mt-2 w-full rounded-xl border border-line p-3 text-sm"
                  />
                </label>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Files Accessed
                  <input
                    type="number"
                    min={0}
                    value={riskPayload.files_accessed}
                    onChange={(event) =>
                      setRiskPayload({
                        ...riskPayload,
                        files_accessed: Number(event.target.value),
                      })
                    }
                    className="mt-2 w-full rounded-xl border border-line p-3 text-sm"
                  />
                </label>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Transaction Amount
                  <input
                    type="number"
                    min={0}
                    value={riskPayload.transaction_amount}
                    onChange={(event) =>
                      setRiskPayload({
                        ...riskPayload,
                        transaction_amount: Number(event.target.value),
                      })
                    }
                    className="mt-2 w-full rounded-xl border border-line p-3 text-sm"
                  />
                </label>
                <label className="flex items-center gap-3 text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  <input
                    type="checkbox"
                    checked={riskPayload.device_known}
                    onChange={(event) =>
                      setRiskPayload({ ...riskPayload, device_known: event.target.checked })
                    }
                    className="h-4 w-4 rounded border-line"
                  />
                  Device Known
                </label>
              </div>
              <button
                onClick={handleRisk}
                className="mt-5 rounded-full bg-ember px-5 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-70"
                disabled={busy === "risk"}
              >
                {busy === "risk" ? "Running..." : "Analyze Risk"}
              </button>
              {riskResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {riskResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Fraud Scoring</summary>
              <p className="text-xs text-fog">POST /api/fraud</p>
              <input
                value={fraudVector}
                onChange={(event) => setFraudVector(event.target.value)}
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                  onClick={() => setFraudVector("120, 0, 1, 0, 50, 0")}
                >
                  Sample vector
                </button>
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleFraud}
                  disabled={busy === "fraud"}
                >
                  {busy === "fraud" ? "Running..." : "Score Fraud"}
                </button>
              </div>
              {fraudResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {fraudResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Cyber Scoring</summary>
              <p className="text-xs text-fog">POST /api/cyber</p>
              <input
                value={cyberVector}
                onChange={(event) => setCyberVector(event.target.value)}
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                  onClick={() => setCyberVector("0.2, 0.1, 0.9, 0.3, 0.2, 0.6")}
                >
                  Sample vector
                </button>
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleCyber}
                  disabled={busy === "cyber"}
                >
                  {busy === "cyber" ? "Running..." : "Score Cyber"}
                </button>
              </div>
              {cyberResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {cyberResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Behavior Scoring</summary>
              <p className="text-xs text-fog">POST /api/behavior</p>
              <input
                value={behaviorVector}
                onChange={(event) => setBehaviorVector(event.target.value)}
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                  onClick={() => setBehaviorVector("0.5, 1.2, 0.2, 0.1, 0.3")}
                >
                  Sample vector
                </button>
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleBehavior}
                  disabled={busy === "behavior"}
                >
                  {busy === "behavior" ? "Running..." : "Score Behavior"}
                </button>
              </div>
              {behaviorResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {behaviorResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Behavior Log Analyzer</summary>
              <p className="text-xs text-fog">POST /api/behavior/logs</p>
              <input
                type="file"
                accept=".csv"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setBehaviorLogFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleBehaviorLogs}
                  disabled={busy === "behaviorLogs"}
                >
                  {busy === "behaviorLogs" ? "Running..." : "Analyze Logs"}
                </button>
              </div>
              {behaviorLogResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {behaviorLogResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Brand Vision</summary>
              <p className="text-xs text-fog">POST /api/vision/brand/predict</p>
              <input
                type="file"
                accept="image/*"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setBrandFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={() => handleBrand(brandFile || imageFile)}
                  disabled={busy === "brand"}
                >
                  {busy === "brand" ? "Running..." : "Analyze Logo"}
                </button>
                {imageFile && (
                  <span className="text-xs text-fog">Using attached image if no file chosen.</span>
                )}
              </div>
              {brandResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {brandResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Vision Classifier</summary>
              <p className="text-xs text-fog">POST /api/vision/predict</p>
              <input
                type="file"
                accept="image/*"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setVisionFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={() => handleVision(visionFile || imageFile)}
                  disabled={busy === "vision"}
                >
                  {busy === "vision" ? "Running..." : "Analyze Image"}
                </button>
                {imageFile && (
                  <span className="text-xs text-fog">Using attached image if no file chosen.</span>
                )}
              </div>
              {visionResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {visionResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Video Analysis</summary>
              <p className="text-xs text-fog">POST /api/vision/video/predict</p>
              <input
                type="file"
                accept="video/*"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setVideoFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 grid gap-3 text-xs text-fog">
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Frames Per Second
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={videoFps}
                    onChange={(event) => setVideoFps(Number(event.target.value))}
                    className="mt-2 w-full rounded-xl border border-line p-2 text-sm"
                  />
                </label>
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-fog">
                  Max Frames
                  <input
                    type="number"
                    min={8}
                    max={64}
                    value={videoMaxFrames}
                    onChange={(event) => setVideoMaxFrames(Number(event.target.value))}
                    className="mt-2 w-full rounded-xl border border-line p-2 text-sm"
                  />
                </label>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={() => handleVideo(videoFile)}
                  disabled={busy === "video"}
                >
                  {busy === "video" ? "Running..." : "Analyze Video"}
                </button>
              </div>
              {videoResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {videoResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Voice Emotion</summary>
              <p className="text-xs text-fog">POST /api/voice/emotion</p>
              <input
                type="file"
                accept="audio/*"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setVoiceFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-ember px-3 py-1 text-xs text-white"
                  onClick={() => handleVoice(voiceFile || audioFile)}
                  disabled={busy === "voice"}
                >
                  {busy === "voice" ? "Running..." : "Analyze Audio"}
                </button>
                {audioFile && (
                  <span className="text-xs text-fog">Using attached audio if no file chosen.</span>
                )}
              </div>
              {voiceResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {voiceResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Multimodal Recommendations</summary>
              <p className="text-xs text-fog">POST /api/recommend/multimodal</p>
              <input
                value={recommendText}
                onChange={(event) => setRecommendText(event.target.value)}
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
                placeholder="Describe what you want (e.g., streetwear sneakers)"
              />
              <input
                type="file"
                accept="image/*"
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setRecommendFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleRecommend}
                  disabled={busy === "recommend"}
                >
                  {busy === "recommend" ? "Running..." : "Get Recommendations"}
                </button>
                {imageFile && (
                  <span className="text-xs text-fog">Uses chat attachment if no file chosen.</span>
                )}
              </div>
              {recommendResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {recommendResult}
                </pre>
              )}
            </details>

            <details className="rounded-2xl border border-line bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-ink">Knowledge Base (RAG)</summary>
              <p className="text-xs text-fog">POST /api/rag/query + /api/rag/upload</p>
              <input
                value={ragQueryText}
                onChange={(event) => setRagQueryText(event.target.value)}
                className="mt-3 w-full rounded-xl border border-line p-3 text-sm"
                placeholder="Ask a question about your docs"
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full bg-moss px-3 py-1 text-xs text-white"
                  onClick={handleRagQuery}
                  disabled={busy === "ragQuery"}
                >
                  {busy === "ragQuery" ? "Running..." : "Query Docs"}
                </button>
              </div>
              <input
                type="file"
                accept=".md,.txt"
                className="mt-4 w-full rounded-xl border border-line p-3 text-sm"
                onChange={(event) => setRagUploadFile(event.target.files?.[0] || null)}
              />
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-full border border-line px-3 py-1 text-xs text-fog"
                  onClick={handleRagUpload}
                  disabled={busy === "ragUpload"}
                >
                  {busy === "ragUpload" ? "Uploading..." : "Upload Doc"}
                </button>
              </div>
              {ragResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {ragResult}
                </pre>
              )}
              {ragUploadResult && (
                <pre className="mt-4 max-h-40 overflow-auto rounded-xl bg-slate-900 p-4 text-xs text-slate-100">
                  {ragUploadResult}
                </pre>
              )}
            </details>
          </div>
        </section>

        {chatData?.meta?.items && chatData.meta.items.length > 0 && (
          <div className="card-panel px-6 py-6">
            <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-fog">
              Recommendation Highlights
            </h3>
            <ul className="mt-4 space-y-3 text-sm text-ink">
              {chatData.meta.items.slice(0, 5).map((item, index) => {
                const title = item.title || item.name || "Item";
                const reason = item.reason || item.overview || "";
                const metaLine = formatItemMeta(item);
                return (
                  <li key={`${title}-${index}`} className="rounded-xl border border-line p-3">
                    <p className="font-semibold">{title}</p>
                    {metaLine && <p className="mt-1 text-xs text-fog">{metaLine}</p>}
                    {reason && <p className="mt-2 text-xs text-fog">{reason}</p>}
                    {item.url && (
                      <a
                        href={item.url}
                        className="mt-2 inline-block text-xs font-semibold text-moss"
                        target="_blank"
                        rel="noreferrer"
                      >
                        View source
                      </a>
                    )}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {chatData && (
          <div className="card-panel px-6 py-6">
            <details className="text-xs text-fog">
              <summary className="cursor-pointer font-semibold">Response inspector</summary>
              <pre className="mt-3 max-h-40 overflow-auto text-[11px] text-slate-700">
                {JSON.stringify(chatData, null, 2)}
              </pre>
            </details>
          </div>
        )}
      </div>
    </main>
  );
}
