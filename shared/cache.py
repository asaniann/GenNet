"""
Redis caching utilities for GenNet services
"""
import json
import hashlib
import functools
from typing import Any, Optional, Callable
import redis
import os
import logging

logger = logging.getLogger(__name__)

# Redis client singleton
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client"""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_db = int(os.getenv('REDIS_CACHE_DB', '2'))  # Use DB 2 for caching
        
        _redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        # Test connection
        _redis_client.ping()
        logger.info("Redis cache client connected successfully")
        return _redis_client
    except (redis.ConnectionError, redis.TimeoutError, Exception) as e:
        logger.warning(f"Redis cache not available: {e}. Caching disabled.")
        _redis_client = None
        return None


def cache_key(*args, **kwargs) -> str:
    """Generate a cache key from function arguments"""
    key_parts = []
    
    # Add positional arguments
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        elif isinstance(arg, dict):
            key_parts.append(json.dumps(arg, sort_keys=True))
        else:
            key_parts.append(str(arg))
    
    # Add keyword arguments (sorted for consistency)
    for key, value in sorted(kwargs.items()):
        if key in ('db', 'request', 'response', 'background_tasks'):  # Skip non-serializable args
            continue
        if isinstance(value, (str, int, float, bool)):
            key_parts.append(f"{key}={value}")
        elif isinstance(value, dict):
            key_parts.append(f"{key}={json.dumps(value, sort_keys=True)}")
        else:
            key_parts.append(f"{key}={str(value)}")
    
    # Create hash
    key_string = '|'.join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return key_hash


def cached(ttl: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache function results in Redis
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Prefix for cache keys
    
    Usage:
        @cached(ttl=600)
        async def get_network(network_id: str):
            # Expensive operation
            return network_data
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            func_name = func.__name__
            key_hash = cache_key(*args, **kwargs)
            cache_key_str = f"{key_prefix}:{func_name}:{key_hash}"
            
            redis_client = get_redis_client()
            
            # Try to get from cache
            if redis_client:
                try:
                    cached_value = redis_client.get(cache_key_str)
                    if cached_value:
                        logger.debug(f"Cache hit: {cache_key_str}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            if redis_client:
                try:
                    # Serialize result
                    serialized = json.dumps(result, default=str)
                    redis_client.setex(cache_key_str, ttl, serialized)
                    logger.debug(f"Cache set: {cache_key_str} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions
            func_name = func.__name__
            key_hash = cache_key(*args, **kwargs)
            cache_key_str = f"{key_prefix}:{func_name}:{key_hash}"
            
            redis_client = get_redis_client()
            
            # Try to get from cache
            if redis_client:
                try:
                    cached_value = redis_client.get(cache_key_str)
                    if cached_value:
                        logger.debug(f"Cache hit: {cache_key_str}")
                        return json.loads(cached_value)
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            if redis_client:
                try:
                    serialized = json.dumps(result, default=str)
                    redis_client.setex(cache_key_str, ttl, serialized)
                    logger.debug(f"Cache set: {cache_key_str} (TTL: {ttl}s)")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")
            
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache(pattern: str):
    """
    Invalidate cache entries matching a pattern
    
    Args:
        pattern: Cache key pattern (supports wildcards like 'cache:get_network:*')
    
    Usage:
        invalidate_cache("cache:get_network:*")
    """
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        # Find matching keys
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching pattern: {pattern}")
    except Exception as e:
        logger.warning(f"Cache invalidation error: {e}")


def clear_cache(key_prefix: str = "cache"):
    """
    Clear all cache entries with a given prefix
    
    Usage:
        clear_cache("cache:get_network")
    """
    invalidate_cache(f"{key_prefix}*")


def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache by key"""
    redis_client = get_redis_client()
    if not redis_client:
        return None
    
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        logger.warning(f"Cache get error: {e}")
    
    return None


def cache_set(key: str, value: Any, ttl: int = 300):
    """Set a value in cache with TTL"""
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        serialized = json.dumps(value, default=str)
        redis_client.setex(key, ttl, serialized)
    except Exception as e:
        logger.warning(f"Cache set error: {e}")


def cache_delete(key: str):
    """Delete a value from cache"""
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    try:
        redis_client.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete error: {e}")

