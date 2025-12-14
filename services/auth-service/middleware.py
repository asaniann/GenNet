"""
Security middleware for audit logging
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from datetime import datetime

logger = logging.getLogger("audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for audit logging"""
    
    async def dispatch(self, request: Request, call_next):
        # Log request
        start_time = datetime.utcnow()
        user_id = request.headers.get("X-User-Id", "anonymous")
        
        response = await call_next(request)
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Audit log entry
        log_entry = {
            "timestamp": start_time.isoformat(),
            "user_id": user_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_seconds": duration,
            "ip_address": request.client.host if request.client else None
        }
        
        logger.info(f"Audit: {log_entry}")
        
        return response

