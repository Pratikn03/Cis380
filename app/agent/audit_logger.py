"""
==============================================================================
AUDIT LOGGING MODULE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Provides comprehensive audit logging for all orchestrator requests,
enabling traceability, debugging, and compliance requirements.

FEATURES:
---------
- Request/Response logging with timestamps
- User tracking and session management
- Performance metrics (latency, tokens)
- Error tracking and alerting
- Export to JSON/CSV for analysis

LOG LEVELS:
-----------
- INFO: Normal operations
- WARNING: Potential issues
- ERROR: Failures requiring attention
- AUDIT: Security-relevant events

USAGE:
------
    from app.agent.audit_logger import AuditLogger
    
    logger = AuditLogger()
    
    # Log a request
    request_id = logger.log_request(
        user_id="user123",
        text="check transaction for fraud",
        route="fraud"
    )
    
    # Log the response
    logger.log_response(
        request_id=request_id,
        answer="Fraud probability: 0.85",
        confidence=0.92,
        latency_ms=45.2
    )
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque
import threading


@dataclass
class AuditEntry:
    """Single audit log entry."""
    id: str
    timestamp: str
    event_type: str  # "request", "response", "error", "alert"
    user_id: str
    session_id: Optional[str]
    route: Optional[str]
    text: Optional[str]
    answer: Optional[str]
    confidence: Optional[float]
    latency_ms: Optional[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AuditLogger:
    """
    Comprehensive audit logging for the orchestrator.
    
    Logs are stored in memory (ring buffer) and optionally persisted to disk.
    """
    
    def __init__(
        self,
        log_dir: Optional[Path] = None,
        max_memory_entries: int = 10000,
        persist: bool = True
    ):
        """
        Initialize the audit logger.
        
        Args:
            log_dir: Directory for persistent logs
            max_memory_entries: Maximum entries to keep in memory
            persist: Whether to persist logs to disk
        """
        self.log_dir = log_dir or Path("logs/audit")
        self.max_memory_entries = max_memory_entries
        self.persist = persist
        
        # Thread-safe ring buffer for in-memory logs
        self._entries: deque[AuditEntry] = deque(maxlen=max_memory_entries)
        self._lock = threading.Lock()
        
        # Request tracking
        self._pending_requests: Dict[str, AuditEntry] = {}
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "total_errors": 0,
            "routes": {},
            "avg_latency_ms": 0.0,
            "latency_samples": 0,
        }
        
        # Setup file logging
        if self.persist:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._setup_file_handler()
        
        # Standard logger for console output
        self._logger = logging.getLogger("Sentifargo.audit")
        self._logger.setLevel(logging.INFO)
    
    def _setup_file_handler(self) -> None:
        """Setup file handler for persistent logging."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"audit_{today}.jsonl"
        
        self._file_handler = logging.FileHandler(log_file)
        self._file_handler.setLevel(logging.INFO)
        
        # JSONL format for easy parsing
        formatter = logging.Formatter('%(message)s')
        self._file_handler.setFormatter(formatter)
    
    def _generate_id(self) -> str:
        """Generate unique request ID."""
        return f"req_{uuid.uuid4().hex[:12]}"
    
    def _now(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def _add_entry(self, entry: AuditEntry) -> None:
        """Add entry to memory and optionally persist."""
        with self._lock:
            self._entries.append(entry)
            
            if self.persist and hasattr(self, '_file_handler'):
                self._file_handler.emit(
                    logging.LogRecord(
                        name="audit",
                        level=logging.INFO,
                        pathname="",
                        lineno=0,
                        msg=entry.to_json(),
                        args=(),
                        exc_info=None
                    )
                )
    
    def _update_stats(
        self,
        route: Optional[str] = None,
        latency_ms: Optional[float] = None,
        error: bool = False
    ) -> None:
        """Update running statistics."""
        with self._lock:
            self._stats["total_requests"] += 1
            
            if error:
                self._stats["total_errors"] += 1
            
            if route:
                self._stats["routes"][route] = self._stats["routes"].get(route, 0) + 1
            
            if latency_ms is not None:
                n = self._stats["latency_samples"]
                avg = self._stats["avg_latency_ms"]
                self._stats["avg_latency_ms"] = (avg * n + latency_ms) / (n + 1)
                self._stats["latency_samples"] += 1
    
    def log_request(
        self,
        user_id: str,
        text: str,
        route: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log an incoming request.
        
        Args:
            user_id: User identifier
            text: Request text
            route: Detected route/intent
            session_id: Optional session identifier
            metadata: Additional metadata
            
        Returns:
            Request ID for tracking
        """
        request_id = self._generate_id()
        
        entry = AuditEntry(
            id=request_id,
            timestamp=self._now(),
            event_type="request",
            user_id=user_id,
            session_id=session_id,
            route=route,
            text=text[:500] if text else None,  # Truncate long text
            answer=None,
            confidence=None,
            latency_ms=None,
            metadata=metadata or {}
        )
        
        self._add_entry(entry)
        self._pending_requests[request_id] = entry
        
        self._logger.info(
            f"[REQUEST] {request_id} | user={user_id} | route={route} | len={len(text) if text else 0}"
        )
        
        return request_id
    
    def log_response(
        self,
        request_id: str,
        answer: str,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        route: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log a response to a request.
        
        Args:
            request_id: Original request ID
            answer: Response text
            confidence: Confidence score
            latency_ms: Processing time in milliseconds
            route: Final route used
            metadata: Additional metadata
        """
        entry = AuditEntry(
            id=request_id,
            timestamp=self._now(),
            event_type="response",
            user_id=self._pending_requests.get(request_id, AuditEntry(
                id="", timestamp="", event_type="", user_id="unknown",
                session_id=None, route=None, text=None, answer=None,
                confidence=None, latency_ms=None
            )).user_id,
            session_id=None,
            route=route,
            text=None,
            answer=answer[:500] if answer else None,  # Truncate
            confidence=confidence,
            latency_ms=latency_ms,
            metadata=metadata or {}
        )
        
        self._add_entry(entry)
        self._update_stats(route=route, latency_ms=latency_ms)
        
        # Clean up pending request
        self._pending_requests.pop(request_id, None)
        
        conf_str = f"{confidence:.2f}" if confidence else "0.00"
        latency_str = f"{latency_ms:.1f}" if latency_ms else "0.0"
        self._logger.info(
            f"[RESPONSE] {request_id} | route={route} | conf={conf_str} | latency={latency_str}ms"
        )
    
    def log_error(
        self,
        request_id: Optional[str],
        error: str,
        user_id: str = "unknown",
        route: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log an error.
        
        Args:
            request_id: Related request ID (if any)
            error: Error message
            user_id: User identifier
            route: Route where error occurred
            metadata: Additional context
        """
        entry = AuditEntry(
            id=request_id or self._generate_id(),
            timestamp=self._now(),
            event_type="error",
            user_id=user_id,
            session_id=None,
            route=route,
            text=None,
            answer=None,
            confidence=None,
            latency_ms=None,
            metadata=metadata or {},
            error=error[:500]
        )
        
        self._add_entry(entry)
        self._update_stats(error=True)
        
        self._logger.error(f"[ERROR] {entry.id} | route={route} | error={error[:100]}")
    
    def log_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        user_id: str = "system",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Log a security or system alert.
        
        Args:
            alert_type: Type of alert (e.g., "high_risk_fraud", "brute_force")
            message: Alert message
            severity: "info", "warning", "critical"
            user_id: Related user
            metadata: Additional context
            
        Returns:
            Alert ID
        """
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        
        entry = AuditEntry(
            id=alert_id,
            timestamp=self._now(),
            event_type="alert",
            user_id=user_id,
            session_id=None,
            route=None,
            text=None,
            answer=None,
            confidence=None,
            latency_ms=None,
            metadata={
                "alert_type": alert_type,
                "severity": severity,
                "message": message,
                **(metadata or {})
            }
        )
        
        self._add_entry(entry)
        
        log_method = getattr(self._logger, severity, self._logger.warning)
        log_method(f"[ALERT:{severity.upper()}] {alert_type} | {message[:100]}")
        
        return alert_id
    
    def get_recent(self, n: int = 100) -> List[Dict]:
        """Get recent log entries."""
        with self._lock:
            recent = list(self._entries)[-n:]
        return [e.to_dict() for e in recent]
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        with self._lock:
            return self._stats.copy()
    
    def get_user_history(self, user_id: str, n: int = 50) -> List[Dict]:
        """Get history for a specific user."""
        with self._lock:
            user_entries = [
                e for e in self._entries 
                if e.user_id == user_id
            ][-n:]
        return [e.to_dict() for e in user_entries]
    
    def export_csv(self, filepath: Path) -> None:
        """Export logs to CSV."""
        import csv
        
        with self._lock:
            entries = list(self._entries)
        
        if not entries:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=entries[0].to_dict().keys())
            writer.writeheader()
            for entry in entries:
                row = entry.to_dict()
                row['metadata'] = json.dumps(row['metadata'])
                writer.writerow(row)
    
    def search(
        self,
        user_id: Optional[str] = None,
        route: Optional[str] = None,
        event_type: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search log entries with filters.
        
        Args:
            user_id: Filter by user
            route: Filter by route
            event_type: Filter by event type
            start_time: ISO timestamp start
            end_time: ISO timestamp end
            limit: Maximum results
            
        Returns:
            Matching log entries
        """
        with self._lock:
            results = []
            for entry in reversed(list(self._entries)):
                if len(results) >= limit:
                    break
                
                if user_id and entry.user_id != user_id:
                    continue
                if route and entry.route != route:
                    continue
                if event_type and entry.event_type != event_type:
                    continue
                if start_time and entry.timestamp < start_time:
                    continue
                if end_time and entry.timestamp > end_time:
                    continue
                
                results.append(entry.to_dict())
            
            return results


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the singleton audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


__all__ = [
    "AuditLogger",
    "AuditEntry",
    "get_audit_logger"
]
