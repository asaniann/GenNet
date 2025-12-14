"""
HTTP client with timeouts, retry logic, and circuit breaker for service-to-service calls
"""
import httpx
import os
import sys
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from typing import Optional, Dict, Any
import logging

# Import circuit breaker
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.circuit_breaker import get_service_circuit_breaker, CircuitBreakerError

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client with retries, timeouts, and circuit breaker for service-to-service calls"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        service_name: Optional[str] = None,
        use_circuit_breaker: bool = True,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries
        self.service_name = service_name or base_url.replace('http://', '').replace('https://', '').split(':')[0]
        self.use_circuit_breaker = use_circuit_breaker
        
        # Initialize circuit breaker if enabled
        if self.use_circuit_breaker:
            self.circuit_breaker = get_service_circuit_breaker(
                self.service_name,
                failure_threshold=circuit_breaker_threshold,
                recovery_timeout=circuit_breaker_timeout,
                expected_exception=(httpx.RequestError, httpx.HTTPStatusError)
            )
    
    def _get_client(self) -> httpx.AsyncClient:
        """Create HTTP client with timeout configuration"""
        timeout = httpx.Timeout(
            timeout=self.timeout,
            connect=self.connect_timeout
        )
        return httpx.AsyncClient(timeout=timeout, base_url=self.base_url)
    
    async def _request_with_retry(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Internal request method with retry logic"""
        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
            reraise=True
        )
        async def _make_request():
            async with self._get_client() as client:
                response = await client.request(method, path, **kwargs)
                response.raise_for_status()
                return response
        
        # Wrap with circuit breaker if enabled
        if self.use_circuit_breaker:
            try:
                return await self.circuit_breaker.call(_make_request)
            except CircuitBreakerError as e:
                logger.error(f"Circuit breaker open for {self.service_name}: {e}")
                raise httpx.HTTPStatusError(
                    message=str(e),
                    request=httpx.Request(method, f"{self.base_url}{path}"),
                    response=httpx.Response(503, text=str(e))
                )
        else:
            return await _make_request()
    
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET request with retries and circuit breaker"""
        response = await self._request_with_retry("GET", path, **kwargs)
        return response.json()
    
    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST request with retries and circuit breaker"""
        response = await self._request_with_retry("POST", path, **kwargs)
        return response.json()
    
    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """PUT request with retries and circuit breaker"""
        response = await self._request_with_retry("PUT", path, **kwargs)
        return response.json()
    
    async def delete(self, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE request with retries and circuit breaker"""
        response = await self._request_with_retry("DELETE", path, **kwargs)
        return response.json()


# Convenience function for quick service calls
async def call_service(
    url: str,
    method: str = "GET",
    timeout: float = 10.0,
    max_retries: int = 3,
    use_circuit_breaker: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to call a service endpoint with retries, timeouts, and circuit breaker
    
    Args:
        url: Full URL to call
        method: HTTP method (GET, POST, PUT, DELETE)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
        use_circuit_breaker: Whether to use circuit breaker
        **kwargs: Additional arguments for httpx request
    
    Returns:
        JSON response as dictionary
    
    Example:
        result = await call_service(
            "http://qualitative-service:8000/ctl/verify",
            method="POST",
            json={"formula": "AG(p)"}
        )
    """
    # Extract base URL and path
    if '://' in url:
        parts = url.split('/', 3)
        base_url = f"{parts[0]}//{parts[2]}"
        path = '/' + parts[3] if len(parts) > 3 else '/'
        service_name = parts[2].split(':')[0]  # Extract service name
    else:
        base_url = url
        path = '/'
        service_name = None
    
    client = ServiceClient(
        base_url=base_url,
        timeout=timeout,
        max_retries=max_retries,
        service_name=service_name,
        use_circuit_breaker=use_circuit_breaker
    )
    
    method = method.upper()
    if method == "GET":
        return await client.get(path, **kwargs)
    elif method == "POST":
        return await client.post(path, **kwargs)
    elif method == "PUT":
        return await client.put(path, **kwargs)
    elif method == "DELETE":
        return await client.delete(path, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")

