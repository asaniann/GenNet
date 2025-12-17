"""
Retry Logic Implementation
Provides configurable retry strategies for resilient service calls
"""

import logging
import time
import random
from enum import Enum
from typing import Callable, Any, Optional, List, Type
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)


class RetryStrategy(str, Enum):
    """Retry strategies"""
    FIXED = "fixed"           # Fixed delay between retries
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"          # Linear backoff
    RANDOM = "random"          # Random jitter


class RetryConfig:
    """Retry configuration"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        if attempt == 0:
            return 0.0
        
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.backoff_multiplier ** (attempt - 1))
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        elif self.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(0, self.initial_delay * attempt)
        else:
            delay = self.initial_delay
        
        # Apply jitter
        if self.jitter:
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        # Cap at max delay
        delay = min(delay, self.max_delay)
        
        return max(0.0, delay)


def retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry decorator
    
    Usage:
        @retry(RetryConfig(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL))
        def unreliable_function():
            # Function that may fail
            pass
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except tuple(config.retryable_exceptions) as e:
                        last_exception = e
                        
                        if attempt < config.max_attempts - 1:
                            delay = config.calculate_delay(attempt)
                            
                            if on_retry:
                                on_retry(e, attempt + 1)
                            
                            logger.warning(
                                f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                                f"after {delay:.2f}s: {e}"
                            )
                            
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"All {config.max_attempts} attempts failed for {func.__name__}"
                            )
                            raise
                    except Exception as e:
                        # Non-retryable exception
                        raise
                
                if last_exception:
                    raise last_exception
                
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None
                
                for attempt in range(config.max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except tuple(config.retryable_exceptions) as e:
                        last_exception = e
                        
                        if attempt < config.max_attempts - 1:
                            delay = config.calculate_delay(attempt)
                            
                            if on_retry:
                                on_retry(e, attempt + 1)
                            
                            logger.warning(
                                f"Retry {attempt + 1}/{config.max_attempts} for {func.__name__} "
                                f"after {delay:.2f}s: {e}"
                            )
                            
                            time.sleep(delay)
                        else:
                            logger.error(
                                f"All {config.max_attempts} attempts failed for {func.__name__}"
                            )
                            raise
                    except Exception as e:
                        # Non-retryable exception
                        raise
                
                if last_exception:
                    raise last_exception
            
            return sync_wrapper
    
    return decorator


# Pre-configured retry configs
QUICK_RETRY = RetryConfig(
    max_attempts=3,
    initial_delay=0.5,
    strategy=RetryStrategy.FIXED
)

STANDARD_RETRY = RetryConfig(
    max_attempts=5,
    initial_delay=1.0,
    strategy=RetryStrategy.EXPONENTIAL
)

AGGRESSIVE_RETRY = RetryConfig(
    max_attempts=10,
    initial_delay=2.0,
    max_delay=120.0,
    strategy=RetryStrategy.EXPONENTIAL,
    backoff_multiplier=2.0
)

