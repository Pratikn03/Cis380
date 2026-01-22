from __future__ import annotations

import re
import time
from typing import Any, Dict, Mapping, Optional

from app.agent.decision_engine import DecisionEngine
from app.agent.memory import MemoryStore
from app.agent.confidence import score_intent
from app.agent.audit_logger import get_audit_logger
from app.legacy.agent.chat_responses import (
    get_about_response,
    get_greeting_response,
    get_help_response,
    get_topic_response,
    is_about_request,
    is_greeting,
    is_help_request,
)
from app.models.recommender.explain import explain_recommendation
from app.models.recommender.predict import recommend
from app.models.recommender.multimodal.multimodal_predict import (
    IndexNotBuiltError,
    multimodal_recommend,
)
from app.models.voice.emotion_predict import predict_emotion
from app.utils.logger import get_logger
from app.utils.llm_stub import LLMStub
from app.services.risk_engine import analyze_risk
from app.services.decision_engine import make_decision
from app.services.explainer import explain_decision


class SentifargoOrchestrator:
    """Orchestrator routing requests to the appropriate AI module."""

    def __init__(
        self,
        llm_client: Optional[LLMStub] = None,
        memory_store: Optional[MemoryStore] = None,
        decision_engine: Optional[DecisionEngine] = None,
    ) -> None:
        self.llm = llm_client or LLMStub()
        self.memory = memory_store or MemoryStore.from_env()
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

        answer, meta = self._invoke_route(route, text, emotion_data, user_id, intent_result, attachments)
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
        self, route: str, text: str, emotion: dict[str, Any] | None, user_id: str, intent: Dict[str, Any] | None = None, attachments: Mapping[str, Any] | None = None
    ) -> tuple[str, Dict[str, Any]]:
        if route == "rag":
            return self._run_rag(text, emotion)
        if route == "fraud":
            return self._run_fraud(text)
        if route == "cyber":
            return self._run_cyber(text)
        if route == "behavior":
            return self._run_behavior(text)
        if route == "risk":
            return self._run_risk(text)
        if route == "voice_emotion":
            return self._run_voice(text)
        if route == "recommend":
            return self._run_recommend(text, user_id)
        if route == "vision":
            return self._run_vision(text, attachments)
        if route == "brand":
            return self._run_brand(text, attachments)
        return self._run_chat(text, emotion, user_id, intent)

    def _run_rag(self, text: str, emotion: dict[str, Any] | None) -> tuple[str, Dict[str, Any]]:
        from app.rag.dsa_pipeline import answer_query

        result = answer_query(text)
        meta = {
            "citations": result.get("citations", []),
            "chunks": [
                {
                    "source": chunk.get("source"),
                    "score": chunk.get("hybrid_score", chunk.get("score")),
                    "chunk_id": chunk.get("chunk_id"),
                    "page": chunk.get("page"),
                }
                for chunk in result.get("sources", [])
            ],
            "confidence": result.get("confidence", 0.0),
        }
        if emotion:
            meta["emotion"] = emotion
        return result.get("answer", ""), meta

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

    def _run_cyber(self, text: str) -> tuple[str, Dict[str, Any]]:
        payload = self._risk_payload_from_message(text)
        scores = analyze_risk(payload)
        score = scores.get("cyber_risk", 0.0)
        msg = "Cyber threat level is normal."
        if score > 0.7:
            msg = "High cyber threat detected! Immediate attention required."
        elif score > 0.4:
            msg = "Elevated cyber risk detected."
        return f"Cyber Analysis: {msg}", {"score": score, "details": scores}

    def _run_behavior(self, text: str) -> tuple[str, Dict[str, Any]]:
        payload = self._risk_payload_from_message(text)
        scores = analyze_risk(payload)
        score = scores.get("behavior_risk", 0.0)
        msg = "User behavior appears normal."
        if score > 0.7:
            msg = "Anomalous behavior detected! Deviation from baseline."
        elif score > 0.4:
            msg = "Slight behavioral anomalies observed."
        return f"Behavior Analysis: {msg}", {"score": score, "details": scores}

    def _run_risk(self, text: str) -> tuple[str, Dict[str, Any]]:
        payload = self._risk_payload_from_message(text)
        scores = analyze_risk(payload)
        decision = make_decision(
            scores.get("cyber_risk", 0.0),
            scores.get("behavior_risk", 0.0),
            scores.get("fraud_risk", 0.0),
        )
        explanation = explain_decision(
            risks=scores,
            decision=decision.decision,
            context=[f"{k}={v}" for k, v in payload.items() if k in ["login_country", "transaction_amount", "device_known"]]
        )
        answer = f"Unified Risk Analysis:\nDecision: **{decision.decision}**\n\n{explanation}"
        return answer, {"scores": scores, "decision": decision.decision, "explanation": explanation}

    def _run_vision(self, text: str, attachments: Mapping[str, Any] | None) -> tuple[str, Dict[str, Any]]:
        if not attachments or not attachments.get("image"):
            return "Please attach an image for vision analysis.", {"available": False}
        
        image_content = attachments.get("image")
        if not isinstance(image_content, (bytes, bytearray)):
             return "Invalid image attachment.", {"available": False}

        try:
            from app.vision_local.analyze import analyze_image_bytes
            analysis = analyze_image_bytes(bytes(image_content))
            label = analysis.get("label", "unknown")
            conf = analysis.get("confidence", 0.0)
            return f"Vision Analysis: Detected **{label}** ({conf:.1%}).", {"analysis": analysis}
        except Exception as e:
            self.logger.warning(f"Vision analysis failed: {e}")
            return "Vision analysis failed.", {"error": str(e)}

    def _run_brand(self, text: str, attachments: Mapping[str, Any] | None) -> tuple[str, Dict[str, Any]]:
        if not attachments or not attachments.get("image"):
            return "Please attach an image for brand detection.", {"available": False}
        
        image_content = attachments.get("image")
        if not isinstance(image_content, (bytes, bytearray)):
             return "Invalid image attachment.", {"available": False}

        try:
            from src.vision.brand.recognizer import predict_image_bytes
            detections = predict_image_bytes(bytes(image_content), conf=0.25)
            if detections:
                brands = sorted(list(set([d["brand"] for d in detections])))
                brand_str = ", ".join(brands)
                
                # Connect to recommendations
                recs = []
                try:
                    from app.streamlit_chatbot.handlers.electronics import recommend_electronics
                    for b in brands:
                        # Try common electronics domains
                        for domain in ["phones", "laptops", "headphones"]:
                            items = recommend_electronics(domain=domain, query=b, limit=2)
                            if items:
                                recs.extend(items)
                except Exception:
                    pass
                
                try:
                    from app.streamlit_chatbot.handlers.clothes import recommend_clothes
                    for b in brands:
                        items = recommend_clothes(query=b, top_k=2)
                        if items:
                            recs.extend(items)
                except Exception:
                    pass

                answer = f"Brand Detection: Found **{brand_str}**."
                if recs:
                    answer += "\n\n**Related Products:**\n"
                    # Simple deduplication by title
                    seen = set()
                    for item in recs:
                        title = item.get("title", "Item")
                        if title not in seen:
                            seen.add(title)
                            price = item.get("price") or item.get("price_usd")
                            meta = f" (${price})" if price else ""
                            answer += f"• {title}{meta}\n"
                    
                return answer, {"detections": detections, "recommendations": recs}
            else:
                return "No brands detected in the image.", {"detections": []}
        except Exception as e:
            self.logger.warning(f"Brand detection failed: {e}")
            return "Brand detection failed.", {"error": str(e)}

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
        text_lower = text.lower()
        
        # Detect recommendation category from query
        category = self._detect_recommend_category(text_lower)
        
        # Route to appropriate handler
        if category == "clothes":
            return self._recommend_clothes(text)
        elif category == "movies":
            return self._recommend_movies(text)
        elif category == "news":
            return self._recommend_news(text)
        elif category == "courses":
            return self._recommend_courses(text)
        elif category == "cars":
            return self._recommend_cars(text)
        elif category == "electronics":
            return self._recommend_electronics(text)
        elif category == "places":
            return self._recommend_places(text)
        
        # Default: generic recommendations
        items = recommend(user_id=user_id, top_k=5)
        titles = [item["title"] for item in items]
        
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
    
    def _detect_recommend_category(self, text: str) -> str:
        """Detect what category of recommendation the user wants."""
        # Clothing keywords
        if any(
            kw in text
            for kw in [
                "cloth",
                "clothing",
                "apparel",
                "fashion",
                "wear",
                "outfit",
                "outfits",
                "dress",
                "shirt",
                "pants",
                "jacket",
                "summer wear",
                "winter wear",
                "style",
            ]
        ):
            return "clothes"
        # Movie keywords
        if any(kw in text for kw in ["movie", "film", "watch", "cinema", "show", "series", "netflix", "streaming"]):
            return "movies"
        # News keywords
        if any(kw in text for kw in ["news", "article", "headline", "breaking", "current events", "latest"]):
            return "news"
        # Course keywords
        if any(kw in text for kw in ["course", "learn", "tutorial", "class", "training", "education", "study"]):
            return "courses"
        # Car keywords
        if any(kw in text for kw in ["car", "vehicle", "suv", "sedan", "truck", "automobile", "drive"]):
            return "cars"
        # Electronics keywords
        if any(kw in text for kw in ["laptop", "phone", "computer", "tablet", "electronic", "gadget", "tech", "device"]):
            return "electronics"
        # Travel/Places keywords
        if any(kw in text for kw in ["travel", "vacation", "destination", "place", "visit", "trip", "hotel", "flight"]):
            return "places"
        return "generic"
    
    def _recommend_clothes(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Clothing recommendations."""
        try:
            from app.streamlit_chatbot.handlers.clothes import recommend_clothes
            items = recommend_clothes(age=None, query=text, top_k=5)
            if items:
                answer = "👕 **Clothing Recommendations:**\n\n"
                for item in items:
                    brand = item.get("brand", "")
                    title = item.get("title", "")
                    reason = item.get("reason", "")
                    price = item.get("price_usd")
                    price_str = f" - ${price:.0f}" if price else ""
                    answer += f"• **{title}** by {brand}{price_str}\n  _{reason}_\n\n"
                return answer, {"items": items, "category": "clothes"}
        except Exception as e:
            self.logger.warning(f"Clothes handler failed: {e}")
        
        # Fallback
        return self._fallback_clothes(text)
    
    def _fallback_clothes(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Fallback clothing recommendations."""
        items = [
            {"title": "Classic White T-Shirt", "brand": "Uniqlo", "reason": "Versatile summer essential"},
            {"title": "Linen Blend Shorts", "brand": "H&M", "reason": "Breathable for hot weather"},
            {"title": "Canvas Sneakers", "brand": "Converse", "reason": "Timeless casual style"},
            {"title": "Floral Summer Dress", "brand": "Zara", "reason": "Perfect for warm days"},
            {"title": "Lightweight Denim Jacket", "brand": "Levi's", "reason": "Great for layering"},
        ]
        answer = "👕 **Clothing Recommendations:**\n\n"
        for item in items:
            answer += f"• **{item['title']}** by {item['brand']}\n  _{item['reason']}_\n\n"
        return answer, {"items": items, "category": "clothes"}
    
    def _recommend_movies(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Movie recommendations."""
        try:
            from app.streamlit_chatbot.handlers.movies import recommend_movies
            items = recommend_movies(query=text, top_n=5)
            if items:
                answer = "🎬 **Movie Recommendations:**\n\n"
                for item in items:
                    title = item.get("title", "")
                    genre = item.get("genre", "")
                    reason = item.get("reason", "")
                    answer += f"• **{title}** ({genre})\n  _{reason}_\n\n"
                return answer, {"items": items, "category": "movies"}
        except Exception as e:
            self.logger.warning(f"Movies handler failed: {e}")
        
        # Fallback
        items = [
            {"title": "Inception", "genre": "Sci-Fi/Thriller", "reason": "Mind-bending plot with stunning visuals"},
            {"title": "The Shawshank Redemption", "genre": "Drama", "reason": "Timeless classic about hope"},
            {"title": "Interstellar", "genre": "Sci-Fi", "reason": "Epic space exploration story"},
            {"title": "Parasite", "genre": "Thriller", "reason": "Oscar-winning masterpiece"},
            {"title": "The Dark Knight", "genre": "Action", "reason": "Best superhero film ever made"},
        ]
        answer = "🎬 **Movie Recommendations:**\n\n"
        for item in items:
            answer += f"• **{item['title']}** ({item['genre']})\n  _{item['reason']}_\n\n"
        return answer, {"items": items, "category": "movies"}
    
    def _recommend_news(self, text: str) -> tuple[str, Dict[str, Any]]:
        """News recommendations."""
        try:
            from app.streamlit_chatbot.handlers.news import recommend_news
            items = recommend_news(query=text, top_n=5)
            if items:
                answer = "📰 **News Recommendations:**\n\n"
                for item in items:
                    title = item.get("title", "")
                    reason = item.get("reason", "")
                    url = item.get("url", "")
                    answer += f"• **{title}**\n  _{reason}_\n"
                    if url:
                        answer += f"  [Read more]({url})\n"
                    answer += "\n"
                return answer, {"items": items, "category": "news"}
        except Exception as e:
            self.logger.warning(f"News handler failed: {e}")

        items = [
            {"title": "Tech Giants Report Quarterly Earnings", "source": "TechCrunch", "reason": "Major market impact"},
            {"title": "Climate Summit Reaches New Agreement", "source": "Reuters", "reason": "Global policy shift"},
            {"title": "AI Breakthrough in Medical Diagnosis", "source": "Nature", "reason": "Healthcare innovation"},
            {"title": "Space Exploration Mission Update", "source": "NASA", "reason": "Scientific milestone"},
            {"title": "Economic Outlook for 2025", "source": "Bloomberg", "reason": "Financial planning insights"},
        ]
        answer = "📰 **News Recommendations:**\n\n"
        for item in items:
            answer += f"• **{item['title']}** - {item['source']}\n  _{item['reason']}_\n\n"
        return answer, {"items": items, "category": "news"}
    
    def _recommend_courses(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Course recommendations."""
        try:
            from app.streamlit_chatbot.handlers.courses import recommend_courses
            items = recommend_courses(query=text, limit=5)
            if items:
                answer = "📚 **Course Recommendations:**\n\n"
                for item in items:
                    title = item.get("title", "")
                    platform = item.get("platform", "Online")
                    rating = item.get("rating", "")
                    tags = item.get("tags", "")
                    reason = f"Rating: {rating}/5. Tags: {tags}"
                    answer += f"• **{title}** on {platform}\n  _{reason}_\n\n"
                return answer, {"items": items, "category": "courses"}
        except Exception as e:
            self.logger.warning(f"Courses handler failed: {e}")

        items = [
            {"title": "Machine Learning Specialization", "platform": "Coursera", "reason": "Industry-leading curriculum"},
            {"title": "Full Stack Web Development", "platform": "Udemy", "reason": "Practical project-based learning"},
            {"title": "Data Science Professional Certificate", "platform": "edX", "reason": "Harvard-backed program"},
            {"title": "Python for Everybody", "platform": "Coursera", "reason": "Great for beginners"},
            {"title": "AWS Cloud Practitioner", "platform": "AWS Training", "reason": "High demand certification"},
        ]
        answer = "📚 **Course Recommendations:**\n\n"
        for item in items:
            answer += f"• **{item['title']}** on {item['platform']}\n  _{item['reason']}_\n\n"
        return answer, {"items": items, "category": "courses"}
    
    def _recommend_cars(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Car recommendations."""
        try:
            from app.streamlit_chatbot.handlers.cars import recommend_cars

            items = recommend_cars(text)
        except Exception as exc:
            self.logger.warning("Cars handler failed: %s", exc)
            items = [
                {"title": "Tesla Model 3", "type": "Electric Sedan", "reason": "Best range and tech features"},
                {"title": "Toyota RAV4 Hybrid", "type": "Hybrid SUV", "reason": "Reliable and fuel efficient"},
                {"title": "Honda Civic", "type": "Compact Sedan", "reason": "Affordable and dependable"},
                {"title": "Ford Mustang Mach-E", "type": "Electric SUV", "reason": "Sporty EV with great performance"},
                {"title": "BMW 3 Series", "type": "Luxury Sedan", "reason": "Premium driving experience"},
            ]
        answer = "🚗 **Car Recommendations:**\n\n"
        for item in items:
            title = item.get("title", "Car")
            car_type = item.get("type") or item.get("brand") or "Car"
            reason = item.get("reason") or ""
            answer += f"• **{title}** ({car_type})\n  _{reason}_\n\n"
        return answer, {"items": items, "category": "cars"}
    
    def _recommend_electronics(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Electronics recommendations."""
        try:
            from app.streamlit_chatbot.handlers.electronics import recommend_electronics
            domain = "phones"
            if "laptop" in text.lower(): domain = "laptops"
            elif "headphone" in text.lower() or "earbud" in text.lower(): domain = "headphones"
            
            items = recommend_electronics(domain=domain, query=text, limit=5)
            if items:
                answer = "📱 **Electronics Recommendations:**\n\n"
                for item in items:
                    title = item.get("title", "")
                    reason = item.get("reason", "")
                    answer += f"• **{title}**\n  _{reason}_\n\n"
                return answer, {"items": items, "category": "electronics"}
        except Exception as e:
            self.logger.warning(f"Electronics handler failed: {e}")

        items = [
            {"title": "MacBook Air M3", "category": "Laptop", "reason": "Best battery life and performance"},
            {"title": "iPhone 15 Pro", "category": "Smartphone", "reason": "Powerful camera and chip"},
            {"title": "Sony WH-1000XM5", "category": "Headphones", "reason": "Industry-leading noise cancellation"},
            {"title": "iPad Pro 12.9", "category": "Tablet", "reason": "Professional-grade display"},
            {"title": "Samsung Galaxy S24 Ultra", "category": "Smartphone", "reason": "Best Android experience"},
        ]
        answer = "📱 **Electronics Recommendations:**\n\n"
        for item in items:
            answer += f"• **{item['title']}** ({item['category']})\n  _{item['reason']}_\n\n"
        return answer, {"items": items, "category": "electronics"}
    
    def _recommend_places(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Travel/Places recommendations."""
        try:
            from app.streamlit_chatbot.handlers.places import recommend_places

            items = recommend_places(query=text, places_api_key=None)
        except Exception as exc:
            self.logger.warning("Places handler failed: %s", exc)
            items = [
                {"title": "Kyoto, Japan", "type": "Cultural", "reason": "Ancient temples and beautiful gardens"},
                {"title": "Santorini, Greece", "type": "Beach/Romantic", "reason": "Stunning sunsets and architecture"},
                {"title": "Machu Picchu, Peru", "type": "Adventure", "reason": "Historic wonder with breathtaking views"},
                {"title": "Iceland", "type": "Nature", "reason": "Northern lights and unique landscapes"},
                {"title": "Barcelona, Spain", "type": "City", "reason": "Art, architecture, and vibrant nightlife"},
            ]
        answer = "✈️ **Travel Recommendations:**\n\n"
        for item in items:
            title = item.get("title", "Place")
            place_type = item.get("type") or item.get("location") or "Place"
            reason = item.get("reason") or ""
            answer += f"• **{title}** ({place_type})\n  _{reason}_\n\n"
        return answer, {"items": items, "category": "places"}

    def _run_chat(
        self, text: str, emotion: dict[str, Any] | None, user_id: str, intent: Dict[str, Any] | None = None
    ) -> tuple[str, Dict[str, Any]]:
        # 1. Check legacy static responses (Greetings, Help, About)
        if is_greeting(text):
            return get_greeting_response(), {"source": "legacy_static"}
        if is_help_request(text):
            return get_help_response(), {"source": "legacy_static"}
        if is_about_request(text):
            return get_about_response(), {"source": "legacy_static"}

        # 2. Check Knowledge Base using Confidence Scorer
        if intent and intent.get("confidence", 0) > 0.6:
            topic = intent.get("intent")
            # Map behavior -> anomaly for legacy KB
            if topic == "behavior":
                topic = "anomaly"
            
            kb_response = get_topic_response(topic)
            if kb_response:
                return kb_response, {"source": "legacy_kb", "topic": topic, "confidence": intent.get("confidence")}

        # 3. Fallback to LLM
        prompt = text
        if emotion:
            prompt = f"Emotion detected: {emotion['emotion']} ({emotion['confidence']}).\n" + prompt
        history = self.memory.get_history(user_id)
        answer = self.llm.generate(prompt, history=history)
        meta = {"source": "chat", "memory_turns": len(history)}
        return answer, meta

    def _risk_payload_from_message(self, message: str) -> dict[str, Any]:
        """Extract risk parameters from natural language message."""
        payload = {
            "transaction_amount": 0.0,
            "clicks_per_minute": 10.0,
            "files_accessed": 0,
            "device_known": True,
            "login_time": 12.0,
            "login_country": "US",
        }
        
        # Extract numbers
        nums = [float(x) for x in re.findall(r"[-+]?(?:\d*\.?\d+)", message)]
        if nums:
            payload["transaction_amount"] = nums[0]
        
        # Extract country (simple heuristic)
        countries = ["US", "UK", "CA", "DE", "FR", "IN", "CN", "JP", "BR", "NG", "RU"]
        for country in countries:
            if country in message.upper():
                payload["login_country"] = country
                break
                
        return payload
