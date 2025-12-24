"""Enhanced chat responses for OmniChatX offline mode."""

from __future__ import annotations


def get_greeting_response() -> str:
    """Return a friendly greeting."""
    return """Hello! I'm OmniChatX, your intelligent assistant!

I can help you with:
- General Questions - Ask me anything!
- Fraud Detection - Analyze transaction risk
- Cyber Security - Detect network threats
- Behavior Analysis - Identify anomalies
- Vision Analysis - Analyze images
- Voice Emotion - Detect emotions from audio
- Document Search - Search uploaded docs

Just type your question or use the attachment feature for media!"""


def get_help_response() -> str:
    """Return help information."""
    return """OmniChatX Capabilities

**Chat Features:**
- Ask any question - I'll search docs or use AI
- Include numbers for fraud/cyber/behavior scoring

**Media Analysis:**
- Upload images for classification
- Record/upload audio for emotion detection
- Upload videos for temporal analysis

**Risk Detection:**
- Say 'fraud check: [values]' for fraud scoring
- Say 'cyber threat: [values]' for threat analysis
- Say 'behavior: [values]' for anomaly detection

**Example prompts:**
- 'What is fraud detection?'
- 'Check fraud risk: 5000 3 online'
- 'Analyze this image' (with attachment)"""


def get_training_response() -> str:
    """Return training/demo guidance."""
    return """Getting Started with OmniChatX

**Quick Start:**
1. Train models: `python scripts/train_all.py --with-vision`
2. Run demo: `bash scripts/run_demo.sh`
3. Test: `bash scripts/codex_test_all.sh`

**Features Ready to Use:**
- Chat with document search (RAG)
- Voice emotion detection
- Image classification
- Risk scoring (fraud/cyber/behavior)

**Tip:** Enable OpenAI API key for enhanced responses!"""


def get_about_response() -> str:
    """Return about/info response."""
    return """About OmniChatX

I'm OmniChatX - a comprehensive AI assistant built by Pratik!

**My Capabilities:**
- Natural language understanding
- Document search & retrieval (RAG)
- Fraud/Cyber/Behavior risk analysis
- Image & video classification
- Voice emotion detection
- Personalized recommendations

**Tech Stack:**
- FastAPI backend
- Streamlit frontend
- PyTorch & TensorFlow models
- OpenAI integration (optional)"""


def get_fallback_response() -> str:
    """Return fallback when no specific answer found."""
    return """I searched my knowledge base but couldn't find specific information on that topic.

**You can:**
- Rephrase your question
- Add documents to `data/docs/` for me to learn from
- Enable OpenAI API for broader knowledge

**Try asking about:**
- Fraud detection
- Cybersecurity
- Machine learning
- Or say 'help' for more options!"""


def is_greeting(text: str) -> bool:
    """Check if text is a greeting."""
    lower = text.lower()
    return any(
        k in lower
        for k in ("hello", "hi ", "hey", "greet", "good morning", "good afternoon", "good evening")
    )


def is_help_request(text: str) -> bool:
    """Check if text is asking for help."""
    lower = text.lower()
    return any(
        k in lower for k in ("help", "what can you do", "capabilities", "features", "how to use")
    )


def is_training_request(text: str) -> bool:
    """Check if text is asking about training/demo."""
    lower = text.lower()
    return any(
        k in lower
        for k in (
            "next step",
            "next steps",
            "what are we doing",
            "what to do",
            "train",
            "training",
            "demo",
        )
    )


def is_about_request(text: str) -> bool:
    """Check if text is asking about the bot."""
    lower = text.lower()
    return any(k in lower for k in ("about", "who are you", "what are you", "your name"))


def get_enhanced_response(message: str) -> str | None:
    """Get enhanced response based on message type.

    Returns None if no specific response is available.
    """
    if not message or not message.strip():
        return get_greeting_response()

    if is_greeting(message):
        return get_greeting_response()

    if is_help_request(message):
        return get_help_response()

    if is_training_request(message):
        return get_training_response()

    if is_about_request(message):
        return get_about_response()

    return None
