"""
Multi-layer Caching Strategy
Provides Redis-based caching with TTL and invalidation
"""

import logging
import json
import hashlib
import asyncio
from typing import Any, Optional, Callable, Dict
from functools import wraps
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CacheConfig:
    """Cache configuration"""
    
    def __init__(
        self,
        ttl: int = 3600,  # 1 hour default
        key_prefix: str = "gennet",
        redis_url: Optional[str] = None,
        enable_cache: bool = True
    ):
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.enable_cache = enable_cache


class CacheManager:
    """Cache manager for Redis-based caching"""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.redis_client = None
        
        if self.config.enable_cache:
            try:
                self.redis_client = redis.from_url(
                    self.config.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected")
            except (RedisError, ConnectionError) as e:
                logger.warning(f"Redis cache not available: {e}")
                self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client or not self.config.enable_cache:
            return None
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            value = self.redis_client.get(full_key)
            
            if value:
                return json.loads(value)
            return None
        except (RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self.redis_client or not self.config.enable_cache:
            return False
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            ttl = ttl or self.config.ttl
            serialized = json.dumps(value)
            
            self.redis_client.setex(full_key, ttl, serialized)
            return True
        except (RedisError, TypeError) as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client or not self.config.enable_cache:
            return False
        
        try:
            full_key = f"{self.config.key_prefix}:{key}"
            self.redis_client.delete(full_key)
            return True
        except RedisError as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern"""
        if not self.redis_client or not self.config.enable_cache:
            return 0
        
        try:
            full_pattern = f"{self.config.key_prefix}:{pattern}"
            keys = self.redis_client.keys(full_pattern)
            
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except RedisError as e:
            logger.warning(f"Cache invalidate error for pattern {pattern}: {e}")
            return 0
    
    def clear(self) -> bool:
        """Clear all cache"""
        if not self.redis_client or not self.config.enable_cache:
            return False
        
        try:
            pattern = f"{self.config.key_prefix}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
            return True
        except RedisError as e:
            logger.warning(f"Cache clear error: {e}")
            return False


# Global cache manager
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    cache_manager: Optional[CacheManager] = None
):
    """
    Caching decorator
    
    Usage:
        @cached(ttl=1800, key_func=lambda network_id: f"network:{network_id}")
        def get_network(network_id: str):
            # Expensive operation
            pass
    """
    if cache_manager is None:
        cache_manager = get_cache_manager()
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash function name and arguments
                key_data = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                key_data = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Cache miss - execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator
