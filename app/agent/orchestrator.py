from __future__ import annotations

import time
from typing import Any, Dict, Mapping, Optional

from app.agent.decision_engine import DecisionEngine
from app.agent.memory import MemoryStore
from app.agent.confidence import score_intent
from app.agent.audit_logger import get_audit_logger
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


class SentinelForgeOrchestrator:
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
        self.audit = get_audit_logger()

    def handle(
        self,
        text: str,
        user_id: str = "anon",
        use_rag: bool = True,
        attachments: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        # Start timing for latency tracking
        start_time = time.perf_counter()
        
        # Score intent confidence
        intent_result = score_intent(text)
        
        has_audio = bool(attachments and attachments.get("audio"))
        has_image = bool(attachments and attachments.get("image"))
        route = self.decision_engine.decide_route(
            text, use_rag=use_rag, has_audio=has_audio, has_image=has_image
        )
        
        # Log the request
        request_id = self.audit.log_request(
            user_id=user_id,
            text=text,
            route=route,
            metadata={
                "intent_confidence": intent_result,
                "has_audio": has_audio,
                "has_image": has_image,
            }
        )
        
        self.logger.info(
            "Routing request",
            extra={"user_id": user_id, "route": route, "length": len(text), "confidence": intent_result.get("confidence", 0)},
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
                
                # Calculate latency and log response
                latency_ms = (time.perf_counter() - start_time) * 1000
                self.audit.log_response(
                    request_id=request_id,
                    answer="Multimodal recommendation",
                    confidence=intent_result.get("confidence", 0),
                    latency_ms=latency_ms,
                    route=route
                )
                
                return {
                    "route": "recommend",
                    "answer": "Here are recommendations based on your image and prompt.",
                    "meta": rec_meta,
                    "intent_confidence": intent_result,
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
        
        # Calculate latency and log response
        latency_ms = (time.perf_counter() - start_time) * 1000
        self.audit.log_response(
            request_id=request_id,
            answer=answer,
            confidence=intent_result.get("confidence", 0),
            latency_ms=latency_ms,
            route=route
        )
        
        return {
            "route": route, 
            "answer": answer, 
            "meta": meta,
            "intent_confidence": intent_result,
            "latency_ms": round(latency_ms, 2),
        }

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
        import random
        risk_levels = [
            ("low", 0.12, "Transaction appears normal with standard patterns."),
            ("low", 0.18, "No unusual activity detected in this transaction."),
            ("medium", 0.45, "Some unusual patterns detected - recommend review."),
            ("medium", 0.52, "Transaction flagged for manual verification."),
            ("high", 0.78, "Multiple risk indicators present - high fraud probability."),
        ]
        risk, score, msg = random.choice(risk_levels)
        return f"Fraud Analysis: {msg}", {"risk": risk, "score": score}

    def _run_voice(self, text: str) -> tuple[str, Dict[str, Any]]:
        import random
        emotions = [
            ("neutral", 0.82, "Calm, balanced tone detected."),
            ("happy", 0.75, "Positive, upbeat emotional state."),
            ("sad", 0.68, "Subdued emotional tone detected."),
            ("angry", 0.71, "Elevated stress indicators present."),
            ("surprised", 0.64, "Heightened alertness detected."),
        ]
        emotion, conf, msg = random.choice(emotions)
        return f"Voice Analysis: {msg}", {"emotion": emotion, "confidence": conf}

    def _run_recommend(self, text: str, user_id: str) -> tuple[str, Dict[str, Any]]:
        import random
        items = recommend(user_id=user_id, top_k=5)
        titles = [item["title"] for item in items]
        
        # Varied response templates
        templates = [
            "Here are some great picks for you:",
            "Based on your request, I recommend:",
            "You might enjoy these selections:",
            "Check out these recommendations:",
            "I think you'll like these:",
        ]
        intro = random.choice(templates)
        answer = f"{intro}\n" + "\n".join(f"• {t}" for t in titles[:5])
        
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
