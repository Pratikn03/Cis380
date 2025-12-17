"""Central orchestrator for OmniChatX."""
from __future__ import annotations

import logging
import re
import os
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd

from agent.policy import decide
from rag.service import rag_service
from agent.utils.shap_explainer import explain as shap_explain

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
logger = logging.getLogger(__name__)


def _looks_like_numeric_vector(text: str) -> bool:
    """Return True if the input is basically a numeric vector (optionally prefixed with 'recommend'/'suggest')."""
    stripped = (text or "").strip()
    if not stripped:
        return False
    # Remove common command words, then check if the remainder is a numeric-looking blob.
    stripped = re.sub(r"\b(recommend|suggest|predict|score)\b", " ", stripped, flags=re.IGNORECASE).strip()
    if not stripped:
        return False
    if not re.search(r"\d", stripped):
        return False
    return bool(re.fullmatch(r"[\s,;|()eE+\-.\d]+", stripped))


def _extract_multimodal_context(message: str) -> list[str]:
    """Extract streamlit-attached context lines like [voice]/[vision] so offline mode can respond usefully."""
    text = message or ""
    lines: list[str] = []

    m_voice = re.search(
        r"\[voice\]\s*emotion\s*=\s*([^\s]+)\s+confidence\s*=\s*([0-9.]+)",
        text,
        re.IGNORECASE,
    )
    if m_voice:
        lines.append(f"Voice emotion: {m_voice.group(1)} (confidence {m_voice.group(2)})")

    m_vis = re.search(
        r"\[vision\]\s*label\s*=\s*([^\s]+)\s+confidence\s*=\s*([0-9.]+)",
        text,
        re.IGNORECASE,
    )
    if m_vis:
        lines.append(f"Vision label: {m_vis.group(1)} (confidence {m_vis.group(2)})")

    return lines


def _offline_assistant(message: str) -> str:
    """Best-effort offline reply (no OpenAI key)."""
    m = (message or "").strip()
    if not m:
        return "Say something and I’ll help."

    lower = m.lower()

    # Provide actionable guidance for common project questions.
    if any(k in lower for k in ("next step", "next steps", "what are we doing", "what to do", "train", "training", "demo")):
        return (
            "Offline mode is enabled (no OPENAI_API_KEY).\n\n"
            "Next steps:\n"
            "1) Train everything: `python scripts/train_all.py --with-vision --voice-limit-per-class 0`\n"
            "2) Run the demo: `bash scripts/run_demo.sh`\n"
            "3) Verify end-to-end: `bash scripts/codex_test_all.sh`\n\n"
            "Tip: In Streamlit, use the **Voice & Vision** tab for uploads, and **OmniChatX Agent** for chat + attachments."
        )

    context_lines = _extract_multimodal_context(m)
    if context_lines:
        return "Offline multimodal summary:\n- " + "\n- ".join(context_lines)

    # Fall back to local docs (RAG).
    return rag_service.answer(m)


def _llm_call(message: str) -> str:
    """Call OpenAI if key set; otherwise use an offline helper response."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return _offline_assistant(message)
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": message}],
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"LLM call failed: {exc}"


def _extract_numbers(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.?\d+)", text)]


@dataclass
class ModelBundle:
    fraud: Optional[object]
    cyber: Optional[object]
    behavior_scaler: Optional[object]
    behavior_model: Optional[object]
    recommender: Optional[object]


def _load_models() -> ModelBundle:
    fraud = cyber = behavior_scaler = behavior_model = recommender = None

    fraud_path = Path("models/fraud/supervised/fraud_model.pkl")
    if fraud_path.exists():
        try:
            fraud = joblib.load(fraud_path)
        except Exception as exc:
            logger.warning("Failed to load fraud model (%s): %s", fraud_path, exc)

    cyber_path = Path("models/cyber/supervised/cyber_model.pkl")
    if cyber_path.exists():
        try:
            cyber = joblib.load(cyber_path)
        except Exception as exc:
            logger.warning("Failed to load cyber model (%s): %s", cyber_path, exc)

    beh_path = Path("models/behavior/behavior_lof.pkl")
    if beh_path.exists():
        try:
            beh = joblib.load(beh_path)
        except Exception as exc:
            logger.warning("Failed to load behavior model (%s): %s", beh_path, exc)
            beh = None
        # stored as dict with scaler + LOF
        if isinstance(beh, dict):
            behavior_scaler = beh.get("preprocessor")
            behavior_model = beh.get("model")

    rec_path = Path("models/recommender/recommender_model.pkl")
    if rec_path.exists():
        try:
            recommender = joblib.load(rec_path)
        except Exception as exc:
            logger.warning("Failed to load recommender model (%s): %s", rec_path, exc)

    return ModelBundle(
        fraud=fraud,
        cyber=cyber,
        behavior_scaler=behavior_scaler,
        behavior_model=behavior_model,
        recommender=recommender,
    )


class OmniChatXOrchestrator:
    """Simple rule-based router that hits RAG, fraud, cyber, behavior, or recommender."""

    def __init__(self):
        self.models = _load_models()
        # optional recommender meta for feature names
        rec_meta_path = Path("models/recommender/recommender_meta.joblib")
        if rec_meta_path.exists():
            try:
                self.rec_meta = joblib.load(rec_meta_path)
            except Exception as exc:
                logger.warning("Failed to load recommender meta (%s): %s", rec_meta_path, exc)
                self.rec_meta = {}
        else:
            self.rec_meta = {}

    # ---------------- Inference helpers ---------------- #
    def _fraud_score(self, message: str) -> str:
        model = self.models.fraud
        if model is None:
            return "Fraud model not available."
        cols = list(getattr(model, "feature_names_in_", []))
        if not cols:
            return "Fraud model missing feature names."

        nums = _extract_numbers(message)
        values = [0.0] * len(cols)
        for i, v in enumerate(nums[: len(values)]):
            values[i] = v
        df = pd.DataFrame([values], columns=cols)

        # If pipeline, use KernelExplainer; else try TreeExplainer
        force_kernel = hasattr(model, "predict_proba") and hasattr(model, "named_steps")
        if hasattr(model, "predict_proba"):
            score = float(model.predict_proba(df)[0][1])
        elif hasattr(model, "decision_function"):
            score = float(model.decision_function(df)[0])
        else:
            score = float(model.predict(df)[0])

        shap_res = shap_explain(model, df.values, cols, top_k=3, force_kernel=force_kernel)
        top_txt = "; ".join([f"{n}:{v:+.3f}" for n, v in shap_res.top_features]) if shap_res.top_features else shap_res.note
        return (
            f"Fraud probability: {score:.4f} (filled {len(nums)} numeric fields; rest set to 0). "
            f"Top features: {top_txt}"
        )

    def _cyber_score(self, message: str) -> str:
        model = self.models.cyber
        if model is None:
            return "Cyber model not available."
        n = getattr(model, "n_features_in_", 0)
        feat_names = list(getattr(model, "feature_names_in_", [f"f{i}" for i in range(n)]))
        nums = _extract_numbers(message)
        arr = np.zeros((1, n), dtype=float)
        for i, v in enumerate(nums[:n]):
            arr[0, i] = v
        if hasattr(model, "predict_proba"):
            score = float(model.predict_proba(arr)[0][1])
            shap_res = shap_explain(model, arr, feat_names, top_k=3, force_kernel=False)
            top_txt = "; ".join([f"{n}:{v:+.3f}" for n, v in shap_res.top_features]) if shap_res.top_features else shap_res.note
            return f"Cyber attack probability: {score:.4f} (filled {len(nums)} numeric fields; rest set to 0). Top: {top_txt}"
        pred = model.predict(arr)[0]
        return f"Cyber model prediction: {pred} (filled {len(nums)} numeric fields; rest set to 0)."

    def _behavior_score(self, message: str) -> str:
        scaler = self.models.behavior_scaler
        model = self.models.behavior_model
        if scaler is None or model is None:
            return "Behavior model not available."
        n = getattr(scaler, "n_features_in_", 0)
        nums = _extract_numbers(message)
        arr = np.zeros((1, n), dtype=float)
        for i, v in enumerate(nums[:n]):
            arr[0, i] = v
        arr_scaled = scaler.transform(arr)
        score = float(model.decision_function(arr_scaled)[0])
        return f"Behavior anomaly score (LOF): {score:.4f} (filled {len(nums)} numeric fields; rest set to 0)."

    def _recommend(self, message: str) -> str:
        model = self.models.recommender
        if model is None:
            return "Recommender model not available."
        n = getattr(model, "n_features_in_", 0)
        nums = _extract_numbers(message)
        arr = np.zeros((1, n), dtype=float)
        for i, v in enumerate(nums[:n]):
            arr[0, i] = v
        feat_names = list(self.rec_meta.get("feature_names", [])) or [f"f{i}" for i in range(n)]
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(arr)[0]
            classes = getattr(model, "classes_", [])
            top_idx = int(np.argmax(proba))
            top_label = classes[top_idx] if len(classes) > top_idx else "item"
            shap_res = shap_explain(model, arr, feat_names, top_k=3, force_kernel=False)
            top_txt = "; ".join([f"{n}:{v:+.3f}" for n, v in shap_res.top_features]) if shap_res.top_features else shap_res.note
            return f"Recommended action: {top_label} (p={proba[top_idx]:.3f}). Top features: {top_txt}"
        pred = model.predict(arr)[0]
        return f"Recommended action: {pred}."

    def _recommend_nl(self, message: str) -> str:
        """Natural-language recommendation helper for the agent chat (movies/electronics/places/news)."""
        try:
            from app.streamlit_chatbot.recommender_router import route_recommendation
        except Exception:
            route_recommendation = None

        if route_recommendation is None:
            return "Recommendation module not available (missing app/streamlit_chatbot)."

        rec = route_recommendation(message)
        category = str(rec.get("category") or "Recommendations")
        items = rec.get("items") or []
        if not items:
            return f"No {category} results right now."

        lines = [f"Here are some {category.lower()} picks:"]
        for i, it in enumerate(items[:5], 1):
            title = it.get("title") or it.get("name") or "Item"
            reason = it.get("reason") or it.get("overview") or ""
            url = it.get("url")
            bullet = f"{i}. {title}"
            details = []
            if reason:
                details.append(str(reason))
            if url:
                details.append(str(url))
            if details:
                bullet += " — " + " · ".join(details)
            lines.append(bullet)
        return "\n".join(lines)

    def _recommend_movie(self, user_id: int, movie_id: int) -> str:
        ml_path = Path("recommender/models/recommender.pkl")
        meta_path = Path("recommender/models/recommender_meta.joblib")
        if not (ml_path.exists() and meta_path.exists()):
            return self._recommend(f"{user_id} {movie_id}")  # fallback to numeric
        ml_model = joblib.load(ml_path)
        meta = joblib.load(meta_path)
        user_stats = meta.get("user_stats")
        item_stats = meta.get("item_stats")
        global_mean = meta.get("global_mean", 3.5)
        user_codes = meta.get("user_codes", {})
        item_codes = meta.get("item_codes", {})
        feat_names = meta.get("feature_names", [])

        u_mean = user_stats.loc[user_id]["user_mean"] if user_id in user_stats.index else global_mean
        u_count = user_stats.loc[user_id]["user_count"] if user_id in user_stats.index else 0.0
        i_mean = item_stats.loc[movie_id]["item_mean"] if movie_id in item_stats.index else global_mean
        i_count = item_stats.loc[movie_id]["item_count"] if movie_id in item_stats.index else 0.0
        u_code = user_codes.get(user_id, 0)
        i_code = item_codes.get(movie_id, 0)

        values = {
            "user_mean": u_mean,
            "item_mean": i_mean,
            "user_count": u_count,
            "item_count": i_count,
            "global_mean": global_mean,
            "user_code": u_code,
            "item_code": i_code,
        }
        feats = np.array([[values.get(k, 0.0) for k in feat_names]])
        proba = ml_model.predict_proba(feats)[0]
        classes = getattr(ml_model, "classes_", [])
        top_idx = int(np.argmax(proba))
        label = classes[top_idx] if len(classes) > top_idx else "like"
        return f"Movie recommendation: {label} (p={proba[top_idx]:.3f}) for user {user_id}, movie {movie_id}."

    # ---------------- Routing ---------------- #
    def route(self, message: str) -> str:
        intent = decide(message)

        if intent == "fraud":
            return self._fraud_score(message)
        if intent == "cyber":
            return self._cyber_score(message)
        if intent == "behavior":
            return self._behavior_score(message)
        if intent == "recommend":
            # 1) If the user provided a numeric vector (e.g., "0.1, 1.2, ..."), use the tabular model.
            if _looks_like_numeric_vector(message):
                return self._recommend(message)

            # 2) If the user explicitly provided "user/movie" IDs, keep that path.
            m = re.search(
                r"\buser(?:_id)?\s*[:=]?\s*(\d+)\b.*\bmovie(?:_id)?\s*[:=]?\s*(\d+)\b",
                (message or "").lower(),
            )
            if m:
                return self._recommend_movie(int(m.group(1)), int(m.group(2)))

            # 3) Otherwise, use the natural-language recommender handlers (offline-capable).
            return self._recommend_nl(message)
        if intent == "rag":
            return rag_service.answer(message)

        # default: LLM if key is set, else offline helper
        return _llm_call(message)
