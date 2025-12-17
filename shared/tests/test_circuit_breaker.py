"""
Tests for Circuit Breaker Implementation
"""

import pytest
import time
from unittest.mock import Mock, patch
from shared.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    get_circuit_breaker,
    circuit_breaker
)


class TestCircuitBreaker:
    """Test CircuitBreaker class"""
    
    def test_initialization(self):
        """Test circuit breaker initialization"""
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        assert cb.name == "test"
        assert cb.stats.state.value == "closed"
        assert cb.stats.failures == 0
    
    def test_successful_call(self):
        """Test successful function call"""
        cb = CircuitBreaker("test")
        
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.stats.state.value == "closed"
        assert cb.stats.total_successes == 1
    
    def test_failed_call_closed_state(self):
        """Test failed call in closed state"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
        
        def fail_func():
            raise ValueError("Test error")
        
        # First failure
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.stats.failures == 1
        assert cb.stats.state.value == "closed"
        
        # Second failure - should open circuit
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.stats.failures == 2
        assert cb.stats.state.value == "open"
    
    def test_open_circuit_rejects_requests(self):
        """Test that open circuit rejects requests"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        
        def fail_func():
            raise ValueError("Test error")
        
        # Cause circuit to open
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(fail_func)
    
    def test_half_open_state(self):
        """Test half-open state transition"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(
            failure_threshold=1,
            timeout=0.1,
            success_threshold=2
        ))
        
        def fail_func():
            raise ValueError("Test error")
        
        # Open circuit
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.stats.state.value == "open"
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Update state (should move to half-open)
        cb._update_state()
        assert cb.stats.state.value == "half_open"
        
        # Successful call
        def success_func():
            return "success"
        
        result = cb.call(success_func)
        assert result == "success"
        assert cb.stats.successes == 1
        
        # Second success should close circuit
        result = cb.call(success_func)
        assert result == "success"
        assert cb.stats.state.value == "closed"
    
    def test_async_call(self):
        """Test async function call"""
        import asyncio
        
        cb = CircuitBreaker("test")
        
        async def async_func():
            return "async success"
        
        result = asyncio.run(cb.call_async(async_func))
        assert result == "async success"
    
    def test_get_stats(self):
        """Test getting circuit breaker statistics"""
        cb = CircuitBreaker("test")
        
        def success_func():
            return "success"
        
        cb.call(success_func)
        stats = cb.get_stats()
        
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert stats["total_requests"] == 1
        assert stats["total_successes"] == 1
        assert stats["failure_rate"] == 0.0
    
    def test_reset(self):
        """Test resetting circuit breaker"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        
        def fail_func():
            raise ValueError("Test error")
        
        # Open circuit
        with pytest.raises(ValueError):
            cb.call(fail_func)
        
        assert cb.stats.state.value == "open"
        
        # Reset
        cb.reset()
        assert cb.stats.state.value == "closed"
        assert cb.stats.failures == 0


class TestCircuitBreakerDecorator:
    """Test circuit breaker decorator"""
    
    def test_decorator_sync(self):
        """Test decorator with sync function"""
        @circuit_breaker("test", CircuitBreakerConfig(failure_threshold=2))
        def test_func():
            return "success"
        
        result = test_func()
        assert result == "success"
    
    def test_decorator_async(self):
        """Test decorator with async function"""
        import asyncio
        
        @circuit_breaker("test")
        async def async_test_func():
            return "async success"
        
        result = asyncio.run(async_test_func())
        assert result == "async success"


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry"""
    
    def test_get_circuit_breaker(self):
        """Test getting circuit breaker from registry"""
        cb1 = get_circuit_breaker("test1")
        cb2 = get_circuit_breaker("test1")
        
        assert cb1 is cb2  # Should be same instance
    
    def test_different_names(self):
        """Test different names get different instances"""
        cb1 = get_circuit_breaker("test1")
        cb2 = get_circuit_breaker("test2")
        
        assert cb1 is not cb2

