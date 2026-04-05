"use client";

import { useState } from "react";
import { useMutation } from "@apollo/client";
import { RECOMMEND_CLOTHES, RECOMMEND_MOVIES } from "@/lib/gateway-graphql";

export function useRecommendations() {
  const [movieResults, setMovieResults] = useState<Record<string, unknown> | null>(null);
  const [clothesResults, setClothesResults] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  const [movies, moviesState] = useMutation(RECOMMEND_MOVIES);
  const [clothes, clothesState] = useMutation(RECOMMEND_CLOTHES);

  const getMovies = async (prompt: string) => {
    setError("");
    try {
      const out = await movies({ variables: { prompt, topK: 5 } });
      setMovieResults(out.data?.recommendMovies ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const getClothes = async (prompt: string) => {
    setError("");
    try {
      const out = await clothes({ variables: { prompt, topK: 5 } });
      setClothesResults(out.data?.recommendClothes ?? null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return {
    movieResults,
    clothesResults,
    error,
    loading: moviesState.loading || clothesState.loading,
    getMovies,
    getClothes,
  };
}
