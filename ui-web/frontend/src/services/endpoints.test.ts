import { api } from "./api";
import {
  behaviorLogs,
  behaviorScore,
  brandPredict,
  chat,
  cyberScore,
  dsaRagAsk,
  dsaRagIngest,
  dsaRagUpload,
  faceEmotionPredict,
  fraudScore,
  multimodalChat,
  ragIndex,
  ragAsk,
  ragQuery,
  ragStatus,
  ragUpload,
  recommendClothes,
  recommendMultimodal,
  riskAnalyze,
  visionPredict,
  visionVideoPredict,
  voiceEmotion,
} from "./endpoints";

describe("legacy endpoint wrappers", () => {
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
    await cyberScore({ features: [4, 5, 6] });
    await behaviorScore({ features: [7, 8, 9] });
    expect(postSpy).toHaveBeenCalledWith("/api/fraud", { features: [1, 2, 3] });
    expect(postSpy).toHaveBeenCalledWith("/api/cyber", { features: [4, 5, 6] });
    expect(postSpy).toHaveBeenCalledWith("/api/behavior", { features: [7, 8, 9] });
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
});
