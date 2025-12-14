"""
Shared logging middleware with correlation IDs
"""
import logging
import uuid
from contextvars import ContextVar
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='')

# Configure structured logger
class StructuredLogger(logging.LoggerAdapter):
    """Logger adapter that includes request ID in log messages"""
    
    def process(self, msg, kwargs):
        request_id = request_id_var.get('')
        if request_id:
            msg = f"[{request_id}] {msg}"
        return msg, kwargs

def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger with request ID support"""
    logger = logging.getLogger(name)
    return StructuredLogger(logger, {})


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to requests and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Store in context variable
        request_id_var.set(correlation_id)
        
        # Log request start
        start_time = time.time()
        logger = get_logger(__name__)
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Request-ID"] = correlation_id
            
            # Log request completion
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                }
            )
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "duration_seconds": round(duration, 3),
                },
                exc_info=True
            )
            raise

