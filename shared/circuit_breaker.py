"""
Circuit Breaker Implementation
Provides resilience patterns for service calls
"""

import logging
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half-open
    timeout: float = 60.0  # Time in seconds before attempting half-open
    expected_exception: type = Exception  # Exception type to catch


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    state: CircuitState = CircuitState.CLOSED
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """Circuit breaker for resilient service calls"""
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self.lock = Lock()
        logger.info(f"Circuit breaker '{name}' initialized")
    
    def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if circuit is closed/half-open
        """
        with self.lock:
            self._update_state()
            
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    async def call_async(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute async function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if circuit is closed/half-open
        """
        with self.lock:
            self._update_state()
            
            if self.stats.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN"
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _update_state(self):
        """Update circuit breaker state based on current conditions"""
        current_time = time.time()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if timeout has passed
            if (self.stats.last_failure_time and
                current_time - self.stats.last_failure_time >= self.config.timeout):
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.successes = 0
                logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN")
    
    def _on_success(self):
        """Handle successful call"""
        with self.lock:
            self.stats.total_requests += 1
            self.stats.total_successes += 1
            
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.successes += 1
                if self.stats.successes >= self.config.success_threshold:
                    self.stats.state = CircuitState.CLOSED
                    self.stats.failures = 0
                    logger.info(f"Circuit breaker '{self.name}' moved to CLOSED")
            elif self.stats.state == CircuitState.CLOSED:
                # Reset failure count on success
                self.stats.failures = 0
    
    def _on_failure(self):
        """Handle failed call"""
        with self.lock:
            self.stats.total_requests += 1
            self.stats.total_failures += 1
            self.stats.failures += 1
            self.stats.last_failure_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Immediately open on failure in half-open
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN (failure in HALF_OPEN)")
            elif (self.stats.state == CircuitState.CLOSED and
                  self.stats.failures >= self.config.failure_threshold):
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' moved to OPEN ({self.stats.failures} failures)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            return {
                "name": self.name,
                "state": self.stats.state.value,
                "failures": self.stats.failures,
                "successes": self.stats.successes,
                "total_requests": self.stats.total_requests,
                "total_failures": self.stats.total_failures,
                "total_successes": self.stats.total_successes,
                "failure_rate": (
                    self.stats.total_failures / self.stats.total_requests
                    if self.stats.total_requests > 0 else 0.0
                )
            }
    
    def reset(self):
        """Reset circuit breaker to closed state"""
        with self.lock:
            self.stats.state = CircuitState.CLOSED
            self.stats.failures = 0
            self.stats.successes = 0
            self.stats.last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' reset")


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """Get or create a circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, config)
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for circuit breaker protection
    
    Usage:
        @circuit_breaker("database", CircuitBreakerConfig(failure_threshold=5))
        def query_database():
            # Database query
            pass
    
    Args:
        name: Circuit breaker name
        config: Optional circuit breaker configuration
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        cb = get_circuit_breaker(name, config)
        
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await cb.call_async(func, *args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return cb.call(func, *args, **kwargs)
            return sync_wrapper
    
    return decorator


import asyncio
