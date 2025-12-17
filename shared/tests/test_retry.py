"""
Tests for Retry Logic Implementation
"""

import pytest
import time
from unittest.mock import Mock, patch
from shared.retry import (
    RetryConfig,
    RetryStrategy,
    retry,
    QUICK_RETRY,
    STANDARD_RETRY,
    AGGRESSIVE_RETRY
)


class TestRetryConfig:
    """Test RetryConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.strategy == RetryStrategy.EXPONENTIAL
    
    def test_calculate_delay_fixed(self):
        """Test fixed delay calculation"""
        config = RetryConfig(strategy=RetryStrategy.FIXED, initial_delay=2.0)
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 2.0
    
    def test_calculate_delay_exponential(self):
        """Test exponential delay calculation"""
        config = RetryConfig(
            strategy=RetryStrategy.EXPONENTIAL,
            initial_delay=1.0,
            backoff_multiplier=2.0
        )
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 4.0
    
    def test_calculate_delay_linear(self):
        """Test linear delay calculation"""
        config = RetryConfig(strategy=RetryStrategy.LINEAR, initial_delay=1.0)
        assert config.calculate_delay(1) == 1.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(3) == 3.0
    
    def test_calculate_delay_max_limit(self):
        """Test max delay limit"""
        config = RetryConfig(initial_delay=100.0, max_delay=10.0)
        delay = config.calculate_delay(1)
        assert delay <= 10.0


class TestRetryDecorator:
    """Test retry decorator"""
    
    def test_successful_call_no_retry(self):
        """Test successful call doesn't retry"""
        call_count = 0
        
        @retry(RetryConfig(max_attempts=3))
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = success_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_on_failure(self):
        """Test retry on failure"""
        call_count = 0
        
        @retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = fail_then_succeed()
        assert result == "success"
        assert call_count == 2
    
    def test_max_attempts_exceeded(self):
        """Test max attempts exceeded"""
        call_count = 0
        
        @retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_fail()
        
        assert call_count == 3
    
    def test_retry_strategy_exponential(self):
        """Test exponential retry strategy"""
        delays = []
        
        def record_delay(exception, attempt):
            delays.append(time.time())
        
        call_count = 0
        
        @retry(
            RetryConfig(
                max_attempts=3,
                initial_delay=0.1,
                strategy=RetryStrategy.EXPONENTIAL,
                backoff_multiplier=2.0
            ),
            on_retry=record_delay
        )
        def fail_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Fail")
            return "success"
        
        start = time.time()
        result = fail_func()
        end = time.time()
        
        assert result == "success"
        # Should have retried twice with exponential backoff
        assert len(delays) == 2
        # Total time should be at least 0.1 + 0.2 = 0.3 seconds
        assert (end - start) >= 0.2
    
    def test_async_retry(self):
        """Test async retry"""
        import asyncio
        
        call_count = 0
        
        @retry(RetryConfig(max_attempts=3, initial_delay=0.01))
        async def async_fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "async success"
        
        result = asyncio.run(async_fail_then_succeed())
        assert result == "async success"
        assert call_count == 2
    
    def test_retryable_exceptions(self):
        """Test retryable exceptions filtering"""
        call_count = 0
        
        @retry(RetryConfig(
            max_attempts=3,
            initial_delay=0.01,
            retryable_exceptions=[ValueError]
        ))
        def fail_with_different_exception():
            nonlocal call_count
            call_count += 1
            raise TypeError("Non-retryable")
        
        # Should not retry on TypeError
        with pytest.raises(TypeError):
            fail_with_different_exception()
        
        assert call_count == 1  # Only called once, no retries


class TestPreconfiguredRetryConfigs:
    """Test pre-configured retry configs"""
    
    def test_quick_retry(self):
        """Test QUICK_RETRY config"""
        assert QUICK_RETRY.max_attempts == 3
        assert QUICK_RETRY.strategy == RetryStrategy.FIXED
    
    def test_standard_retry(self):
        """Test STANDARD_RETRY config"""
        assert STANDARD_RETRY.max_attempts == 5
        assert STANDARD_RETRY.strategy == RetryStrategy.EXPONENTIAL
    
    def test_aggressive_retry(self):
        """Test AGGRESSIVE_RETRY config"""
        assert AGGRESSIVE_RETRY.max_attempts == 10
        assert AGGRESSIVE_RETRY.max_delay == 120.0

