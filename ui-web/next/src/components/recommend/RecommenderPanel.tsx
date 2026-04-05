"use client";

import { useState } from "react";
import { useRecommendations } from "@/lib/hooks/useRecommendations";

export function RecommenderPanel() {
  const [prompt, setPrompt] = useState("");
  const { movieResults, clothesResults, error, loading, getMovies, getClothes } = useRecommendations();

  return (
    <section className="card panel-grid">
      <div className="sf-panel-heading">Recommendation Studio</div>
      <input
        className="input"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Try: recommend sci-fi movies, or summer streetwear outfits"
      />
      <div className="flex flex-wrap gap-3">
        <button className="pill-btn" type="button" onClick={() => getMovies(prompt)}>
          {loading ? "Running..." : "Movie Recommender"}
        </button>
        <button className="pill-btn" type="button" onClick={() => getClothes(prompt)}>
          {loading ? "Running..." : "Clothes Recommender"}
        </button>
      </div>
      {error && <div className="muted">Error: {error}</div>}
      <div className="sf-two-col">
        <article className="card">
          <div className="card-title">Movies</div>
          <pre className="sf-pretty-pre mt-3">{JSON.stringify(movieResults ?? { status: "idle" }, null, 2)}</pre>
        </article>
        <article className="card">
          <div className="card-title">Clothes</div>
          <pre className="sf-pretty-pre mt-3">{JSON.stringify(clothesResults ?? { status: "idle" }, null, 2)}</pre>
        </article>
      </div>
    </section>
  );
}
