"""
Application Performance Monitoring (APM) Integration
Supports Datadog, New Relic, and Elastic APM
"""

import logging
import os
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class APMProvider(str, Enum):
    """APM provider types"""
    DATADOG = "datadog"
    NEW_RELIC = "newrelic"
    ELASTIC = "elastic"
    NONE = "none"


class APMClient:
    """APM client for application performance monitoring"""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("APM_PROVIDER", "none")
        self.enabled = self.provider != "none"
        
        if self.enabled:
            self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize APM provider"""
        try:
            if self.provider == APMProvider.DATADOG:
                self._init_datadog()
            elif self.provider == APMProvider.NEW_RELIC:
                self._init_newrelic()
            elif self.provider == APMProvider.ELASTIC:
                self._init_elastic()
        except Exception as e:
            logger.warning(f"Failed to initialize APM provider {self.provider}: {e}")
            self.enabled = False
    
    def _init_datadog(self):
        """Initialize Datadog APM"""
        try:
            from ddtrace import patch_all, tracer
            patch_all()
            self.tracer = tracer
            logger.info("Datadog APM initialized")
        except ImportError:
            logger.warning("Datadog APM not available (ddtrace not installed)")
            self.enabled = False
    
    def _init_newrelic(self):
        """Initialize New Relic APM"""
        try:
            import newrelic.agent
            newrelic.agent.initialize()
            self.agent = newrelic.agent
            logger.info("New Relic APM initialized")
        except ImportError:
            logger.warning("New Relic APM not available (newrelic not installed)")
            self.enabled = False
    
    def _init_elastic(self):
        """Initialize Elastic APM"""
        try:
            from elasticapm import Client
            self.client = Client({
                'SERVICE_NAME': os.getenv("SERVICE_NAME", "gennet-service"),
                'SERVER_URL': os.getenv("ELASTIC_APM_SERVER_URL", "http://apm-server:8200"),
                'ENVIRONMENT': os.getenv("ENVIRONMENT", "production")
            })
            logger.info("Elastic APM initialized")
        except ImportError:
            logger.warning("Elastic APM not available (elasticapm not installed)")
            self.enabled = False
    
    def start_transaction(self, name: str, transaction_type: str = "request") -> Any:
        """Start an APM transaction"""
        if not self.enabled:
            return None
        
        try:
            if self.provider == APMProvider.DATADOG:
                return self.tracer.trace(name, service=os.getenv("SERVICE_NAME", "gennet"))
            elif self.provider == APMProvider.NEW_RELIC:
                return self.agent.current_transaction()
            elif self.provider == APMProvider.ELASTIC:
                return self.client.begin_transaction(transaction_type)
        except Exception as e:
            logger.warning(f"Failed to start APM transaction: {e}")
            return None
    
    def end_transaction(self, transaction: Any, result: str = "success"):
        """End an APM transaction"""
        if not self.enabled or transaction is None:
            return
        
        try:
            if self.provider == APMProvider.DATADOG:
                transaction.finish()
            elif self.provider == APMProvider.NEW_RELIC:
                pass  # New Relic handles this automatically
            elif self.provider == APMProvider.ELASTIC:
                self.client.end_transaction(name=result, result=result)
        except Exception as e:
            logger.warning(f"Failed to end APM transaction: {e}")
    
    def add_custom_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add custom metric"""
        if not self.enabled:
            return
        
        try:
            if self.provider == APMProvider.DATADOG:
                from ddtrace import statsd
                statsd.increment(name, value, tags=[f"{k}:{v}" for k, v in (tags or {}).items()])
            elif self.provider == APMProvider.NEW_RELIC:
                self.agent.record_custom_metric(name, value)
            elif self.provider == APMProvider.ELASTIC:
                self.client.metrics.collect(name, value, tags=tags or {})
        except Exception as e:
            logger.warning(f"Failed to add custom metric: {e}")
    
    def capture_exception(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Capture exception in APM"""
        if not self.enabled:
            return
        
        try:
            if self.provider == APMProvider.DATADOG:
                self.tracer.current_span().set_exc_info(
                    type(exception),
                    exception,
                    exception.__traceback__
                )
            elif self.provider == APMProvider.NEW_RELIC:
                self.agent.record_exception()
            elif self.provider == APMProvider.ELASTIC:
                self.client.capture_exception(exc_info=(type(exception), exception, exception.__traceback__))
        except Exception as e:
            logger.warning(f"Failed to capture exception: {e}")


# Global APM client instance
_apm_client: Optional[APMClient] = None


def get_apm_client() -> APMClient:
    """Get global APM client instance"""
    global _apm_client
    if _apm_client is None:
        _apm_client = APMClient()
    return _apm_client

