"""
==============================================================================
REAL-TIME ALERT SERVICE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Centralized alert service for real-time notifications across all detection
modules. Supports multiple notification channels and alert routing.

CHANNELS:
---------
- Webhook (POST to configured URLs)
- Email (SMTP)
- Slack
- Console/Logging
- Custom handlers

USAGE:
------
    from app.services.alert_service import AlertService, Alert

    service = AlertService()
    service.add_webhook("https://hooks.slack.com/...")

    alert = Alert(
        alert_type="fraud",
        severity="high",
        message="High-risk transaction detected",
        data={"transaction_id": "123", "amount": 5000}
    )
    service.send(alert)
"""

from __future__ import annotations

import ipaddress
import json
import smtplib
import socket
import threading
import queue
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(Enum):
    """Types of alerts."""

    FRAUD = "fraud"
    CYBER = "cyber"
    BEHAVIOR = "behavior"
    VOICE = "voice"
    VISION = "vision"
    VIDEO = "video"
    SYSTEM = "system"
    PERFORMANCE = "performance"


@dataclass
class Alert:
    """Alert data structure."""

    alert_type: str
    severity: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "Sentifargo"
    tags: List[str] = field(default_factory=list)
    acknowledged: bool = False
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "tags": self.tags,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class AlertChannel(ABC):
    """Base class for alert channels."""

    @abstractmethod
    def send(self, alert: Alert) -> bool:
        """Send alert through this channel."""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if channel is enabled."""
        pass


class ConsoleChannel(AlertChannel):
    """Console/logging alert channel."""

    SEVERITY_COLORS = {
        "critical": "\033[91m",  # Red
        "high": "\033[93m",  # Yellow
        "medium": "\033[94m",  # Blue
        "low": "\033[92m",  # Green
        "info": "\033[97m",  # White
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        self.use_colors = use_colors
        self._enabled = True

    def send(self, alert: Alert) -> bool:
        try:
            severity_upper = alert.severity.upper()

            if self.use_colors:
                color = self.SEVERITY_COLORS.get(alert.severity.lower(), "")
                print(f"{color}[{severity_upper}]{self.RESET} {alert.alert_type}: {alert.message}")
            else:
                print(f"[{severity_upper}] {alert.alert_type}: {alert.message}")

            logger.info(f"Alert sent to console: {alert.alert_id}")
            return True
        except Exception as e:
            logger.error(f"Console alert failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled


def _validate_webhook_url(url: str) -> None:
    """Reject private/loopback URLs to prevent SSRF via webhook registration."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Webhook URL must use http or https, got: {parsed.scheme!r}")
    host = (parsed.hostname or "").strip().lower()
    if not host:
        raise ValueError("Webhook URL has no valid host.")
    # Check if host is a bare IP address.
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            raise ValueError(f"Webhook URL resolves to a private/internal address: {host}")
    except ValueError as exc:
        # Re-raise SSRF block; for non-IP hosts fall through to DNS check.
        if "private" in str(exc) or "internal" in str(exc) or "loopback" in str(exc):
            raise
    # DNS-resolve the hostname and check resulting IPs.
    try:
        results = socket.getaddrinfo(host, None)
        for (_, _, _, _, sockaddr) in results:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
                    raise ValueError(
                        f"Webhook host {host!r} resolves to a private/internal address: {ip_str}"
                    )
            except ValueError as exc:
                if "private" in str(exc) or "internal" in str(exc) or "loopback" in str(exc):
                    raise
    except socket.gaierror:
        pass  # Let urlopen handle DNS failures at send time.


class WebhookChannel(AlertChannel):
    """Webhook alert channel (supports Slack, Discord, custom)."""

    def __init__(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "POST",
        timeout: int = 10,
    ):
        _validate_webhook_url(url)
        self.url = url
        self.headers = headers or {"Content-Type": "application/json"}
        self.method = method
        self.timeout = timeout
        self._enabled = True

    def send(self, alert: Alert) -> bool:
        try:
            # Format for Slack-compatible webhook
            payload = self._format_payload(alert)
            data = json.dumps(payload).encode("utf-8")

            req = Request(self.url, data=data, headers=self.headers, method=self.method)

            with urlopen(req, timeout=self.timeout) as response:
                if response.status < 300:
                    logger.info(f"Webhook alert sent: {alert.alert_id}")
                    return True
                else:
                    logger.warning(f"Webhook returned {response.status}")
                    return False

        except URLError as e:
            logger.error(f"Webhook failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False

    def _format_payload(self, alert: Alert) -> Dict[str, Any]:
        """Format alert for webhook (Slack-compatible)."""
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "ℹ️"}

        emoji = severity_emoji.get(alert.severity.lower(), "⚪")

        return {
            "text": f"{emoji} *{alert.severity.upper()}* - {alert.alert_type}",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {alert.message}"},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Type:*\n{alert.alert_type}"},
                        {"type": "mrkdwn", "text": f"*Severity:*\n{alert.severity}"},
                        {"type": "mrkdwn", "text": f"*ID:*\n{alert.alert_id}"},
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"```{json.dumps(alert.data, indent=2)}```"},
                },
            ],
        }

    def is_enabled(self) -> bool:
        return self._enabled


class EmailChannel(AlertChannel):
    """Email alert channel using SMTP."""

    def __init__(
        self,
        smtp_host: str = "localhost",
        smtp_port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        sender: str = "alerts@Sentifargo.ai",
        recipients: Optional[List[str]] = None,
        use_tls: bool = True,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.sender = sender
        self.recipients = recipients or []
        self.use_tls = use_tls
        self._enabled = bool(recipients)

    def send(self, alert: Alert) -> bool:
        if not self.recipients:
            logger.warning("No email recipients configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{alert.severity.upper()}] {alert.alert_type}: {alert.message[:50]}"
            msg["From"] = self.sender
            msg["To"] = ", ".join(self.recipients)

            # Plain text
            text = f"""
Alert: {alert.message}

Type: {alert.alert_type}
Severity: {alert.severity}
ID: {alert.alert_id}
Time: {alert.timestamp}

Data:
{json.dumps(alert.data, indent=2)}
"""

            # HTML
            html = f"""
<html>
<body>
<h2 style="color: {'red' if alert.severity == 'critical' else 'orange' if alert.severity == 'high' else 'blue'}">
    {alert.message}
</h2>
<table>
    <tr><td><strong>Type:</strong></td><td>{alert.alert_type}</td></tr>
    <tr><td><strong>Severity:</strong></td><td>{alert.severity}</td></tr>
    <tr><td><strong>ID:</strong></td><td>{alert.alert_id}</td></tr>
    <tr><td><strong>Time:</strong></td><td>{alert.timestamp}</td></tr>
</table>
<pre>{json.dumps(alert.data, indent=2)}</pre>
</body>
</html>
"""

            msg.attach(MIMEText(text, "plain"))
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.sendmail(self.sender, self.recipients, msg.as_string())

            logger.info(f"Email alert sent: {alert.alert_id}")
            return True

        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled and bool(self.recipients)


class CallbackChannel(AlertChannel):
    """Custom callback alert channel."""

    def __init__(self, callback: Callable[[Alert], bool]):
        self.callback = callback
        self._enabled = True

    def send(self, alert: Alert) -> bool:
        try:
            return self.callback(alert)
        except Exception as e:
            logger.error(f"Callback failed: {e}")
            return False

    def is_enabled(self) -> bool:
        return self._enabled


class AlertService:
    """
    Central alert service managing multiple channels and routing.
    """

    def __init__(
        self,
        dedup_window_seconds: int = 60,
        rate_limit_per_minute: int = 100,
        async_mode: bool = True,
    ):
        """
        Initialize alert service.

        Args:
            dedup_window_seconds: Window for deduplicating similar alerts
            rate_limit_per_minute: Maximum alerts per minute
            async_mode: Whether to send alerts asynchronously
        """
        self.channels: List[AlertChannel] = []
        self.dedup_window = timedelta(seconds=dedup_window_seconds)
        self.rate_limit = rate_limit_per_minute
        self.async_mode = async_mode

        # Deduplication tracking
        self._recent_alerts: Dict[str, datetime] = {}

        # Rate limiting
        self._alert_times: List[datetime] = []

        # Routing rules: (condition_fn, channel_indices)
        self._routing_rules: List[tuple] = []

        # Async queue
        self._queue: queue.Queue = queue.Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        # Statistics
        self._stats = {"total_sent": 0, "total_failed": 0, "deduplicated": 0, "rate_limited": 0}

        # Add console by default
        self.add_channel(ConsoleChannel())

        # Start worker if async
        if async_mode:
            self._start_worker()

    def add_channel(self, channel: AlertChannel) -> "AlertService":
        """Add an alert channel."""
        self.channels.append(channel)
        return self

    def add_webhook(self, url: str, headers: Optional[Dict] = None) -> "AlertService":
        """Add a webhook channel."""
        return self.add_channel(WebhookChannel(url, headers))

    def add_email(
        self, recipients: List[str], smtp_host: str = "localhost", smtp_port: int = 587, **kwargs
    ) -> "AlertService":
        """Add an email channel."""
        return self.add_channel(
            EmailChannel(smtp_host=smtp_host, smtp_port=smtp_port, recipients=recipients, **kwargs)
        )

    def add_callback(self, callback: Callable[[Alert], bool]) -> "AlertService":
        """Add a custom callback channel."""
        return self.add_channel(CallbackChannel(callback))

    def add_routing_rule(
        self, condition: Callable[[Alert], bool], channel_indices: List[int]
    ) -> "AlertService":
        """
        Add a routing rule.

        Args:
            condition: Function that takes Alert and returns True if rule applies
            channel_indices: List of channel indices to route to
        """
        self._routing_rules.append((condition, channel_indices))
        return self

    def _get_dedup_key(self, alert: Alert) -> str:
        """Generate deduplication key for an alert."""
        return f"{alert.alert_type}:{alert.severity}:{alert.message[:100]}"

    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if alert is a duplicate within the window."""
        key = self._get_dedup_key(alert)
        now = datetime.now()

        # Clean old entries
        cutoff = now - self.dedup_window
        self._recent_alerts = {k: v for k, v in self._recent_alerts.items() if v > cutoff}

        if key in self._recent_alerts:
            return True

        self._recent_alerts[key] = now
        return False

    def _is_rate_limited(self) -> bool:
        """Check if we're rate limited."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        # Clean old entries
        self._alert_times = [t for t in self._alert_times if t > cutoff]

        if len(self._alert_times) >= self.rate_limit:
            return True

        self._alert_times.append(now)
        return False

    def _get_target_channels(self, alert: Alert) -> List[AlertChannel]:
        """Get channels to send alert to based on routing rules."""
        # Check routing rules
        for condition, indices in self._routing_rules:
            if condition(alert):
                return [self.channels[i] for i in indices if i < len(self.channels)]

        # Default: all enabled channels
        return [ch for ch in self.channels if ch.is_enabled()]

    def send(self, alert: Alert) -> bool:
        """
        Send an alert through configured channels.

        Args:
            alert: Alert to send

        Returns:
            True if sent successfully to at least one channel
        """
        # Deduplication check
        if self._is_duplicate(alert):
            self._stats["deduplicated"] += 1
            logger.debug(f"Alert deduplicated: {alert.alert_id}")
            return False

        # Rate limiting check
        if self._is_rate_limited():
            self._stats["rate_limited"] += 1
            logger.warning(f"Alert rate limited: {alert.alert_id}")
            return False

        if self.async_mode:
            self._queue.put(alert)
            return True
        else:
            return self._send_sync(alert)

    def _send_sync(self, alert: Alert) -> bool:
        """Send alert synchronously."""
        channels = self._get_target_channels(alert)
        success = False

        for channel in channels:
            try:
                if channel.send(alert):
                    success = True
            except Exception as e:
                logger.error(f"Channel error: {e}")

        if success:
            self._stats["total_sent"] += 1
        else:
            self._stats["total_failed"] += 1

        return success

    def _worker(self) -> None:
        """Worker thread for async sending."""
        while self._running:
            try:
                alert = self._queue.get(timeout=1)
                self._send_sync(alert)
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")

    def _start_worker(self) -> None:
        """Start the worker thread."""
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        """Stop the alert service."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5)

    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize(),
            "channels": len(self.channels),
            "enabled_channels": sum(1 for ch in self.channels if ch.is_enabled()),
        }

    # Convenience methods for common alert types
    def fraud_alert(self, message: str, data: Dict = None, severity: str = "high") -> bool:
        """Send a fraud alert."""
        return self.send(
            Alert(alert_type="fraud", severity=severity, message=message, data=data or {})
        )

    def cyber_alert(self, message: str, data: Dict = None, severity: str = "high") -> bool:
        """Send a cyber security alert."""
        return self.send(
            Alert(alert_type="cyber", severity=severity, message=message, data=data or {})
        )

    def system_alert(self, message: str, data: Dict = None, severity: str = "medium") -> bool:
        """Send a system alert."""
        return self.send(
            Alert(alert_type="system", severity=severity, message=message, data=data or {})
        )


# Global instance
_default_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get or create the default alert service."""
    global _default_service
    if _default_service is None:
        _default_service = AlertService()
    return _default_service


def send_alert(
    message: str, alert_type: str = "system", severity: str = "medium", data: Optional[Dict] = None
) -> bool:
    """Convenience function to send an alert."""
    service = get_alert_service()
    return service.send(
        Alert(alert_type=alert_type, severity=severity, message=message, data=data or {})
    )


# CLI demo
if __name__ == "__main__":
    print("Testing Alert Service...")

    service = AlertService(async_mode=False)

    # Test alerts
    alerts = [
        Alert(
            alert_type="fraud",
            severity="critical",
            message="High-value transaction detected from unusual location",
            data={"transaction_id": "TXN123", "amount": 10000, "location": "Nigeria"},
        ),
        Alert(
            alert_type="cyber",
            severity="high",
            message="Multiple failed login attempts detected",
            data={"user_id": "user_456", "attempts": 15, "ip": "192.168.1.100"},
        ),
        Alert(
            alert_type="behavior",
            severity="medium",
            message="Unusual access pattern detected",
            data={"user_id": "user_789", "anomaly_score": 0.85},
        ),
        Alert(
            alert_type="system",
            severity="info",
            message="Model retrained successfully",
            data={"model": "fraud_xgb_v2", "accuracy": 0.945},
        ),
    ]

    for alert in alerts:
        service.send(alert)

    print(f"\n📊 Stats: {service.get_stats()}")
