"use client";

import { useState } from "react";
import { useMutation } from "@apollo/client";
import { MISSION_CHAT, QUERY_RAG, RECOMMEND_CLOTHES, RECOMMEND_MOVIES } from "@/lib/gateway-graphql";

export function useMissionChat() {
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null);
  const [lastError, setLastError] = useState<string>("");

  const [missionChat, missionState] = useMutation(MISSION_CHAT);
  const [queryRag] = useMutation(QUERY_RAG);
  const [recommendMovies] = useMutation(RECOMMEND_MOVIES);
  const [recommendClothes] = useMutation(RECOMMEND_CLOTHES);

  const ask = async (query: string, mode: "chat" | "rag" | "movies" | "clothes") => {
    if (!query.trim()) return;
    setLastError("");
    try {
      let response: Record<string, unknown> | null = null;

      if (mode === "rag") {
        const out = await queryRag({ variables: { query, topK: 6, returnChunks: false } });
        response = out.data?.queryRag ?? null;
      } else if (mode === "movies") {
        const out = await recommendMovies({ variables: { prompt: query, topK: 5 } });
        response = out.data?.recommendMovies ?? null;
      } else if (mode === "clothes") {
        const out = await recommendClothes({ variables: { prompt: query, topK: 5 } });
        response = out.data?.recommendClothes ?? null;
      } else {
        const out = await missionChat({ variables: { prompt: query, useRag: true } });
        response = out.data?.missionChat ?? null;
      }

      setLastResult(response);
    } catch (error: unknown) {
      setLastError(error instanceof Error ? error.message : String(error));
    }
  };

  return {
    ask,
    lastResult,
    lastError,
    loading: missionState.loading,
  };
}
