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

export const brandPredict = (payload: FormData, kind?: string, conf?: number) =>
  api.post("/api/vision/brand/predict", payload, {
    headers: { "Content-Type": "multipart/form-data" },
    params: {
      ...(kind ? { kind } : {}),
      ...(typeof conf === "number" ? { conf } : {}),
    },
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

export const faceEmotionPredict = (payload: FormData) =>
  api.post("/api/vision/face_emotion/predict", payload, {
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

export const ragQuery = (payload: { query: string; top_k?: number; return_chunks?: boolean }) =>
  api.post("/api/rag/query", payload);

export const ragIndex = (rebuild = false) =>
  api.post(`/api/rag/index?rebuild=${rebuild ? "true" : "false"}`);

export const ragStatus = () => api.get("/api/rag/status");

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

export const agentEscalate = (payload: {
  message: string;
  route?: string;
  severity?: string;
  evidence?: Record<string, unknown>;
  user_id?: string;
}) => api.post("/api/agent/escalate", payload);

export const healthDetailed = () => api.get("/health/detailed");

export const cyberTimeline = (params?: {
  window?: number;
  limit?: number;
  severity?: string;
  event_type?: string;
}) => api.get("/api/cyber/timeline", { params });

export const cyberTimelineEvents = (params?: { limit?: number; severity?: string }) =>
  api.get("/api/cyber/timeline/events", { params });

export const cyberTimelineSummary = () => api.get("/api/cyber/timeline/summary");

export const fraudExplain = (payload: { features: number[]; amount?: number }) =>
  api.post("/api/fraud/explain", payload);

export const adminModelRegistry = () => api.get("/api/v1/admin/model-registry");

export const featureFlags = () => api.get("/api/v1/admin/feature-flags");

export const updateFeatureFlags = (flags: Record<string, boolean>) =>
  api.put("/api/v1/admin/feature-flags", { flags });

export const auditLogs = (params?: { limit?: number; action?: string }) =>
  api.get("/api/v1/admin/audit-logs", { params });

export const userSettings = () => api.get("/api/v1/users/me/settings");

export const updateUserSettings = (payload: {
  theme: string;
  default_model: string;
  agent_token_cap: number;
}) => api.put("/api/v1/users/me/settings", payload);

export const logout = () => api.post("/api/v1/auth/logout");

export const passwordResetRequest = (payload: { username?: string; email?: string }) =>
  api.post("/api/v1/auth/password-reset/request", payload);

export const passwordResetConfirm = (payload: { token: string; new_password: string }) =>
  api.post("/api/v1/auth/password-reset/confirm", payload);

export const totpEnroll = () => api.post("/api/v1/auth/totp/enroll");

export const totpVerify = (payload: { code: string }) =>
  api.post("/api/v1/auth/totp/verify", payload);
