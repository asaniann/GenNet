"""
Prometheus metrics for GenNet services
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
from typing import Callable

# HTTP request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Business metrics (can be customized per service)
networks_created_total = Counter(
    'grn_networks_created_total',
    'Total number of GRN networks created'
)

workflows_executed_total = Counter(
    'workflows_executed_total',
    'Total number of workflows executed',
    ['workflow_type', 'status']
)

users_registered_total = Counter(
    'users_registered_total',
    'Total number of users registered'
)

# Gauge for active connections, jobs, etc.
active_connections = Gauge(
    'active_connections',
    'Number of active connections'
)

active_workflows = Gauge(
    'active_workflows',
    'Number of active workflows',
    ['status']
)

# Business metrics for personalized health
predictions_generated_total = Counter(
    'health_predictions_generated_total',
    'Total number of health predictions generated',
    ['prediction_type', 'method']
)

patient_grns_built_total = Counter(
    'patient_grns_built_total',
    'Total number of patient-specific GRNs built',
    ['method']
)

explanations_generated_total = Counter(
    'explanations_generated_total',
    'Total number of explanations generated',
    ['method']
)

reports_generated_total = Counter(
    'health_reports_generated_total',
    'Total number of health reports generated',
    ['format']
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP metrics for Prometheus"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint
        if request.url.path == "/metrics":
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Extract endpoint pattern (simplify path parameters)
            endpoint = self._normalize_path(request.url.path)
            
            # Track metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=response.status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            # Track errors too
            duration = time.time() - start_time
            endpoint = self._normalize_path(request.url.path)
            
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=500
            ).inc()
            
            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
    
    def _normalize_path(self, path: str) -> str:
        """Normalize path by replacing IDs with placeholders"""
        # Replace UUIDs and numeric IDs with placeholders
        import re
        # Replace UUIDs
        path = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '{id}', path)
        # Replace numeric IDs at end of path segments
        path = re.sub(r'/\d+', '/{id}', path)
        # Replace query parameters
        if '?' in path:
            path = path.split('?')[0]
        return path or '/'


def get_metrics_response() -> Response:
    """Get Prometheus metrics endpoint response"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

