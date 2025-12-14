"""
Circuit Breaker pattern implementation for resilient service communication
"""
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation to prevent cascading failures
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery (half-open)
        expected_exception: Exception type that indicates failure (default: Exception)
        name: Name of the circuit breaker (for logging)
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        name: str = "circuit_breaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of func execution
        
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If func raises an exception
        """
        async with self._lock:
            # Check if we should attempt recovery
            if self.state == CircuitState.OPEN:
                if time.time() - (self.last_failure_time or 0) >= self.recovery_timeout:
                    logger.info(f"Circuit breaker {self.name}: Attempting recovery (half-open)")
                    self.state = CircuitState.HALF_OPEN
                    self.failure_count = 0
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Service unavailable. Retry after {self.recovery_timeout}s"
                    )
        
        # Execute the function
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset failure count and close circuit if it was half-open
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"Circuit breaker {self.name}: Service recovered, closing circuit")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                elif self.failure_count > 0:
                    # Reset failure count on success
                    self.failure_count = 0
            
            return result
        
        except self.expected_exception as e:
            # Failure - increment counter
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                logger.warning(
                    f"Circuit breaker {self.name}: Failure {self.failure_count}/{self.failure_threshold}. "
                    f"Error: {str(e)}"
                )
                
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        f"Circuit breaker {self.name}: Threshold reached. Opening circuit for {self.recovery_timeout}s"
                    )
                    self.state = CircuitState.OPEN
                    self.last_failure_time = time.time()
            
            raise
    
    def reset(self):
        """Manually reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name}: Manually reset")


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: type = Exception,
    name: Optional[str] = None
):
    """
    Decorator to apply circuit breaker pattern to a function
    
    Usage:
        @circuit_breaker(failure_threshold=5, recovery_timeout=60)
        async def call_external_service():
            # Service call
            pass
    """
    def decorator(func: Callable) -> Callable:
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=cb_name
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Attach breaker instance for monitoring
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Global circuit breakers for common services
_service_breakers: dict[str, CircuitBreaker] = {}


def get_service_circuit_breaker(service_name: str, **kwargs) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a named service
    
    Args:
        service_name: Name of the service
        **kwargs: Additional arguments for CircuitBreaker
    
    Returns:
        CircuitBreaker instance
    """
    if service_name not in _service_breakers:
        _service_breakers[service_name] = CircuitBreaker(
            name=service_name,
            **kwargs
        )
    return _service_breakers[service_name]

