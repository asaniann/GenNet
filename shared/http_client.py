"""
HTTP client with timeouts and retry logic for service-to-service calls
"""
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    Retrying
)
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ServiceClient:
    """HTTP client with retries and timeouts for service-to-service calls"""
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        connect_timeout: float = 5.0,
        max_retries: int = 3,
        retry_backoff: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
    
    def _get_client(self) -> httpx.AsyncClient:
        """Create HTTP client with timeout configuration"""
        timeout = httpx.Timeout(
            timeout=self.timeout,
            connect=self.connect_timeout
        )
        return httpx.AsyncClient(timeout=timeout, base_url=self.base_url)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET request with retries"""
        async with self._get_client() as client:
            try:
                response = await client.get(path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                logger.error(f"Timeout calling {self.base_url}{path}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} calling {self.base_url}{path}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error calling {self.base_url}{path}: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST request with retries"""
        async with self._get_client() as client:
            try:
                response = await client.post(path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                logger.error(f"Timeout calling {self.base_url}{path}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} calling {self.base_url}{path}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error calling {self.base_url}{path}: {e}")
                raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError))
    )
    async def put(self, path: str, **kwargs) -> Dict[str, Any]:
        """PUT request with retries"""
        async with self._get_client() as client:
            try:
                response = await client.put(path, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                logger.error(f"Timeout calling {self.base_url}{path}: {e}")
                raise
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} calling {self.base_url}{path}")
                raise
            except httpx.RequestError as e:
                logger.error(f"Request error calling {self.base_url}{path}: {e}")
                raise


# Convenience function for quick service calls
async def call_service(
    url: str,
    method: str = "GET",
    timeout: float = 10.0,
    max_retries: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function to call a service endpoint with retries and timeouts
    
    Args:
        url: Full URL to call
        method: HTTP method (GET, POST, PUT, DELETE)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries
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
    client = ServiceClient(
        base_url="",  # Will use full URL
        timeout=timeout,
        max_retries=max_retries
    )
    
    # Extract base URL and path
    if '://' in url:
        parts = url.split('/', 3)
        base_url = f"{parts[0]}//{parts[2]}"
        path = '/' + parts[3] if len(parts) > 3 else '/'
        client.base_url = base_url
    
    method = method.upper()
    if method == "GET":
        return await client.get(path, **kwargs)
    elif method == "POST":
        return await client.post(path, **kwargs)
    elif method == "PUT":
        return await client.put(path, **kwargs)
    else:
        raise ValueError(f"Unsupported method: {method}")

