"""
Tests for Caching Implementation
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from shared.cache import (
    CacheConfig,
    CacheManager,
    get_cache_manager,
    cached
)
import json


class TestCacheConfig:
    """Test CacheConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = CacheConfig()
        assert config.ttl == 3600
        assert config.key_prefix == "gennet"
        assert config.enable_cache is True
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = CacheConfig(
            ttl=1800,
            key_prefix="test",
            enable_cache=False
        )
        assert config.ttl == 1800
        assert config.key_prefix == "test"
        assert config.enable_cache is False


class TestCacheManager:
    """Test CacheManager class"""
    
    @patch('shared.cache.redis.from_url')
    def test_initialization_with_redis(self, mock_redis):
        """Test initialization with Redis available"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        manager = CacheManager(CacheConfig(redis_url="redis://localhost:6379/0"))
        
        assert manager.redis_client is not None
        mock_client.ping.assert_called_once()
    
    @patch('shared.cache.redis.from_url')
    def test_initialization_without_redis(self, mock_redis):
        """Test initialization without Redis"""
        mock_redis.side_effect = ConnectionError("Redis unavailable")
        
        manager = CacheManager(CacheConfig())
        
        assert manager.redis_client is None
    
    @patch('shared.cache.redis.from_url')
    def test_get_cache_hit(self, mock_redis):
        """Test cache get with hit"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = json.dumps({"key": "value"})
        mock_redis.return_value = mock_client
        
        manager = CacheManager()
        result = manager.get("test_key")
        
        assert result == {"key": "value"}
        mock_client.get.assert_called_once_with("gennet:test_key")
    
    @patch('shared.cache.redis.from_url')
    def test_get_cache_miss(self, mock_redis):
        """Test cache get with miss"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_redis.return_value = mock_client
        
        manager = CacheManager()
        result = manager.get("test_key")
        
        assert result is None
    
    @patch('shared.cache.redis.from_url')
    def test_set_cache(self, mock_redis):
        """Test cache set"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        manager = CacheManager()
        result = manager.set("test_key", {"key": "value"}, ttl=1800)
        
        assert result is True
        mock_client.setex.assert_called_once()
        call_args = mock_client.setex.call_args
        assert call_args[0][0] == "gennet:test_key"
        assert call_args[0][1] == 1800
    
    @patch('shared.cache.redis.from_url')
    def test_delete_cache(self, mock_redis):
        """Test cache delete"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis.return_value = mock_client
        
        manager = CacheManager()
        result = manager.delete("test_key")
        
        assert result is True
        mock_client.delete.assert_called_once_with("gennet:test_key")
    
    @patch('shared.cache.redis.from_url')
    def test_invalidate_pattern(self, mock_redis):
        """Test cache invalidation by pattern"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = ["gennet:key1", "gennet:key2"]
        mock_client.delete.return_value = 2
        mock_redis.return_value = mock_client
        
        manager = CacheManager()
        result = manager.invalidate_pattern("key*")
        
        assert result == 2
        mock_client.keys.assert_called_once_with("gennet:key*")
        mock_client.delete.assert_called_once_with("gennet:key1", "gennet:key2")
    
    def test_cache_disabled(self):
        """Test cache operations when disabled"""
        manager = CacheManager(CacheConfig(enable_cache=False))
        
        assert manager.get("key") is None
        assert manager.set("key", "value") is False
        assert manager.delete("key") is False


class TestCachedDecorator:
    """Test cached decorator"""
    
    @patch('shared.cache.get_cache_manager')
    def test_cached_decorator_hit(self, mock_get_manager):
        """Test cached decorator with cache hit"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = "cached_value"
        mock_get_manager.return_value = mock_manager
        
        call_count = 0
        
        @cached(ttl=3600)
        def expensive_func(arg1, arg2):
            nonlocal call_count
            call_count += 1
            return f"result_{arg1}_{arg2}"
        
        result = expensive_func("a", "b")
        
        assert result == "cached_value"
        assert call_count == 0  # Function not called
        mock_manager.get.assert_called_once()
    
    @patch('shared.cache.get_cache_manager')
    def test_cached_decorator_miss(self, mock_get_manager):
        """Test cached decorator with cache miss"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_manager.set.return_value = True
        mock_get_manager.return_value = mock_manager
        
        call_count = 0
        
        @cached(ttl=3600)
        def expensive_func(arg1):
            nonlocal call_count
            call_count += 1
            return f"result_{arg1}"
        
        result = expensive_func("test")
        
        assert result == "result_test"
        assert call_count == 1  # Function called once
        mock_manager.get.assert_called_once()
        mock_manager.set.assert_called_once()
    
    @patch('shared.cache.get_cache_manager')
    def test_cached_decorator_with_key_func(self, mock_get_manager):
        """Test cached decorator with custom key function"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_manager.set.return_value = True
        mock_get_manager.return_value = mock_manager
        
        @cached(ttl=3600, key_func=lambda network_id: f"network:{network_id}")
        def get_network(network_id: str):
            return {"id": network_id}
        
        result = get_network("net-123")
        
        assert result == {"id": "net-123"}
        # Check that key function was used
        call_args = mock_manager.get.call_args[0][0]
        assert "network:net-123" in call_args or call_args == "network:net-123"
    
    @patch('shared.cache.get_cache_manager')
    def test_cached_decorator_async(self, mock_get_manager):
        """Test cached decorator with async function"""
        import asyncio
        
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_manager.set.return_value = True
        mock_get_manager.return_value = mock_manager
        
        call_count = 0
        
        @cached(ttl=3600)
        async def async_expensive_func(arg):
            nonlocal call_count
            call_count += 1
            return f"async_result_{arg}"
        
        result = asyncio.run(async_expensive_func("test"))
        
        assert result == "async_result_test"
        assert call_count == 1
        mock_manager.set.assert_called_once()


class TestCacheManagerGlobal:
    """Test global cache manager"""
    
    def test_get_cache_manager_singleton(self):
        """Test that get_cache_manager returns singleton"""
        # Reset global state
        import shared.cache
        shared.cache._cache_manager = None
        
        manager1 = get_cache_manager()
        manager2 = get_cache_manager()
        
        assert manager1 is manager2

