import { api } from "./api";

export const chat = (payload: { message: string }) => api.post("/api/chat", payload);

export const multimodalChat = (payload: FormData) =>
  api.post("/api/chat/multimodal", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const riskAnalyze = (payload: {
  login_country: string;
  device_known: boolean;
  login_time: number;
  clicks_per_minute: number;
  files_accessed: number;
  transaction_amount: number;
}) => api.post("/api/risk/analyze", payload);

export const brandPredict = (payload: FormData, kind?: string) =>
  api.post("/api/vision/brand/predict", payload, {
    headers: { "Content-Type": "multipart/form-data" },
    params: kind ? { kind } : undefined,
  });

export const voiceEmotion = (payload: FormData) =>
  api.post("/api/voice/emotion", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const fraudScore = (payload: { features: number[] }) => api.post("/api/fraud", payload);

export const cyberScore = (payload: { features: number[] }) => api.post("/api/cyber", payload);

export const behaviorScore = (payload: { features: number[] }) =>
  api.post("/api/behavior", payload);

export const behaviorLogs = (payload: FormData) =>
  api.post("/api/behavior/logs", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const visionPredict = (payload: FormData) =>
  api.post("/api/vision/predict", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const recommendMultimodal = (payload: FormData) =>
  api.post("/api/recommend/multimodal", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const recommendClothes = (payload: FormData) =>
  api.post("/api/recommend/clothes", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const ragAsk = (payload: { query: string }) => api.post("/api/rag/ask", payload);

export const ragUpload = (payload: FormData) =>
  api.post("/api/rag/upload", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const dsaRagAsk = (payload: { query: string }) =>
  api.post("/api/dsa-rag/ask", payload);

export const dsaRagUpload = (payload: FormData) =>
  api.post("/api/dsa-rag/upload", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const dsaRagIngest = (payload: { filename?: string; content?: string }) =>
  api.post("/api/dsa-rag/ingest", payload);

export const visionVideoPredict = (payload: FormData) =>
  api.post("/api/vision/video/predict", payload, {
    headers: { "Content-Type": "multipart/form-data" },
  });
