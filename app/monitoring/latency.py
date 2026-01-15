"""
==============================================================================
LATENCY MONITORING MODULE
==============================================================================
Author: Pratik Niroula
Project: Sentifargo - Sentifargo

PURPOSE:
--------
Monitors and tracks latency metrics across all API endpoints and
model inference operations.

FEATURES:
---------
- Request latency tracking
- Model inference timing
- Percentile calculations (p50, p95, p99)
- Anomaly detection on latency
- Real-time dashboarding support

USAGE:
------
    from app.monitoring.latency import LatencyMonitor, track_latency
    
    monitor = LatencyMonitor()
    
    # Track a request
    with monitor.track("fraud_inference"):
        result = fraud_model.predict(data)
    
    # Or use decorator
    @track_latency("endpoint_name")
    def my_endpoint():
        ...
    
    # Get stats
    stats = monitor.get_stats("fraud_inference")
"""

from __future__ import annotations

import time
import functools
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager
import threading
import statistics


@dataclass
class LatencyStats:
    """Latency statistics for an operation."""
    name: str
    count: int
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    std_dev_ms: float
    last_ms: float
    window_minutes: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class LatencySample:
    """Single latency measurement."""
    name: str
    latency_ms: float
    timestamp: str
    success: bool
    metadata: Dict[str, Any]


class LatencyMonitor:
    """
    Monitor and track latency across system operations.
    """
    
    # Latency thresholds (in ms)
    THRESHOLDS = {
        "fast": 100,     # < 100ms is fast
        "normal": 500,   # < 500ms is normal
        "slow": 1000,    # < 1000ms is slow
        "critical": 5000 # > 5000ms is critical
    }
    
    def __init__(
        self,
        max_samples: int = 10000,
        window_minutes: int = 60
    ):
        """
        Initialize the latency monitor.
        
        Args:
            max_samples: Maximum samples to keep per operation
            window_minutes: Default time window for statistics
        """
        self.max_samples = max_samples
        self.window_minutes = window_minutes
        
        # Storage: operation_name -> deque of (timestamp, latency_ms, success)
        self._samples: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=max_samples)
        )
        
        # Running totals for quick stats
        self._totals: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {"count": 0, "sum": 0, "min": float("inf"), "max": 0}
        )
        
        # Thread safety
        self._lock = threading.Lock()
    
    def record(
        self,
        name: str,
        latency_ms: float,
        success: bool = True,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record a latency measurement.
        
        Args:
            name: Operation name
            latency_ms: Latency in milliseconds
            success: Whether operation succeeded
            metadata: Additional context
        """
        timestamp = datetime.now().isoformat()
        
        with self._lock:
            self._samples[name].append((timestamp, latency_ms, success, metadata or {}))
            
            totals = self._totals[name]
            totals["count"] += 1
            totals["sum"] += latency_ms
            totals["min"] = min(totals["min"], latency_ms)
            totals["max"] = max(totals["max"], latency_ms)
    
    @contextmanager
    def track(self, name: str, metadata: Optional[Dict] = None):
        """
        Context manager to track operation latency.
        
        Usage:
            with monitor.track("my_operation"):
                do_work()
        """
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            self.record(name, latency_ms, success, metadata)
    
    def _get_recent_samples(
        self,
        name: str,
        window_minutes: Optional[int] = None
    ) -> List[float]:
        """Get latency values within time window."""
        window = window_minutes or self.window_minutes
        cutoff = datetime.now() - timedelta(minutes=window)
        cutoff_str = cutoff.isoformat()
        
        with self._lock:
            samples = self._samples.get(name, [])
            return [
                lat for ts, lat, _, _ in samples
                if ts >= cutoff_str
            ]
    
    def get_stats(
        self,
        name: str,
        window_minutes: Optional[int] = None
    ) -> Optional[LatencyStats]:
        """
        Get latency statistics for an operation.
        
        Args:
            name: Operation name
            window_minutes: Time window (default: configured window)
            
        Returns:
            LatencyStats or None if no data
        """
        window = window_minutes or self.window_minutes
        values = self._get_recent_samples(name, window)
        
        if not values:
            return None
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return LatencyStats(
            name=name,
            count=n,
            mean_ms=statistics.mean(values),
            median_ms=statistics.median(values),
            min_ms=min(values),
            max_ms=max(values),
            p50_ms=sorted_values[int(n * 0.50)],
            p95_ms=sorted_values[min(int(n * 0.95), n - 1)],
            p99_ms=sorted_values[min(int(n * 0.99), n - 1)],
            std_dev_ms=statistics.stdev(values) if n > 1 else 0,
            last_ms=values[-1] if values else 0,
            window_minutes=window,
        )
    
    def get_all_stats(self, window_minutes: Optional[int] = None) -> Dict[str, LatencyStats]:
        """Get stats for all tracked operations."""
        result = {}
        with self._lock:
            names = list(self._samples.keys())
        
        for name in names:
            stats = self.get_stats(name, window_minutes)
            if stats:
                result[name] = stats
        
        return result
    
    def get_slow_operations(
        self,
        threshold_ms: float = 1000,
        window_minutes: Optional[int] = None
    ) -> List[Dict]:
        """Get operations exceeding latency threshold."""
        result = []
        all_stats = self.get_all_stats(window_minutes)
        
        for name, stats in all_stats.items():
            if stats.p95_ms > threshold_ms:
                result.append({
                    "name": name,
                    "p95_ms": stats.p95_ms,
                    "p99_ms": stats.p99_ms,
                    "max_ms": stats.max_ms,
                    "count": stats.count,
                    "severity": self._classify_latency(stats.p95_ms),
                })
        
        return sorted(result, key=lambda x: x["p95_ms"], reverse=True)
    
    def _classify_latency(self, latency_ms: float) -> str:
        """Classify latency into severity level."""
        if latency_ms < self.THRESHOLDS["fast"]:
            return "fast"
        elif latency_ms < self.THRESHOLDS["normal"]:
            return "normal"
        elif latency_ms < self.THRESHOLDS["slow"]:
            return "slow"
        else:
            return "critical"
    
    def detect_anomalies(
        self,
        name: str,
        z_threshold: float = 3.0
    ) -> List[Dict]:
        """
        Detect latency anomalies using z-score.
        
        Args:
            name: Operation name
            z_threshold: Z-score threshold for anomaly
            
        Returns:
            List of anomalous samples
        """
        with self._lock:
            samples = list(self._samples.get(name, []))
        
        if len(samples) < 10:
            return []
        
        latencies = [s[1] for s in samples]
        mean = statistics.mean(latencies)
        std = statistics.stdev(latencies)
        
        if std == 0:
            return []
        
        anomalies = []
        for ts, lat, success, meta in samples:
            z_score = (lat - mean) / std
            if abs(z_score) > z_threshold:
                anomalies.append({
                    "timestamp": ts,
                    "latency_ms": lat,
                    "z_score": z_score,
                    "success": success,
                    "metadata": meta,
                })
        
        return anomalies
    
    def get_timeline(
        self,
        name: str,
        bucket_minutes: int = 5,
        window_minutes: Optional[int] = None
    ) -> List[Dict]:
        """
        Get latency timeline aggregated by time buckets.
        
        Args:
            name: Operation name
            bucket_minutes: Size of time buckets
            window_minutes: Total time window
            
        Returns:
            List of time buckets with aggregated stats
        """
        window = window_minutes or self.window_minutes
        now = datetime.now()
        cutoff = now - timedelta(minutes=window)
        
        with self._lock:
            samples = [
                (ts, lat) for ts, lat, _, _ in self._samples.get(name, [])
                if ts >= cutoff.isoformat()
            ]
        
        if not samples:
            return []
        
        # Group by bucket
        buckets = defaultdict(list)
        for ts, lat in samples:
            sample_time = datetime.fromisoformat(ts)
            bucket_key = sample_time.replace(
                minute=(sample_time.minute // bucket_minutes) * bucket_minutes,
                second=0,
                microsecond=0
            )
            buckets[bucket_key].append(lat)
        
        # Calculate stats per bucket
        timeline = []
        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]
            timeline.append({
                "timestamp": bucket_time.isoformat(),
                "count": len(values),
                "mean_ms": statistics.mean(values),
                "min_ms": min(values),
                "max_ms": max(values),
                "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) > 1 else values[0],
            })
        
        return timeline
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall latency monitoring summary."""
        all_stats = self.get_all_stats()
        
        total_requests = sum(s.count for s in all_stats.values())
        avg_latency = (
            sum(s.mean_ms * s.count for s in all_stats.values()) / total_requests
            if total_requests > 0 else 0
        )
        
        slow_ops = self.get_slow_operations()
        
        return {
            "total_operations_tracked": len(all_stats),
            "total_requests": total_requests,
            "overall_avg_latency_ms": round(avg_latency, 2),
            "slow_operations_count": len(slow_ops),
            "critical_operations": [
                op["name"] for op in slow_ops 
                if op["severity"] == "critical"
            ],
            "top_by_volume": sorted(
                [{"name": n, "count": s.count} for n, s in all_stats.items()],
                key=lambda x: x["count"],
                reverse=True
            )[:5],
        }
    
    def reset(self, name: Optional[str] = None) -> None:
        """Reset latency data."""
        with self._lock:
            if name:
                self._samples.pop(name, None)
                self._totals.pop(name, None)
            else:
                self._samples.clear()
                self._totals.clear()


# Singleton instance
_latency_monitor: Optional[LatencyMonitor] = None


def get_latency_monitor() -> LatencyMonitor:
    """Get or create the singleton latency monitor."""
    global _latency_monitor
    if _latency_monitor is None:
        _latency_monitor = LatencyMonitor()
    return _latency_monitor


def track_latency(name: str, metadata: Optional[Dict] = None):
    """
    Decorator to track function latency.
    
    Usage:
        @track_latency("my_function")
        def my_function():
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_latency_monitor()
            with monitor.track(name, metadata):
                return func(*args, **kwargs)
        return wrapper
    return decorator


__all__ = [
    "LatencyMonitor",
    "LatencyStats",
    "LatencySample",
    "get_latency_monitor",
    "track_latency",
]
