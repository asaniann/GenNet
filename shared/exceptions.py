"""
Custom exceptions for GenNet services
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any


class GenNetException(HTTPException):
    """Base exception for GenNet platform"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        error_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code or f"ERR_{status_code}"
        self.error_type = error_type or self.__class__.__name__
        self.metadata = metadata or {}


class ValidationError(GenNetException):
    """Raised when request validation fails"""
    
    def __init__(self, detail: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR",
            error_type="ValidationError",
            metadata={"field": field, **kwargs}
        )


class NotFoundError(GenNetException):
    """Raised when a resource is not found"""
    
    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource_type} with id '{resource_id}' not found",
            error_code="NOT_FOUND",
            error_type="NotFoundError",
            metadata={"resource_type": resource_type, "resource_id": resource_id, **kwargs}
        )


class UnauthorizedError(GenNetException):
    """Raised when authentication/authorization fails"""
    
    def __init__(self, detail: str = "Authentication required", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED",
            error_type="UnauthorizedError",
            metadata=kwargs
        )


class ForbiddenError(GenNetException):
    """Raised when access is forbidden"""
    
    def __init__(self, detail: str = "Access forbidden", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN",
            error_type="ForbiddenError",
            metadata=kwargs
        )


class ConflictError(GenNetException):
    """Raised when a resource conflict occurs"""
    
    def __init__(self, detail: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code="CONFLICT",
            error_type="ConflictError",
            metadata={"resource_type": resource_type, **kwargs}
        )


class ServiceUnavailableError(GenNetException):
    """Raised when a dependent service is unavailable"""
    
    def __init__(self, service_name: str, detail: Optional[str] = None, **kwargs):
        detail = detail or f"Service '{service_name}' is currently unavailable"
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
            error_type="ServiceUnavailableError",
            metadata={"service_name": service_name, **kwargs}
        )


class RateLimitError(GenNetException):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_EXCEEDED",
            error_type="RateLimitError",
            metadata={"retry_after": retry_after, **kwargs}
        )


class InternalServerError(GenNetException):
    """Raised when an internal server error occurs"""
    
    def __init__(self, detail: str = "Internal server error", error_id: Optional[str] = None, **kwargs):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="INTERNAL_ERROR",
            error_type="InternalServerError",
            metadata={"error_id": error_id, **kwargs}
        )


def create_error_response(
    exception: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Create a standardized error response from an exception
    
    Args:
        exception: The exception to convert
        include_traceback: Whether to include traceback in response (only for development)
    
    Returns:
        Dictionary with error details
    """
    if isinstance(exception, GenNetException):
        return {
            "error": {
                "code": exception.error_code,
                "type": exception.error_type,
                "message": exception.detail,
                "metadata": exception.metadata
            }
        }
    elif isinstance(exception, HTTPException):
        return {
            "error": {
                "code": f"HTTP_{exception.status_code}",
                "type": "HTTPException",
                "message": exception.detail,
                "metadata": {}
            }
        }
    else:
        response = {
            "error": {
                "code": "INTERNAL_ERROR",
                "type": type(exception).__name__,
                "message": str(exception),
                "metadata": {}
            }
        }
        
        if include_traceback:
            import traceback
            response["error"]["traceback"] = traceback.format_exc()
        
        return response

