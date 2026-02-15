"use client";

import { useState } from "react";
import { useMutation } from "@apollo/client";
import {
  ANALYZE_VIDEO_EMOTION,
  ANALYZE_VOICE_EMOTION,
  DETECT_BRAND_LOGOS,
  DETECT_DEEPFAKE,
} from "@/lib/gateway-graphql";

export function useMediaAnalyze() {
  const [snapshot, setSnapshot] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");

  const [voiceMutation, voiceState] = useMutation(ANALYZE_VOICE_EMOTION);
  const [videoMutation, videoState] = useMutation(ANALYZE_VIDEO_EMOTION);
  const [deepfakeMutation, deepfakeState] = useMutation(DETECT_DEEPFAKE);
  const [brandMutation, brandState] = useMutation(DETECT_BRAND_LOGOS);

  const run = async (
    mode: "voice" | "video" | "deepfake" | "brand",
    input: { fileName?: string; mediaUrl?: string },
  ) => {
    setError("");
    try {
      let result: Record<string, unknown> | null = null;
      if (mode === "voice") {
        const out = await voiceMutation({ variables: { input } });
        result = out.data?.analyzeVoiceEmotion ?? null;
      } else if (mode === "video") {
        const out = await videoMutation({ variables: { input } });
        result = out.data?.analyzeVideoEmotion ?? null;
      } else if (mode === "deepfake") {
        const out = await deepfakeMutation({ variables: { input } });
        result = out.data?.detectDeepfake ?? null;
      } else {
        const out = await brandMutation({ variables: { input } });
        result = out.data?.detectBrandLogos ?? null;
      }
      setSnapshot((prev) => ({ ...prev, [mode]: result ?? { status: "empty" } }));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const loading = voiceState.loading || videoState.loading || deepfakeState.loading || brandState.loading;

  return { snapshot, error, run, loading };
}
