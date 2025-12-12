"""Central orchestrator for OmniChatX."""
from __future__ import annotations

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


def _llm_call(message: str) -> str:
    """Call OpenAI if key set; otherwise instruct user to set it."""
    if not OPENAI_KEY:
        return "Set OPENAI_API_KEY to enable LLM replies."
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}"},
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
        fraud = joblib.load(fraud_path)

    cyber_path = Path("models/cyber/supervised/cyber_model.pkl")
    if cyber_path.exists():
        cyber = joblib.load(cyber_path)

    beh_path = Path("models/behavior/behavior_lof.pkl")
    if beh_path.exists():
        beh = joblib.load(beh_path)
        # stored as dict with scaler + LOF
        if isinstance(beh, dict):
            behavior_scaler = beh.get("preprocessor")
            behavior_model = beh.get("model")

    rec_path = Path("models/recommender/recommender_model.pkl")
    if rec_path.exists():
        recommender = joblib.load(rec_path)

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
        rag_service.build()
        # optional recommender meta for feature names
        rec_meta_path = Path("models/recommender/recommender_meta.joblib")
        self.rec_meta = joblib.load(rec_meta_path) if rec_meta_path.exists() else {}

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
            # try to parse two ints as user/movie
            nums = _extract_numbers(message)
            if len(nums) >= 2:
                res = self._recommend_movie(int(nums[0]), int(nums[1]))
                # include approximate explanation if present
                if isinstance(res, dict):
                    expl = res.get("explanation")
                    label = res.get("label")
                    prob = res.get("probability")
                    mode = res.get("mode")
                    return f"Recommend (mode={mode}): {label} (p={prob}). {expl or ''}"
                return res
            return self._recommend(message)
        if intent == "rag":
            return rag_service.answer(message)

        # default: LLM if key is set, else RAG fallback
        return _llm_call(message)
