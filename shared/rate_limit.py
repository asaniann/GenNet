"""
Rate limiting middleware for GenNet services
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import os
import redis
import logging

logger = logging.getLogger(__name__)

# Redis connection for rate limiting (optional - falls back to in-memory)
_rate_limit_redis: redis.Redis = None

def get_rate_limit_redis():
    """Get Redis client for distributed rate limiting"""
    global _rate_limit_redis
    
    if _rate_limit_redis is not None:
        return _rate_limit_redis
    
    try:
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_RATE_LIMIT_DB', '3'))  # Use DB 3 for rate limiting
        
        _rate_limit_redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=2
        )
        _rate_limit_redis.ping()
        logger.info("Redis connected for rate limiting")
        return _rate_limit_redis
    except Exception as e:
        logger.warning(f"Redis not available for rate limiting, using in-memory: {e}")
        return None


def get_limiter_key_func(request: Request) -> str:
    """Get rate limiting key - uses user ID if authenticated, else IP address"""
    # Try to get user ID from request headers (set by auth middleware)
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_limiter_key_func,
    storage_uri=get_rate_limit_redis().connection_pool.connection_kwargs.get("host") if get_rate_limit_redis() else None,
    default_limits=["1000/hour", "100/minute"]  # Default limits
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests"""
    
    def __init__(self, app: ASGIApp, default_limit: str = "100/minute"):
        super().__init__(app)
        self.default_limit = default_limit
        self.skip_paths = ["/health", "/health/live", "/health/ready", "/metrics", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks and metrics
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            return await call_next(request)
        
        # Check rate limit
        try:
            # Use limiter to check rate limit
            # This is a simplified check - actual implementation would use slowapi's limiter
            # For now, we'll implement a basic version
            pass  # Rate limiting logic would go here
        except RateLimitExceeded:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        return await call_next(request)


def create_rate_limit_decorator(limit: str):
    """
    Create a rate limit decorator for specific endpoints
    
    Usage:
        @app.get("/networks")
        @limiter.limit("10/minute")
        async def list_networks(request: Request):
            ...
    """
    def decorator(func):
        # Apply rate limit using slowapi's limiter
        return limiter.limit(limit)(func)
    return decorator


