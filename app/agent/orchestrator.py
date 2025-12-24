from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from app.agent.decision_engine import DecisionEngine
from app.agent.memory import MemoryStore
from app.models.recommender.explain import explain_recommendation
from app.models.recommender.predict import recommend
from app.models.recommender.multimodal.multimodal_predict import (
    IndexNotBuiltError,
    multimodal_recommend,
)
from app.models.voice.emotion_predict import predict_emotion
from app.rag.prompting import build_rag_prompt
from app.rag.retriever import retrieve_context
from app.utils.logger import get_logger
from app.utils.llm_stub import LLMStub


class OmniChatXOrchestrator:
    """Orchestrator routing requests to the appropriate AI module."""

    def __init__(
        self,
        llm_client: Optional[LLMStub] = None,
        memory_store: Optional[MemoryStore] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ) -> None:
        self.llm = llm_client or LLMStub()
        self.memory = memory_store or MemoryStore()
        self.decision_engine = decision_engine or DecisionEngine()
        self.logger = get_logger(self.__class__.__name__)

    def handle(
        self,
        text: str,
        user_id: str = "anon",
        use_rag: bool = True,
        attachments: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        has_audio = bool(attachments and attachments.get("audio"))
        has_image = bool(attachments and attachments.get("image"))
        route = self.decision_engine.decide_route(
            text, use_rag=use_rag, has_audio=has_audio, has_image=has_image
        )
        self.logger.info(
            "Routing request",
            extra={"user_id": user_id, "route": route, "length": len(text)},
        )
        emotion_data = None
        if has_audio:
            assert attachments is not None
            audio_content = attachments.get("audio")
            try:
                if isinstance(audio_content, (bytes, bytearray)):
                    emotion_data = predict_emotion(audio_bytes=bytes(audio_content))
            except Exception as exc:
                self.logger.warning("Emotion detection failed: %s", exc)
        if has_image and route == "recommend":
            try:
                assert attachments is not None
                image_content = attachments.get("image")
                image_bytes = (
                    image_content if isinstance(image_content, (bytes, bytearray)) else None
                )
                text_value = (text or "").strip()
                from app.vision_local.analyze import analyze_image_bytes

                rec_meta = multimodal_recommend(
                    image_bytes=image_bytes, text=text_value or None, top_k=5
                )
                try:
                    if image_bytes is not None:
                        rec_meta["visual"] = analyze_image_bytes(image_bytes)
                except Exception:
                    pass
                return {
                    "route": "recommend",
                    "answer": "Here are recommendations based on your image and prompt.",
                    "meta": rec_meta,
                }
            except IndexNotBuiltError as exc:
                return {
                    "route": "recommend",
                    "answer": "Multimodal recommender isn't ready yet.",
                    "meta": {"error": str(exc)},
                }

        answer, meta = self._invoke_route(route, text, emotion_data, user_id)
        self.memory.add_turn(user_id, text, answer)
        if emotion_data:
            meta["emotion"] = emotion_data
        return {"route": route, "answer": answer, "meta": meta}

    def _invoke_route(
        self, route: str, text: str, emotion: dict[str, Any] | None, user_id: str
    ) -> tuple[str, Dict[str, Any]]:
        if route == "rag":
            return self._run_rag(text, emotion)
        if route == "fraud":
            return self._run_fraud(text)
        if route == "voice_emotion":
            return self._run_voice(text)
        if route == "recommend":
            return self._run_recommend(text, user_id)
        return self._run_chat(text, emotion)

    def _run_rag(self, text: str, emotion: dict[str, Any] | None) -> tuple[str, Dict[str, Any]]:
        context = retrieve_context(text)
        prompt = build_rag_prompt(text, context)
        context_texts: list[str] = [str(chunk.get("text", "")) for chunk in context]
        if emotion:
            context_texts.append(f"Emotion: {emotion['emotion']} ({emotion['confidence']})")
        answer = self.llm.generate(prompt, context_texts)
        citations = [chunk.get("chunk_id") for chunk in context]
        meta = {
            "citations": citations,
            "chunks": [
                {
                    "source": chunk.get("source"),
                    "score": chunk.get("score"),
                    "chunk_id": chunk.get("chunk_id"),
                }
                for chunk in context
            ],
        }
        return answer, meta

    def _run_fraud(self, text: str) -> tuple[str, Dict[str, Any]]:
        return "Fraud stub: transaction looks benign.", {"risk": "low", "score": 0.12}

    def _run_voice(self, text: str) -> tuple[str, Dict[str, Any]]:
        return "Voice emotion stub: calm tone detected.", {"emotion": "neutral", "confidence": 0.82}

    def _run_recommend(self, text: str, user_id: str) -> tuple[str, Dict[str, Any]]:
        items = recommend(user_id=user_id, top_k=5)
        titles = [item["title"] for item in items]
        answer = self.llm.generate(f"Recommend: {text}", context=titles if titles else None)
        explanations = [
            {"item_id": item["item_id"], "text": explain_recommendation(user_id, item["item_id"])}
            for item in items
        ]
        return answer, {"items": items, "explanations": explanations}

    def _run_chat(self, text: str, emotion: dict[str, Any] | None) -> tuple[str, Dict[str, Any]]:
        prompt = text
        if emotion:
            prompt = f"Emotion detected: {emotion['emotion']} ({emotion['confidence']}).\n" + prompt
        answer = self.llm.generate(prompt)
        meta = {"source": "chat_fallback"}
        return answer, meta
