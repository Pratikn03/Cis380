from __future__ import annotations

import random
from typing import Sequence


class LLMStub:
    """Intelligent offline LLM client with varied responses."""

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

    def generate(self, prompt: str, context: Sequence[str] | None = None) -> str:
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
