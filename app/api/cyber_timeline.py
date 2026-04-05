"""
==============================================================================
CYBER TIMELINE VISUALIZATION API
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Provides timeline-based visualization for cyber security events,
enabling analysts to see attack patterns over time.

FEATURES:
---------
- Time-series event aggregation
- Attack pattern detection
- IP/source geolocation
- Severity timeline
- Interactive filtering

API ENDPOINTS:
--------------
    GET /api/cyber/timeline
    - Returns events grouped by time window

    GET /api/cyber/timeline/patterns
    - Returns detected attack patterns

    GET /api/cyber/timeline/sources
    - Returns source IP/location breakdown

USAGE:
------
    # Fetch timeline data
    curl http://localhost:8000/api/cyber/timeline?window=1h&limit=100
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
import random

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/cyber/timeline", tags=["cyber-timeline"])


@dataclass
class TimelineEvent:
    """Single event in the timeline."""

    timestamp: str
    event_type: str  # "intrusion", "malware", "ddos", "brute_force", etc.
    severity: str  # "critical", "high", "medium", "low", "info"
    source_ip: str
    destination_ip: str
    description: str
    confidence: float
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class TimelineBucket:
    """Aggregated events in a time window."""

    start_time: str
    end_time: str
    total_events: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    top_sources: List[Dict[str, Any]]
    peak_score: float


@dataclass
class AttackPattern:
    """Detected attack pattern."""

    pattern_id: str
    pattern_type: str  # "scan", "brute_force", "exfiltration", "lateral_movement"
    start_time: str
    end_time: str
    source_ips: List[str]
    target_ips: List[str]
    event_count: int
    confidence: float
    description: str
    mitre_techniques: List[str]


class CyberTimelineService:
    """Service for cyber timeline data and analysis."""

    # Event types with their characteristics
    EVENT_TYPES = {
        "intrusion": {"base_severity": "high", "mitre": ["T1190", "T1133"]},
        "malware": {"base_severity": "critical", "mitre": ["T1204", "T1059"]},
        "ddos": {"base_severity": "high", "mitre": ["T1498"]},
        "brute_force": {"base_severity": "medium", "mitre": ["T1110"]},
        "scan": {"base_severity": "low", "mitre": ["T1046"]},
        "data_exfil": {"base_severity": "critical", "mitre": ["T1041", "T1048"]},
        "lateral_move": {"base_severity": "high", "mitre": ["T1021", "T1570"]},
        "privilege_esc": {"base_severity": "high", "mitre": ["T1068", "T1548"]},
        "persistence": {"base_severity": "medium", "mitre": ["T1547", "T1053"]},
        "recon": {"base_severity": "low", "mitre": ["T1595", "T1592"]},
    }

    # Sample source IPs for demo
    SAMPLE_SOURCES = [
        ("192.168.1.100", "Internal - Workstation"),
        ("192.168.1.50", "Internal - Server"),
        ("10.0.0.25", "Internal - Database"),
        ("45.33.32.156", "External - US"),
        ("185.220.101.1", "External - Tor Exit"),
        ("91.121.87.10", "External - EU"),
        ("103.224.182.252", "External - APAC"),
        ("23.94.5.133", "External - Cloud"),
    ]

    def __init__(self):
        """Initialize the timeline service."""
        self._events: List[TimelineEvent] = []
        self._patterns: List[AttackPattern] = []
        self._generate_sample_data()

    def _generate_sample_data(self, num_events: int = 500) -> None:
        """Generate sample timeline data for demonstration."""
        now = datetime.now()

        for i in range(num_events):
            # Random time in last 24 hours
            time_offset = random.randint(0, 24 * 60)  # minutes
            event_time = now - timedelta(minutes=time_offset)

            # Random event type (weighted)
            event_type = random.choices(
                list(self.EVENT_TYPES.keys()),
                weights=[0.1, 0.05, 0.05, 0.15, 0.25, 0.03, 0.07, 0.05, 0.1, 0.15],
                k=1,
            )[0]

            event_config = self.EVENT_TYPES[event_type]

            # Adjust severity based on type with some randomness
            severities = ["critical", "high", "medium", "low", "info"]
            base_idx = severities.index(event_config["base_severity"])
            severity = severities[max(0, min(4, base_idx + random.randint(-1, 1)))]

            # Random source/dest
            source = random.choice(self.SAMPLE_SOURCES)
            dest = random.choice(self.SAMPLE_SOURCES)
            while dest == source:
                dest = random.choice(self.SAMPLE_SOURCES)

            event = TimelineEvent(
                timestamp=event_time.isoformat(),
                event_type=event_type,
                severity=severity,
                source_ip=source[0],
                destination_ip=dest[0],
                description=f"{event_type.replace('_', ' ').title()} detected from {source[1]}",
                confidence=round(random.uniform(0.6, 0.99), 2),
                metadata={
                    "source_location": source[1],
                    "dest_location": dest[1],
                    "mitre": event_config["mitre"],
                    "bytes_transferred": (
                        random.randint(100, 100000)
                        if event_type in ["data_exfil", "scan"]
                        else None
                    ),
                },
            )
            self._events.append(event)

        # Sort by timestamp
        self._events.sort(key=lambda e: e.timestamp, reverse=True)

        # Generate some patterns
        self._generate_patterns()

    def _generate_patterns(self) -> None:
        """Detect and generate attack patterns from events."""
        now = datetime.now()

        # Sample patterns
        patterns = [
            AttackPattern(
                pattern_id="pattern_001",
                pattern_type="scan",
                start_time=(now - timedelta(hours=6)).isoformat(),
                end_time=(now - timedelta(hours=4)).isoformat(),
                source_ips=["45.33.32.156", "91.121.87.10"],
                target_ips=["192.168.1.100", "192.168.1.50", "10.0.0.25"],
                event_count=47,
                confidence=0.89,
                description="Port scanning activity detected from external sources targeting internal network",
                mitre_techniques=["T1046", "T1595"],
            ),
            AttackPattern(
                pattern_id="pattern_002",
                pattern_type="brute_force",
                start_time=(now - timedelta(hours=3)).isoformat(),
                end_time=(now - timedelta(hours=2)).isoformat(),
                source_ips=["185.220.101.1"],
                target_ips=["192.168.1.50"],
                event_count=156,
                confidence=0.95,
                description="SSH brute force attack from Tor exit node against internal server",
                mitre_techniques=["T1110.001", "T1110.003"],
            ),
            AttackPattern(
                pattern_id="pattern_003",
                pattern_type="lateral_movement",
                start_time=(now - timedelta(hours=1)).isoformat(),
                end_time=now.isoformat(),
                source_ips=["192.168.1.100"],
                target_ips=["10.0.0.25", "192.168.1.50"],
                event_count=23,
                confidence=0.78,
                description="Potential lateral movement from compromised workstation",
                mitre_techniques=["T1021", "T1570"],
            ),
        ]
        self._patterns = patterns

    def get_timeline(
        self,
        window_minutes: int = 60,
        limit: int = 24,
        severity_filter: Optional[str] = None,
        event_type_filter: Optional[str] = None,
    ) -> List[Dict]:
        """
        Get timeline data aggregated by time window.

        Args:
            window_minutes: Size of each time bucket in minutes
            limit: Maximum number of buckets to return
            severity_filter: Filter by severity level
            event_type_filter: Filter by event type

        Returns:
            List of timeline buckets
        """
        # Filter events
        filtered = self._events
        if severity_filter:
            filtered = [e for e in filtered if e.severity == severity_filter]
        if event_type_filter:
            filtered = [e for e in filtered if e.event_type == event_type_filter]

        if not filtered:
            return []

        # Group by time window
        now = datetime.now()
        buckets: Dict[int, List[TimelineEvent]] = defaultdict(list)

        for event in filtered:
            event_time = datetime.fromisoformat(event.timestamp)
            minutes_ago = int((now - event_time).total_seconds() / 60)
            bucket_idx = minutes_ago // window_minutes
            if bucket_idx < limit:
                buckets[bucket_idx].append(event)

        # Build bucket summaries
        result = []
        for i in range(limit):
            bucket_events = buckets.get(i, [])
            start_time = now - timedelta(minutes=(i + 1) * window_minutes)
            end_time = now - timedelta(minutes=i * window_minutes)

            # Aggregate stats
            by_severity = defaultdict(int)
            by_type = defaultdict(int)
            source_counts = defaultdict(int)
            peak_score = 0.0

            for event in bucket_events:
                by_severity[event.severity] += 1
                by_type[event.event_type] += 1
                source_counts[event.source_ip] += 1
                peak_score = max(peak_score, event.confidence)

            # Top sources
            top_sources = sorted(
                [{"ip": ip, "count": count} for ip, count in source_counts.items()],
                key=lambda x: x["count"],
                reverse=True,
            )[:5]

            bucket = TimelineBucket(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                total_events=len(bucket_events),
                by_severity=dict(by_severity),
                by_type=dict(by_type),
                top_sources=top_sources,
                peak_score=peak_score,
            )
            result.append(asdict(bucket))

        return result

    def get_events(
        self,
        limit: int = 100,
        offset: int = 0,
        severity: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict]:
        """Get individual events with filtering."""
        filtered = self._events
        if severity:
            filtered = [e for e in filtered if e.severity == severity]
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]

        return [e.to_dict() for e in filtered[offset : offset + limit]]

    def get_patterns(self) -> List[Dict]:
        """Get detected attack patterns."""
        return [asdict(p) for p in self._patterns]

    def get_sources_breakdown(self) -> Dict[str, Any]:
        """Get breakdown of event sources."""
        source_stats = defaultdict(
            lambda: {"count": 0, "severities": defaultdict(int), "types": defaultdict(int)}
        )

        for event in self._events:
            stats = source_stats[event.source_ip]
            stats["count"] += 1
            stats["severities"][event.severity] += 1
            stats["types"][event.event_type] += 1

        # Convert to list and sort
        sources = []
        for ip, stats in source_stats.items():
            location = next((s[1] for s in self.SAMPLE_SOURCES if s[0] == ip), "Unknown")
            sources.append(
                {
                    "ip": ip,
                    "location": location,
                    "total_events": stats["count"],
                    "by_severity": dict(stats["severities"]),
                    "by_type": dict(stats["types"]),
                    "risk_score": min(
                        1.0, stats["count"] / 100 + stats["severities"].get("critical", 0) * 0.3
                    ),
                }
            )

        sources.sort(key=lambda x: x["total_events"], reverse=True)

        return {
            "total_unique_sources": len(sources),
            "external_sources": len([s for s in sources if "External" in s["location"]]),
            "internal_sources": len([s for s in sources if "Internal" in s["location"]]),
            "sources": sources[:20],  # Top 20
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get overall timeline summary."""
        now = datetime.now()

        # Events in last hour
        hour_ago = now - timedelta(hours=1)
        recent_events = [e for e in self._events if datetime.fromisoformat(e.timestamp) > hour_ago]

        # Severity breakdown
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        for event in self._events:
            severity_counts[event.severity] += 1
            type_counts[event.event_type] += 1

        return {
            "total_events": len(self._events),
            "events_last_hour": len(recent_events),
            "active_patterns": len(self._patterns),
            "by_severity": dict(severity_counts),
            "by_type": dict(type_counts),
            "critical_alerts": severity_counts.get("critical", 0),
            "high_alerts": severity_counts.get("high", 0),
        }


# Singleton service instance
_timeline_service: Optional[CyberTimelineService] = None


def get_timeline_service() -> CyberTimelineService:
    """Get or create the timeline service."""
    global _timeline_service
    if _timeline_service is None:
        _timeline_service = CyberTimelineService()
    return _timeline_service


# =============================================================================
# API ENDPOINTS
# =============================================================================


@router.get("")
def get_timeline(
    window: int = Query(60, description="Time window in minutes"),
    limit: int = Query(24, description="Number of buckets"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """Get aggregated timeline data."""
    service = get_timeline_service()
    return {
        "timeline": service.get_timeline(window, limit, severity, event_type),
        "window_minutes": window,
        "buckets": limit,
    }


@router.get("/events")
def get_events(
    limit: int = Query(100, description="Number of events"),
    offset: int = Query(0, description="Offset for pagination"),
    severity: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
):
    """Get individual timeline events."""
    service = get_timeline_service()
    return {
        "events": service.get_events(limit, offset, severity, event_type),
        "limit": limit,
        "offset": offset,
    }


@router.get("/patterns")
def get_patterns():
    """Get detected attack patterns."""
    service = get_timeline_service()
    return {
        "patterns": service.get_patterns(),
        "total": len(service._patterns),
    }


@router.get("/sources")
def get_sources():
    """Get source IP breakdown."""
    service = get_timeline_service()
    return service.get_sources_breakdown()


@router.get("/summary")
def get_summary():
    """Get timeline summary statistics."""
    service = get_timeline_service()
    return service.get_summary()


__all__ = [
    "router",
    "CyberTimelineService",
    "TimelineEvent",
    "TimelineBucket",
    "AttackPattern",
    "get_timeline_service",
]
