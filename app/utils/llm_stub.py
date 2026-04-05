from __future__ import annotations

import json
import os
import random
from typing import Sequence

import requests


class LLMStub:
    """Hybrid LLM client: offline-first with optional OpenAI chat completions."""

    # Knowledge base for common topics
    KNOWLEDGE = {
        "fraud": [
            "Fraud detection uses machine learning to identify suspicious patterns in transactions. Common techniques include anomaly detection, behavioral analysis, and rule-based systems.",
            "Modern fraud detection systems analyze transaction velocity, geographic patterns, device fingerprints, and spending behavior to catch fraudulent activity in real-time.",
            "Key fraud indicators include unusual transaction amounts, rapid successive transactions, mismatched billing/shipping addresses, and transactions from high-risk locations.",
        ],
        "cyber": [
            "Cybersecurity involves protecting systems, networks, and data from digital attacks. Key areas include network security, application security, and incident response.",
            "Common cyber threats include phishing, malware, ransomware, DDoS attacks, and social engineering. Defense requires multiple layers of protection.",
            "Zero-trust architecture assumes no user or system should be trusted by default. It requires verification for every access request, minimizing attack surface.",
        ],
        "machine learning": [
            "Machine learning enables computers to learn from data without explicit programming. It includes supervised learning, unsupervised learning, and reinforcement learning.",
            "Deep learning uses neural networks with multiple layers to learn complex patterns. It excels at image recognition, natural language processing, and speech recognition.",
            "Key ML concepts include training data, feature engineering, model selection, hyperparameter tuning, and cross-validation for robust model performance.",
        ],
        "anomaly": [
            "Anomaly detection identifies unusual patterns that don't conform to expected behavior. It's crucial for fraud detection, network security, and system monitoring.",
            "Statistical methods, isolation forests, autoencoders, and clustering algorithms are common approaches for detecting anomalies in data.",
            "Effective anomaly detection requires understanding normal behavior patterns first, then flagging deviations that exceed defined thresholds.",
        ],
    }

    GREETINGS = [
        "Hello! I'm your AI assistant. I can help with fraud detection, cybersecurity, machine learning questions, and movie recommendations. What would you like to know?",
        "Hi there! I'm here to assist you with anomaly detection, ML concepts, and recommendations. Feel free to ask anything!",
        "Welcome! I specialize in security analytics, machine learning, and intelligent recommendations. How can I help you today?",
    ]

    FALLBACKS = [
        "That's an interesting question! While I don't have specific information on that topic, I can help with fraud detection, cybersecurity, machine learning, or movie recommendations.",
        "I'd love to help with that! For best results, try asking about fraud detection, cyber threats, ML concepts, or ask me to recommend something.",
        "Great question! My expertise is in anomaly detection and security. Try asking about fraud patterns, cyber threats, or machine learning techniques.",
    ]

    def __init__(
        self,
        *,
        mode: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.mode = (mode or os.getenv("LLM_MODE", "offline")).strip().lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4")
        self.max_tokens = int(max_tokens or os.getenv("OPENAI_MAX_TOKENS", "800"))
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.timeout = float(timeout or os.getenv("OPENAI_TIMEOUT_SEC", "30"))

    def generate(
        self,
        prompt: str,
        context: Sequence[str] | None = None,
        *,
        history: Sequence[dict] | None = None,
    ) -> str:
        if self._use_online():
            try:
                return self._generate_online(prompt, context=context, history=history)
            except Exception:
                pass
        return self._generate_offline(prompt, context=context)

    def _use_online(self) -> bool:
        return self.mode in {"online", "auto"} and bool(self.api_key)

    def _generate_online(
        self,
        prompt: str,
        *,
        context: Sequence[str] | None,
        history: Sequence[dict] | None,
    ) -> str:
        messages = [{"role": "system", "content": "You are Sentifargo, a helpful AI assistant."}]
        messages.extend(self._history_messages(history))
        if context and not self._prompt_has_context(prompt):
            context_block = self._format_context(context)
            if context_block:
                messages.append(
                    {
                        "role": "system",
                        "content": f"Context for grounding:\n{context_block}",
                    }
                )
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": self.max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload),
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("OpenAI response contained no choices.")
        message = choices[0].get("message") or {}
        return str(message.get("content") or "").strip()

    def _generate_offline(self, prompt: str, context: Sequence[str] | None) -> str:
        prompt_lower = prompt.lower().strip()

        # Check for greetings
        if any(word in prompt_lower for word in ["hello", "hi", "hey", "greet"]):
            return random.choice(self.GREETINGS)

        # Check knowledge base
        for topic, responses in self.KNOWLEDGE.items():
            if topic in prompt_lower:
                return random.choice(responses)

        # Check for help request
        if any(word in prompt_lower for word in ["help", "what can", "how to"]):
            return """I can help you with:
• **Fraud Detection** - Ask about fraud patterns, detection methods
• **Cybersecurity** - Learn about threats and protection
• **Machine Learning** - Understand ML concepts and techniques
• **Recommendations** - Get movie, product, or content suggestions
• **Anomaly Detection** - Discover unusual patterns in data

Just ask a question or say "recommend a movie" to get started!"""

        # Use context if provided
        if context:
            context_text = " ".join(context[:2])
            return f"Based on the available information: {context_text[:300]}..."

        # Fallback response
        return random.choice(self.FALLBACKS)

    def _history_messages(self, history: Sequence[dict] | None) -> list[dict]:
        if not history:
            return []
        messages: list[dict] = []
        for turn in history[-6:]:
            user_text = str(turn.get("user") or "").strip()
            assistant_text = str(turn.get("assistant") or "").strip()
            if user_text:
                messages.append({"role": "user", "content": user_text})
            if assistant_text:
                messages.append({"role": "assistant", "content": assistant_text})
        return messages

    def _prompt_has_context(self, prompt: str) -> bool:
        lowered = prompt.lower()
        return "document context:" in lowered or "context:" in lowered

    def _format_context(self, context: Sequence[str]) -> str:
        chunks = []
        for idx, item in enumerate(context[:4]):
            text = str(item).replace("\n", " ").strip()
            if not text:
                continue
            chunks.append(f"[{idx + 1}] {text[:800]}")
        return "\n".join(chunks)
