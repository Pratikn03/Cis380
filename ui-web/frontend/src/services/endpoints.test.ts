import { api } from "./api";
import {
  adminModelRegistry,
  agentEscalate,
  auditLogs,
  behaviorLogs,
  behaviorScore,
  brandPredict,
  chat,
  cyberScore,
  cyberTimeline,
  cyberTimelineEvents,
  cyberTimelineSummary,
  dsaRagAsk,
  dsaRagIngest,
  dsaRagUpload,
  faceEmotionPredict,
  featureFlags,
  fraudScore,
  fraudExplain,
  healthDetailed,
  logout,
  multimodalChat,
  passwordResetConfirm,
  passwordResetRequest,
  ragIndex,
  ragAsk,
  ragQuery,
  ragStatus,
  ragUpload,
  recommendClothes,
  recommendMultimodal,
  riskAnalyze,
  totpEnroll,
  totpVerify,
  updateFeatureFlags,
  updateUserSettings,
  userSettings,
  visionPredict,
  visionVideoPredict,
  voiceEmotion,
} from "./endpoints";

describe("compatibility endpoint wrappers", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("calls chat endpoint", async () => {
    const spy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);
    await chat({ message: "hello" });
    expect(spy).toHaveBeenCalledWith("/api/chat", { message: "hello" });
  });

  it("calls risk endpoint", async () => {
    const payload = {
      login_country: "US",
      device_known: true,
      login_time: 11,
      clicks_per_minute: 4,
      files_accessed: 1,
      transaction_amount: 9,
    };
    const spy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);
    await riskAnalyze(payload);
    expect(spy).toHaveBeenCalledWith("/api/risk/analyze", payload);
  });

  it("calls score endpoints", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);
    await fraudScore({ features: [1, 2, 3] });
    await fraudExplain({ features: [1, 2, 3], amount: 99 });
    await cyberScore({ features: [4, 5, 6] });
    await behaviorScore({ features: [7, 8, 9] });
    expect(postSpy).toHaveBeenCalledWith("/api/fraud", { features: [1, 2, 3] });
    expect(postSpy).toHaveBeenCalledWith("/api/fraud/explain", {
      features: [1, 2, 3],
      amount: 99,
    });
    expect(postSpy).toHaveBeenCalledWith("/api/cyber", { features: [4, 5, 6] });
    expect(postSpy).toHaveBeenCalledWith("/api/behavior", { features: [7, 8, 9] });
  });

  it("calls health and timeline endpoints", async () => {
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: {} } as never);

    await healthDetailed();
    await cyberTimeline({ window: 24, limit: 10, severity: "high", event_type: "login" });
    await cyberTimelineEvents({ limit: 5, severity: "critical" });
    await cyberTimelineSummary();

    expect(getSpy).toHaveBeenCalledWith("/health/detailed");
    expect(getSpy).toHaveBeenCalledWith("/api/cyber/timeline", {
      params: { window: 24, limit: 10, severity: "high", event_type: "login" },
    });
    expect(getSpy).toHaveBeenCalledWith("/api/cyber/timeline/events", {
      params: { limit: 5, severity: "critical" },
    });
    expect(getSpy).toHaveBeenCalledWith("/api/cyber/timeline/summary");
  });

  it("calls rag endpoints", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: {} } as never);

    await ragAsk({ query: "what is dijkstra" });
    await ragStatus();

    expect(postSpy).toHaveBeenCalledWith("/api/rag/ask", { query: "what is dijkstra" });
    expect(getSpy).toHaveBeenCalledWith("/api/rag/status");
  });

  it("calls multipart wrappers with expected headers and params", async () => {
    const payload = new FormData();
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);

    await multimodalChat(payload);
    await brandPredict(payload, "movie");
    await voiceEmotion(payload);
    await behaviorLogs(payload);
    await visionPredict(payload);
    await faceEmotionPredict(payload);
    await recommendMultimodal(payload);
    await recommendClothes(payload);
    await ragUpload(payload);
    await dsaRagUpload(payload);
    await visionVideoPredict(payload);

    expect(postSpy).toHaveBeenCalledWith(
      "/api/chat/multimodal",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/vision/brand/predict",
      payload,
      expect.objectContaining({
        headers: { "Content-Type": "multipart/form-data" },
        params: { kind: "movie" },
      }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/voice/emotion",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/behavior/logs",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/vision/predict",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/vision/face_emotion/predict",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/recommend/multimodal",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/recommend/clothes",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/rag/upload",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/dsa-rag/upload",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
    expect(postSpy).toHaveBeenCalledWith(
      "/api/vision/video/predict",
      payload,
      expect.objectContaining({ headers: { "Content-Type": "multipart/form-data" } }),
    );
  });

  it("calls index/query and DSA wrappers", async () => {
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);

    await ragQuery({ query: "x", top_k: 2, return_chunks: true });
    await ragIndex(true);
    await dsaRagAsk({ query: "graph" });
    await dsaRagIngest({ filename: "doc.md", content: "hello" });

    expect(postSpy).toHaveBeenCalledWith("/api/rag/query", {
      query: "x",
      top_k: 2,
      return_chunks: true,
    });
    expect(postSpy).toHaveBeenCalledWith("/api/rag/index?rebuild=true");
    expect(postSpy).toHaveBeenCalledWith("/api/dsa-rag/ask", { query: "graph" });
    expect(postSpy).toHaveBeenCalledWith("/api/dsa-rag/ingest", {
      filename: "doc.md",
      content: "hello",
    });
  });

  it("calls agent, admin, auth, and settings wrappers", async () => {
    const getSpy = vi.spyOn(api, "get").mockResolvedValue({ data: {} } as never);
    const postSpy = vi.spyOn(api, "post").mockResolvedValue({ data: {} } as never);
    const putSpy = vi.spyOn(api, "put").mockResolvedValue({ data: {} } as never);

    await agentEscalate({
      message: "high risk upload",
      route: "agent",
      severity: "high",
      evidence: { confidence: 0.92 },
      user_id: "analyst",
    });
    await adminModelRegistry();
    await featureFlags();
    await updateFeatureFlags({ agent_streaming: true });
    await auditLogs({ limit: 20, action: "feature_flags.updated" });
    await userSettings();
    await updateUserSettings({
      theme: "sand",
      default_model: "fusion",
      agent_token_cap: 2048,
    });
    await logout();
    await passwordResetRequest({ username: "analyst" });
    await passwordResetConfirm({ token: "reset-token", new_password: "NewPassword123!" });
    await totpEnroll();
    await totpVerify({ code: "123456" });

    expect(postSpy).toHaveBeenCalledWith("/api/agent/escalate", {
      message: "high risk upload",
      route: "agent",
      severity: "high",
      evidence: { confidence: 0.92 },
      user_id: "analyst",
    });
    expect(getSpy).toHaveBeenCalledWith("/api/v1/admin/model-registry");
    expect(getSpy).toHaveBeenCalledWith("/api/v1/admin/feature-flags");
    expect(putSpy).toHaveBeenCalledWith("/api/v1/admin/feature-flags", {
      flags: { agent_streaming: true },
    });
    expect(getSpy).toHaveBeenCalledWith("/api/v1/admin/audit-logs", {
      params: { limit: 20, action: "feature_flags.updated" },
    });
    expect(getSpy).toHaveBeenCalledWith("/api/v1/users/me/settings");
    expect(putSpy).toHaveBeenCalledWith("/api/v1/users/me/settings", {
      theme: "sand",
      default_model: "fusion",
      agent_token_cap: 2048,
    });
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/logout");
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/password-reset/request", {
      username: "analyst",
    });
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/password-reset/confirm", {
      token: "reset-token",
      new_password: "NewPassword123!",
    });
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/totp/enroll");
    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/totp/verify", { code: "123456" });
  });
});
