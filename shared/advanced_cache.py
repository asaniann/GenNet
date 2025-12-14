"""
Advanced caching strategies with TTL, invalidation, and cache warming
"""
import json
import hashlib
import time
from typing import Callable, Any, Optional, Dict, List, Set
from functools import wraps
from datetime import datetime, timedelta
import logging
import asyncio

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheStrategy:
    """Cache strategy enumeration"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


class AdvancedCache:
    """
    Advanced caching with multiple strategies and features
    
    Features:
    - TTL-based expiration
    - Cache warming
    - Pattern-based invalidation
    - Cache statistics
    - Multiple eviction strategies
    """
    
    def __init__(
        self,
        redis_client: Optional[Any] = None,
        default_ttl: int = 300,
        max_size: int = 10000,
        strategy: CacheStrategy = CacheStrategy.LRU
    ):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.strategy = strategy
        
        # In-memory cache if Redis not available
        if not self.redis_client:
            self._memory_cache: Dict[str, Dict[str, Any]] = {}
            self._access_times: Dict[str, float] = {}  # For LRU
            self._access_counts: Dict[str, int] = defaultdict(int)  # For LFU
            self._insertion_order: List[str] = []  # For FIFO
        
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key"""
        # Filter out non-serializable args
        key_data = {
            "args": [str(arg) for arg in args if isinstance(arg, (str, int, float, bool, type(None)))],
            "kwargs": {k: str(v) for k, v in kwargs.items() if isinstance(v, (str, int, float, bool, type(None)))}
        }
        key_str = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.stats["hits"] += 1
                    return json.loads(value)
                self.stats["misses"] += 1
                return None
            except Exception as e:
                logger.error(f"Redis cache get error: {e}")
                self.stats["misses"] += 1
                return None
        else:
            # In-memory cache
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                # Check TTL
                if entry.get("expires_at", float('inf')) > time.time():
                    self.stats["hits"] += 1
                    # Update access tracking
                    self._access_times[key] = time.time()
                    self._access_counts[key] += 1
                    return entry["value"]
                else:
                    # Expired
                    del self._memory_cache[key]
            
            self.stats["misses"] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
                self.stats["sets"] += 1
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
        else:
            # In-memory cache
            # Check if we need to evict
            if len(self._memory_cache) >= self.max_size and key not in self._memory_cache:
                self._evict()
            
            self._memory_cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
                "created_at": time.time()
            }
            self._access_times[key] = time.time()
            self._access_counts[key] = 0
            if key not in self._insertion_order:
                self._insertion_order.append(key)
            
            self.stats["sets"] += 1
    
    def delete(self, key: str):
        """Delete key from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
                self.stats["deletes"] += 1
            except Exception as e:
                logger.error(f"Redis cache delete error: {e}")
        else:
            if key in self._memory_cache:
                del self._memory_cache[key]
                self._access_times.pop(key, None)
                self._access_counts.pop(key, None)
                if key in self._insertion_order:
                    self._insertion_order.remove(key)
                self.stats["deletes"] += 1
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if self.redis_client:
            try:
                keys = list(self.redis_client.scan_iter(match=pattern))
                if keys:
                    self.redis_client.delete(*keys)
                    self.stats["deletes"] += len(keys)
            except Exception as e:
                logger.error(f"Redis cache delete_pattern error: {e}")
        else:
            # In-memory pattern matching
            keys_to_delete = [k for k in self._memory_cache.keys() if pattern.replace("*", "") in k]
            for key in keys_to_delete:
                self.delete(key)
    
    def _evict(self):
        """Evict entry based on strategy"""
        if not self._memory_cache:
            return
        
        if self.strategy == CacheStrategy.LRU:
            # Evict least recently used
            key_to_evict = min(self._access_times.items(), key=lambda x: x[1])[0]
        elif self.strategy == CacheStrategy.LFU:
            # Evict least frequently used
            key_to_evict = min(self._access_counts.items(), key=lambda x: x[1])[0]
        elif self.strategy == CacheStrategy.FIFO:
            # Evict first inserted
            key_to_evict = self._insertion_order[0]
        else:
            # Default: random
            key_to_evict = next(iter(self._memory_cache))
        
        self.delete(key_to_evict)
        self.stats["evictions"] += 1
    
    def warm_cache(self, func: Callable, *args, **kwargs):
        """Pre-populate cache by calling function"""
        key = self._make_key(func.__name__, *args, **kwargs)
        if not self.get(key):
            try:
                result = func(*args, **kwargs)
                self.set(key, result)
                logger.info(f"Cache warmed for {func.__name__}")
            except Exception as e:
                logger.error(f"Cache warming failed for {func.__name__}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        stats = {
            **self.stats,
            "hit_rate": hit_rate,
            "size": len(self._memory_cache) if not self.redis_client else None
        }
        
        return stats


def cached(
    ttl: int = 300,
    key_prefix: str = "cache",
    strategy: CacheStrategy = CacheStrategy.LRU,
    cache_instance: Optional[AdvancedCache] = None,
    invalidate_on: Optional[List[str]] = None
):
    """
    Advanced caching decorator
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        strategy: Cache eviction strategy
        cache_instance: Custom cache instance (optional)
        invalidate_on: List of parameter names that invalidate cache
    
    Usage:
        @cached(ttl=600, key_prefix="networks")
        async def get_network(network_id: str):
            ...
    """
    cache = cache_instance or AdvancedCache(default_ttl=ttl, strategy=strategy)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check for invalidation conditions
            if invalidate_on:
                for param_name in invalidate_on:
                    if param_name in kwargs and kwargs[param_name] is None:
                        # Invalidate cache
                        pattern = f"{key_prefix}:{func.__name__}:*"
                        cache.delete_pattern(pattern)
                        # Execute function without cache
                        return await func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache._make_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check for invalidation conditions
            if invalidate_on:
                for param_name in invalidate_on:
                    if param_name in kwargs and kwargs[param_name] is None:
                        # Invalidate cache
                        pattern = f"{key_prefix}:{func.__name__}:*"
                        cache.delete_pattern(pattern)
                        # Execute function without cache
                        return func(*args, **kwargs)
            
            # Generate cache key
            cache_key = cache._make_key(f"{key_prefix}:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Attach cache instance and helper methods
        import asyncio
        if asyncio.iscoroutinefunction(func):
            async_wrapper.cache = cache
            async_wrapper.invalidate = lambda pattern: cache.delete_pattern(f"{key_prefix}:{func.__name__}:{pattern}")
            return async_wrapper
        else:
            sync_wrapper.cache = cache
            sync_wrapper.invalidate = lambda pattern: cache.delete_pattern(f"{key_prefix}:{func.__name__}:{pattern}")
            return sync_wrapper
    
    return decorator


# Global cache instance
_advanced_cache: Optional[AdvancedCache] = None


def get_advanced_cache(redis_client: Optional[Any] = None) -> AdvancedCache:
    """Get or create global advanced cache instance"""
    global _advanced_cache
    if _advanced_cache is None:
        _advanced_cache = AdvancedCache(redis_client=redis_client)
    return _advanced_cache


from collections import defaultdict

