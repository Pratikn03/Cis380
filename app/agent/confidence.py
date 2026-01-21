"""
==============================================================================
INTENT CONFIDENCE SCORING MODULE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Provides confidence scores for intent detection, helping the orchestrator
make better routing decisions and providing transparency to users.

CONFIDENCE LEVELS:
------------------
- HIGH (0.8-1.0): Strong keyword match, unambiguous intent
- MEDIUM (0.5-0.8): Partial match, some ambiguity
- LOW (0.0-0.5): Weak match, fallback likely

USAGE:
------
    from app.agent.confidence import IntentConfidenceScorer
    
    scorer = IntentConfidenceScorer()
    result = scorer.score("check this transaction for fraud")
    # Returns: {"intent": "fraud", "confidence": 0.92, "level": "high"}
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional


@dataclass
class IntentScore:
    """Result of intent confidence scoring."""
    intent: str
    confidence: float
    level: str  # "high", "medium", "low"
    matched_keywords: List[str]
    alternative_intents: List[Tuple[str, float]]
    
    def to_dict(self) -> Dict:
        return {
            "intent": self.intent,
            "confidence": round(self.confidence, 4),
            "level": self.level,
            "matched_keywords": self.matched_keywords,
            "alternatives": [
                {"intent": i, "confidence": round(c, 4)} 
                for i, c in self.alternative_intents[:3]
            ]
        }


class IntentConfidenceScorer:
    """
    Scores confidence for intent detection using keyword matching,
    pattern analysis, and context clues.
    """
    
    # Intent keyword mappings with weights
    INTENT_KEYWORDS: Dict[str, Dict[str, float]] = {
        "fraud": {
            "fraud": 1.0, "fraudulent": 1.0, "scam": 0.9, "suspicious": 0.8,
            "transaction": 0.6, "payment": 0.5, "credit": 0.5, "card": 0.4,
            "money": 0.4, "transfer": 0.5, "unauthorized": 0.9, "fake": 0.7,
            "phishing": 0.8, "identity": 0.6, "theft": 0.7, "steal": 0.7,
        },
        "cyber": {
            "cyber": 1.0, "hack": 0.9, "hacker": 0.9, "intrusion": 0.9,
            "malware": 0.9, "virus": 0.8, "attack": 0.7, "breach": 0.8,
            "security": 0.6, "network": 0.5, "firewall": 0.7, "threat": 0.7,
            "vulnerability": 0.8, "exploit": 0.8, "ddos": 0.9, "ransomware": 0.9,
            "login": 0.4, "password": 0.5, "authentication": 0.6,
        },
        "behavior": {
            "behavior": 1.0, "behavioral": 1.0, "anomaly": 0.8, "pattern": 0.6,
            "user": 0.4, "activity": 0.5, "unusual": 0.7, "suspicious": 0.6,
            "employee": 0.5, "insider": 0.8, "risk": 0.5, "deviation": 0.7,
            "baseline": 0.7, "monitoring": 0.5, "tracking": 0.5,
        },
        "voice_emotion": {
            "voice": 1.0, "emotion": 1.0, "audio": 0.9, "speech": 0.8,
            "tone": 0.7, "stress": 0.7, "angry": 0.8, "sad": 0.8, "happy": 0.8,
            "sentiment": 0.7, "feeling": 0.6, "mood": 0.6, "call": 0.4,
            "recording": 0.5, "sound": 0.5,
        },
        "vision": {
            "image": 1.0, "photo": 0.9, "picture": 0.9, "face": 0.8,
            "deepfake": 1.0, "real": 0.5, "fake": 0.7, "authentic": 0.7,
            "detect": 0.4, "analyze": 0.3, "recognition": 0.7, "logo": 0.8,
            "brand": 0.8, "visual": 0.7,
        },
        "video": {
            "video": 1.0, "footage": 0.9, "surveillance": 0.8, "clip": 0.7,
            "recording": 0.6, "temporal": 0.8, "frame": 0.7, "movie": 0.3,
            "stream": 0.6, "camera": 0.5,
        },
        "recommend": {
            "recommend": 1.0, "suggestion": 0.9, "suggest": 0.9, "movie": 0.8,
            "film": 0.7, "watch": 0.6, "like": 0.4, "similar": 0.7,
            "preference": 0.6, "best": 0.4, "top": 0.4, "popular": 0.5,
            "genre": 0.7, "action": 0.3, "comedy": 0.3, "drama": 0.3,
        },
        "rag": {
            "document": 1.0, "search": 0.7, "find": 0.5, "policy": 0.8,
            "manual": 0.8, "guide": 0.7, "lookup": 0.7, "query": 0.6,
            "information": 0.5, "knowledge": 0.6, "retrieve": 0.8,
            "pdf": 0.8, "file": 0.5, "upload": 0.6,
        },
        "chat": {
            "hello": 0.8, "hi": 0.8, "hey": 0.8, "help": 0.6, "what": 0.3,
            "how": 0.3, "why": 0.3, "explain": 0.5, "tell": 0.4,
            "thanks": 0.7, "thank": 0.7, "bye": 0.8, "goodbye": 0.8,
        }
    }
    
    # Patterns for stronger matching
    INTENT_PATTERNS: Dict[str, List[str]] = {
        "fraud": [
            r"check.*fraud", r"fraud.*detection", r"is.*fraudulent",
            r"suspicious.*transaction", r"credit.*card.*fraud",
        ],
        "cyber": [
            r"cyber.*attack", r"security.*breach", r"network.*intrusion",
            r"detect.*malware", r"hack.*attempt",
        ],
        "behavior": [
            r"user.*behavior", r"unusual.*activity", r"behavioral.*anomaly",
            r"insider.*threat", r"employee.*monitoring",
        ],
        "voice_emotion": [
            r"voice.*emotion", r"detect.*emotion.*audio", r"analyze.*speech",
            r"emotional.*state", r"tone.*analysis",
        ],
        "vision": [
            r"analyze.*image", r"detect.*deepfake", r"real.*or.*fake",
            r"image.*authentic", r"face.*recognition",
        ],
        "video": [
            r"analyze.*video", r"video.*detection", r"surveillance.*footage",
            r"fake.*video", r"temporal.*analysis",
        ],
        "recommend": [
            r"recommend.*movie", r"suggest.*film", r"what.*watch",
            r"movie.*like", r"similar.*to",
        ],
        "rag": [
            r"search.*document", r"find.*policy", r"lookup.*manual",
            r"query.*knowledge", r"retrieve.*information",
        ],
    }
    
    def __init__(self):
        """Initialize the confidence scorer."""
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        self._compiled_patterns: Dict[str, List[re.Pattern]] = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self._compiled_patterns[intent] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def score(self, text: str) -> IntentScore:
        """
        Score the confidence for intent detection.
        
        Args:
            text: Input text to analyze
            
        Returns:
            IntentScore with confidence metrics
        """
        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))
        
        # Calculate scores for each intent
        intent_scores: Dict[str, Tuple[float, List[str]]] = {}
        
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0.0
            matched = []
            
            # Keyword matching
            for word, weight in keywords.items():
                if word in words:
                    score += weight
                    matched.append(word)
            
            # Pattern matching (bonus)
            if intent in self._compiled_patterns:
                for pattern in self._compiled_patterns[intent]:
                    if pattern.search(text_lower):
                        score += 0.5
                        matched.append(f"pattern:{pattern.pattern[:20]}")
            
            # Normalize score
            max_possible = sum(keywords.values()) + len(self._compiled_patterns.get(intent, [])) * 0.5
            normalized = min(score / max(max_possible * 0.3, 1), 1.0)  # 30% of max = full confidence
            
            intent_scores[intent] = (normalized, matched)
        
        # Sort by score
        sorted_intents = sorted(
            intent_scores.items(), 
            key=lambda x: x[1][0], 
            reverse=True
        )
        
        # Get top intent
        top_intent, (top_score, top_matched) = sorted_intents[0]
        
        # Determine confidence level
        if top_score >= 0.8:
            level = "high"
        elif top_score >= 0.5:
            level = "medium"
        else:
            level = "low"
            # Default to chat for low confidence
            if top_score < 0.2:
                top_intent = "chat"
                top_score = 0.5
                level = "medium"
        
        # Get alternatives
        alternatives = [(i, s[0]) for i, s in sorted_intents[1:4] if s[0] > 0.1]
        
        return IntentScore(
            intent=top_intent,
            confidence=top_score,
            level=level,
            matched_keywords=top_matched,
            alternative_intents=alternatives
        )
    
    def explain(self, text: str) -> str:
        """
        Get a human-readable explanation of the confidence scoring.
        
        Args:
            text: Input text
            
        Returns:
            Explanation string
        """
        result = self.score(text)
        
        explanation = f"""
Intent Detection Analysis
========================
Input: "{text[:50]}{'...' if len(text) > 50 else ''}"

Primary Intent: {result.intent.upper()}
Confidence: {result.confidence:.1%} ({result.level})
Matched Keywords: {', '.join(result.matched_keywords[:5]) or 'None'}

Alternative Intents:
"""
        for alt_intent, alt_conf in result.alternative_intents:
            explanation += f"  - {alt_intent}: {alt_conf:.1%}\n"
        
        if not result.alternative_intents:
            explanation += "  None with significant confidence\n"
        
        return explanation.strip()


# Singleton instance
_scorer: Optional[IntentConfidenceScorer] = None


def get_confidence_scorer() -> IntentConfidenceScorer:
    """Get or create the singleton confidence scorer."""
    global _scorer
    if _scorer is None:
        _scorer = IntentConfidenceScorer()
    return _scorer


def score_intent(text: str) -> Dict:
    """
    Quick function to score intent confidence.
    
    Args:
        text: Input text
        
    Returns:
        Dict with intent, confidence, level, and alternatives
    """
    return get_confidence_scorer().score(text).to_dict()


__all__ = [
    "IntentConfidenceScorer",
    "IntentScore", 
    "get_confidence_scorer",
    "score_intent"
]
