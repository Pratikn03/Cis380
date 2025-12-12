"""Simple keyword-based policy for routing."""


def decide(message: str) -> str:
    text = message.lower()
    if any(k in text for k in ["fraud", "transaction", "card"]):
        return "fraud"
    if any(k in text for k in ["cyber", "network", "attack", "packet"]):
        return "cyber"
    if any(k in text for k in ["behavior", "insider", "employee"]):
        return "behavior"
    if "recommend" in text or "suggest" in text:
        return "recommend"
    if any(k in text for k in ["career", "careers", "skills", "role", "roles", "job", "jobs", "ml engineer", "data scientist", "skill map"]):
        return "rag"
    if any(k in text for k in ["doc", "note", "pdf", "paper", "from docs", "rag"]):
        return "rag"
    return "llm"
