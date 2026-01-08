"""
==============================================================================
ALERT SEVERITY SCORING MODULE
==============================================================================
Author: Pratik Niroula
Project: SentinelForge - Universal Anomaly Intelligence System

PURPOSE:
--------
Provides intelligent severity scoring for alerts across all detection modules
(fraud, cyber, behavior, etc.), enabling proper prioritization and response.

SEVERITY LEVELS:
----------------
- CRITICAL (0.9-1.0): Immediate action required, confirmed threat
- HIGH (0.7-0.9): Likely threat, urgent review needed
- MEDIUM (0.4-0.7): Suspicious activity, standard review
- LOW (0.2-0.4): Minor anomaly, routine monitoring
- INFO (0.0-0.2): Normal variation, no action needed

FEATURES:
---------
- Multi-factor severity calculation
- Context-aware scoring
- Historical pattern analysis
- Automatic escalation triggers
- Alert aggregation and deduplication

USAGE:
------
    from app.monitoring.alerts import AlertSeverityScorer, Alert
    
    scorer = AlertSeverityScorer()
    alert = scorer.create_alert(
        alert_type="fraud",
        risk_score=0.85,
        context={"amount": 10000, "location": "foreign"}
    )
    # Returns: Alert with severity="high", priority=2, etc.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import threading


class Severity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    
    @property
    def priority(self) -> int:
        """Numeric priority (lower = more urgent)."""
        return {
            Severity.CRITICAL: 1,
            Severity.HIGH: 2,
            Severity.MEDIUM: 3,
            Severity.LOW: 4,
            Severity.INFO: 5
        }[self]
    
    @property
    def color(self) -> str:
        """UI color code."""
        return {
            Severity.CRITICAL: "#FF0000",  # Red
            Severity.HIGH: "#FF6600",      # Orange
            Severity.MEDIUM: "#FFCC00",    # Yellow
            Severity.LOW: "#0099FF",       # Blue
            Severity.INFO: "#00CC00"       # Green
        }[self]


@dataclass
class Alert:
    """Security/anomaly alert."""
    id: str
    timestamp: str
    alert_type: str  # "fraud", "cyber", "behavior", "vision", etc.
    severity: Severity
    priority: int
    title: str
    description: str
    risk_score: float
    confidence: float
    source: str
    user_id: Optional[str]
    context: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    related_alerts: List[str] = field(default_factory=list)
    status: str = "open"  # "open", "acknowledged", "investigating", "resolved", "false_positive"
    assigned_to: Optional[str] = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['severity'] = self.severity.value
        return result
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AlertRule:
    """Rule for generating alerts."""
    name: str
    alert_type: str
    condition: str  # Description of trigger condition
    base_severity: Severity
    risk_threshold: float
    escalation_factors: Dict[str, float]  # Factor -> multiplier
    cooldown_minutes: int = 5  # Prevent duplicate alerts


class AlertSeverityScorer:
    """
    Intelligent alert severity scoring and management.
    """
    
    # Base severity thresholds by risk score
    SEVERITY_THRESHOLDS = [
        (0.9, Severity.CRITICAL),
        (0.7, Severity.HIGH),
        (0.4, Severity.MEDIUM),
        (0.2, Severity.LOW),
        (0.0, Severity.INFO),
    ]
    
    # Alert type configurations
    ALERT_CONFIGS: Dict[str, Dict] = {
        "fraud": {
            "title_template": "Fraud Alert: {summary}",
            "escalation_factors": {
                "high_amount": 1.3,      # Transaction > $5000
                "new_location": 1.2,     # Different country
                "velocity": 1.4,         # Multiple transactions
                "compromised_card": 1.5, # Known compromised
            },
            "recommendations": [
                "Verify transaction with cardholder",
                "Check recent transaction history",
                "Consider temporary account freeze",
                "Review IP and device fingerprint",
            ]
        },
        "cyber": {
            "title_template": "Cyber Alert: {summary}",
            "escalation_factors": {
                "known_threat_actor": 1.5,
                "critical_system": 1.4,
                "data_exfiltration": 1.6,
                "lateral_movement": 1.3,
                "persistence": 1.4,
            },
            "recommendations": [
                "Isolate affected systems",
                "Capture forensic evidence",
                "Reset compromised credentials",
                "Review network logs",
            ]
        },
        "behavior": {
            "title_template": "Behavior Alert: {summary}",
            "escalation_factors": {
                "after_hours": 1.2,
                "sensitive_data": 1.4,
                "repeat_offense": 1.3,
                "elevated_privileges": 1.3,
            },
            "recommendations": [
                "Interview employee if appropriate",
                "Review access logs",
                "Check for policy violations",
                "Monitor continued activity",
            ]
        },
        "vision": {
            "title_template": "Vision Alert: {summary}",
            "escalation_factors": {
                "deepfake_detected": 1.5,
                "brand_misuse": 1.3,
                "identity_fraud": 1.4,
            },
            "recommendations": [
                "Verify image source",
                "Cross-reference with known images",
                "Check for manipulation artifacts",
            ]
        },
        "voice": {
            "title_template": "Voice Alert: {summary}",
            "escalation_factors": {
                "stress_detected": 1.2,
                "anger_detected": 1.3,
                "caller_verification_failed": 1.4,
            },
            "recommendations": [
                "Review call recording",
                "Escalate to supervisor if needed",
                "Document emotional context",
            ]
        },
    }
    
    def __init__(self):
        """Initialize the severity scorer."""
        self._alerts: List[Alert] = []
        self._alert_counts: Dict[str, int] = defaultdict(int)
        self._recent_alerts: Dict[str, datetime] = {}  # For deduplication
        self._lock = threading.Lock()
    
    def _calculate_base_severity(self, risk_score: float) -> Severity:
        """Calculate base severity from risk score."""
        for threshold, severity in self.SEVERITY_THRESHOLDS:
            if risk_score >= threshold:
                return severity
        return Severity.INFO
    
    def _apply_escalation(
        self,
        base_severity: Severity,
        risk_score: float,
        alert_type: str,
        context: Dict[str, Any]
    ) -> Tuple[Severity, float]:
        """Apply escalation factors to adjust severity."""
        config = self.ALERT_CONFIGS.get(alert_type, {})
        escalation_factors = config.get("escalation_factors", {})
        
        adjusted_score = risk_score
        
        for factor, multiplier in escalation_factors.items():
            if context.get(factor):
                adjusted_score = min(adjusted_score * multiplier, 1.0)
        
        # Recalculate severity with adjusted score
        adjusted_severity = self._calculate_base_severity(adjusted_score)
        
        return adjusted_severity, adjusted_score
    
    def _generate_title(self, alert_type: str, context: Dict[str, Any]) -> str:
        """Generate alert title."""
        config = self.ALERT_CONFIGS.get(alert_type, {})
        template = config.get("title_template", "{alert_type} Alert: {summary}")
        
        summary = context.get("summary", "Anomaly detected")
        return template.format(summary=summary, alert_type=alert_type.title())
    
    def _generate_description(
        self,
        alert_type: str,
        risk_score: float,
        severity: Severity,
        context: Dict[str, Any]
    ) -> str:
        """Generate detailed alert description."""
        desc_parts = [
            f"A {severity.value} severity {alert_type} alert has been triggered.",
            f"Risk Score: {risk_score:.1%}",
        ]
        
        if context.get("user_id"):
            desc_parts.append(f"User: {context['user_id']}")
        
        if context.get("details"):
            desc_parts.append(f"Details: {context['details']}")
        
        return " ".join(desc_parts)
    
    def _get_recommendations(self, alert_type: str, severity: Severity) -> List[str]:
        """Get recommendations based on alert type and severity."""
        config = self.ALERT_CONFIGS.get(alert_type, {})
        all_recs = config.get("recommendations", [])
        
        # More recommendations for higher severity
        if severity in (Severity.CRITICAL, Severity.HIGH):
            return all_recs
        elif severity == Severity.MEDIUM:
            return all_recs[:3]
        else:
            return all_recs[:1]
    
    def _check_duplicate(self, alert_type: str, user_id: Optional[str], context: Dict) -> bool:
        """Check if this is a duplicate alert within cooldown period."""
        # Create a key for deduplication
        key_parts = [alert_type]
        if user_id:
            key_parts.append(user_id)
        if context.get("source_id"):
            key_parts.append(str(context["source_id"]))
        
        key = ":".join(key_parts)
        
        with self._lock:
            last_alert = self._recent_alerts.get(key)
            if last_alert:
                config = self.ALERT_CONFIGS.get(alert_type, {})
                cooldown = config.get("cooldown_minutes", 5)
                if datetime.now() - last_alert < timedelta(minutes=cooldown):
                    return True
            
            self._recent_alerts[key] = datetime.now()
            return False
    
    def create_alert(
        self,
        alert_type: str,
        risk_score: float,
        confidence: float = 0.8,
        source: str = "system",
        user_id: Optional[str] = None,
        context: Optional[Dict] = None,
        force: bool = False
    ) -> Optional[Alert]:
        """
        Create a new alert with intelligent severity scoring.
        
        Args:
            alert_type: Type of alert (fraud, cyber, behavior, etc.)
            risk_score: Risk score 0.0-1.0
            confidence: Model confidence 0.0-1.0
            source: Source system/model
            user_id: Related user ID
            context: Additional context
            force: Create even if duplicate
            
        Returns:
            Alert object or None if deduplicated
        """
        context = context or {}
        
        # Check for duplicates
        if not force and self._check_duplicate(alert_type, user_id, context):
            return None
        
        # Calculate severity
        base_severity = self._calculate_base_severity(risk_score)
        final_severity, adjusted_score = self._apply_escalation(
            base_severity, risk_score, alert_type, context
        )
        
        # Generate alert content
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"
        title = self._generate_title(alert_type, context)
        description = self._generate_description(alert_type, risk_score, final_severity, context)
        recommendations = self._get_recommendations(alert_type, final_severity)
        
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            alert_type=alert_type,
            severity=final_severity,
            priority=final_severity.priority,
            title=title,
            description=description,
            risk_score=adjusted_score,
            confidence=confidence,
            source=source,
            user_id=user_id,
            context=context,
            recommendations=recommendations,
        )
        
        with self._lock:
            self._alerts.append(alert)
            self._alert_counts[alert_type] += 1
        
        return alert
    
    def score_severity(
        self,
        alert_type: str,
        risk_score: float,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Score severity without creating an alert.
        
        Returns:
            Dict with severity, adjusted_score, factors applied
        """
        context = context or {}
        base_severity = self._calculate_base_severity(risk_score)
        final_severity, adjusted_score = self._apply_escalation(
            base_severity, risk_score, alert_type, context
        )
        
        # Identify which factors were applied
        config = self.ALERT_CONFIGS.get(alert_type, {})
        applied_factors = [
            factor for factor in config.get("escalation_factors", {}).keys()
            if context.get(factor)
        ]
        
        return {
            "base_severity": base_severity.value,
            "final_severity": final_severity.value,
            "base_score": risk_score,
            "adjusted_score": adjusted_score,
            "priority": final_severity.priority,
            "color": final_severity.color,
            "applied_factors": applied_factors,
        }
    
    def get_alerts(
        self,
        alert_type: Optional[str] = None,
        severity: Optional[Severity] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get alerts with optional filters."""
        with self._lock:
            results = []
            for alert in reversed(self._alerts):
                if len(results) >= limit:
                    break
                if alert_type and alert.alert_type != alert_type:
                    continue
                if severity and alert.severity != severity:
                    continue
                if status and alert.status != status:
                    continue
                results.append(alert.to_dict())
            return results
    
    def update_alert_status(
        self,
        alert_id: str,
        status: str,
        assigned_to: Optional[str] = None
    ) -> bool:
        """Update alert status."""
        with self._lock:
            for alert in self._alerts:
                if alert.id == alert_id:
                    alert.status = status
                    if assigned_to:
                        alert.assigned_to = assigned_to
                    return True
        return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        with self._lock:
            open_alerts = [a for a in self._alerts if a.status == "open"]
            severity_counts = defaultdict(int)
            for alert in open_alerts:
                severity_counts[alert.severity.value] += 1
            
            return {
                "total_alerts": len(self._alerts),
                "open_alerts": len(open_alerts),
                "by_type": dict(self._alert_counts),
                "by_severity": dict(severity_counts),
                "critical_count": severity_counts.get("critical", 0),
                "high_count": severity_counts.get("high", 0),
            }


# Singleton instance
_alert_scorer: Optional[AlertSeverityScorer] = None


def get_alert_scorer() -> AlertSeverityScorer:
    """Get or create the singleton alert scorer."""
    global _alert_scorer
    if _alert_scorer is None:
        _alert_scorer = AlertSeverityScorer()
    return _alert_scorer


def create_alert(
    alert_type: str,
    risk_score: float,
    **kwargs
) -> Optional[Alert]:
    """Quick function to create an alert."""
    return get_alert_scorer().create_alert(alert_type, risk_score, **kwargs)


def score_severity(alert_type: str, risk_score: float, context: Optional[Dict] = None) -> Dict:
    """Quick function to score severity."""
    return get_alert_scorer().score_severity(alert_type, risk_score, context)


__all__ = [
    "AlertSeverityScorer",
    "Alert",
    "Severity",
    "AlertRule",
    "get_alert_scorer",
    "create_alert",
    "score_severity",
]
