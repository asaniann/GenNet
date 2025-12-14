"""
Advanced monitoring and alerting utilities
"""
import logging
import time
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertRule:
    """Alert rule definition"""
    
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        level: AlertLevel = AlertLevel.WARNING,
        cooldown: int = 300,  # 5 minutes
        message_template: Optional[str] = None
    ):
        self.name = name
        self.condition = condition
        self.level = level
        self.cooldown = cooldown
        self.message_template = message_template or f"Alert: {name}"
        self.last_triggered: Optional[datetime] = None
        self.trigger_count = 0
    
    def check(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if alert condition is met
        
        Returns:
            Alert dict if triggered, None otherwise
        """
        if self.condition(metrics):
            # Check cooldown
            now = datetime.utcnow()
            if self.last_triggered:
                time_since_last = (now - self.last_triggered).total_seconds()
                if time_since_last < self.cooldown:
                    return None  # Still in cooldown
            
            self.last_triggered = now
            self.trigger_count += 1
            
            return {
                "name": self.name,
                "level": self.level.value,
                "message": self._format_message(metrics),
                "timestamp": now.isoformat(),
                "trigger_count": self.trigger_count,
                "metrics": metrics
            }
        
        return None
    
    def _format_message(self, metrics: Dict[str, Any]) -> str:
        """Format alert message"""
        try:
            return self.message_template.format(**metrics)
        except (KeyError, ValueError):
            return self.message_template


class MetricCollector:
    """Collects and aggregates metrics"""
    
    def __init__(self, window_size: int = 60):
        """
        Args:
            window_size: Number of samples to keep in sliding window
        """
        self.window_size = window_size
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
    
    def record(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        key = self._make_key(name, tags)
        timestamp = time.time()
        self.metrics[key].append((timestamp, value))
    
    def increment(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter"""
        key = self._make_key(name, tags)
        self.counters[key] += value
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge value"""
        key = self._make_key(name, tags)
        self.gauges[key] = value
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        key = self._make_key(name, tags)
        self.histograms[key].append(value)
        # Keep only recent values
        if len(self.histograms[key]) > self.window_size:
            self.histograms[key] = self.histograms[key][-self.window_size:]
    
    def get_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get statistics for a metric"""
        key = self._make_key(name, tags)
        
        if key in self.metrics and self.metrics[key]:
            values = [v for _, v in self.metrics[key]]
            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "sum": sum(values),
                "latest": values[-1] if values else None
            }
        
        return {}
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> int:
        """Get counter value"""
        key = self._make_key(name, tags)
        return self.counters.get(key, 0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, tags)
        return self.gauges.get(key)
    
    def _make_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Create metric key from name and tags"""
        if tags:
            tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
            return f"{name}[{tag_str}]"
        return name


class AlertManager:
    """Manages alerts and alert rules"""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.handlers: List[Callable[[Dict[str, Any]], None]] = []
        self.alert_history: deque = deque(maxlen=1000)
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.rules.append(rule)
    
    def add_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Add an alert handler (e.g., send to Slack, email, etc.)"""
        self.handlers.append(handler)
    
    def check_alerts(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Check all alert rules against current metrics
        
        Returns:
            List of triggered alerts
        """
        triggered = []
        
        for rule in self.rules:
            alert = rule.check(metrics)
            if alert:
                triggered.append(alert)
                self.alert_history.append(alert)
                
                # Notify handlers
                for handler in self.handlers:
                    try:
                        handler(alert)
                    except Exception as e:
                        logger.error(f"Error in alert handler: {e}")
        
        return triggered
    
    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get recent alerts within specified time window"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        return [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert["timestamp"]) > cutoff
        ]


class PerformanceMonitor:
    """Monitor performance metrics and latency"""
    
    def __init__(self, collector: MetricCollector):
        self.collector = collector
    
    def time_operation(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Decorator to time an operation
        
        Usage:
            @monitor.time_operation("create_network")
            async def create_network(...):
                ...
        """
        def decorator(func):
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start
                    self.collector.record(f"{name}.duration", duration, tags)
                    self.collector.increment(f"{name}.success", 1, tags)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self.collector.record(f"{name}.duration", duration, tags)
                    self.collector.increment(f"{name}.error", 1, tags)
                    raise
            
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start
                    self.collector.record(f"{name}.duration", duration, tags)
                    self.collector.increment(f"{name}.success", 1, tags)
                    return result
                except Exception as e:
                    duration = time.time() - start
                    self.collector.record(f"{name}.duration", duration, tags)
                    self.collector.increment(f"{name}.error", 1, tags)
                    raise
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator


# Global instances
_metric_collector: Optional[MetricCollector] = None
_alert_manager: Optional[AlertManager] = None


def get_metric_collector() -> MetricCollector:
    """Get or create global metric collector"""
    global _metric_collector
    if _metric_collector is None:
        _metric_collector = MetricCollector()
    return _metric_collector


def get_alert_manager() -> AlertManager:
    """Get or create global alert manager"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


# Predefined alert rules
def create_high_error_rate_rule(threshold: float = 0.1, window_minutes: int = 5) -> AlertRule:
    """Alert when error rate exceeds threshold"""
    def condition(metrics: Dict[str, Any]) -> bool:
        error_rate = metrics.get("error_rate", 0.0)
        return error_rate > threshold
    
    return AlertRule(
        name="high_error_rate",
        condition=condition,
        level=AlertLevel.ERROR,
        message_template="Error rate is {error_rate:.2%}, exceeds threshold"
    )


def create_high_latency_rule(threshold_ms: float = 1000.0, metric_name: str = "p95_latency") -> AlertRule:
    """Alert when latency exceeds threshold"""
    def condition(metrics: Dict[str, Any]) -> bool:
        latency = metrics.get(metric_name, 0.0)
        return latency > threshold_ms
    
    return AlertRule(
        name="high_latency",
        condition=condition,
        level=AlertLevel.WARNING,
        message_template=f"{metric_name} is {{p95_latency}}ms, exceeds {threshold_ms}ms threshold"
    )


def create_low_success_rate_rule(threshold: float = 0.95) -> AlertRule:
    """Alert when success rate drops below threshold"""
    def condition(metrics: Dict[str, Any]) -> bool:
        success_rate = metrics.get("success_rate", 1.0)
        return success_rate < threshold
    
    return AlertRule(
        name="low_success_rate",
        condition=condition,
        level=AlertLevel.WARNING,
        message_template="Success rate is {success_rate:.2%}, below {threshold} threshold"
    )

