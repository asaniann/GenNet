"""
Enhanced Input Validation Utilities
Provides common validation functions for API endpoints
"""

import re
import logging
from typing import Any, Dict, List, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format
    
    Args:
        uuid_string: String to validate
        
    Returns:
        True if valid UUID, False otherwise
    """
    uuid_pattern = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )
    return bool(uuid_pattern.match(uuid_string))


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email, False otherwise
    """
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    return bool(email_pattern.match(email))


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValueError("Value must be a string")
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Enforce max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        logger.warning(f"String truncated to {max_length} characters")
    
    return sanitized


def validate_pagination(page: int, limit: int, max_limit: int = 100) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters
    
    Args:
        page: Page number (1-indexed)
        limit: Items per page
        max_limit: Maximum items per page
        
    Returns:
        Tuple of (validated_page, validated_limit)
    """
    if page < 1:
        page = 1
    if limit < 1:
        limit = 10
    if limit > max_limit:
        limit = max_limit
    
    return page, limit


def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validate JSON structure has required fields
    
    Args:
        data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        True if all required fields present, False otherwise
    """
    if not isinstance(data, dict):
        return False
    
    for field in required_fields:
        if field not in data:
            return False
    
    return True


def validate_range(value: float, min_val: float, max_val: float) -> bool:
    """
    Validate value is within range
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        True if value in range, False otherwise
    """
    return min_val <= value <= max_val


def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
    """
    Validate value is in allowed enum values
    
    Args:
        value: Value to validate
        allowed_values: List of allowed values
        
    Returns:
        True if value in allowed values, False otherwise
    """
    return value in allowed_values


def validate_input(func: Callable) -> Callable:
    """
    Decorator to validate function inputs
    
    Usage:
        @validate_input
        def my_function(param1: str, param2: int):
            # Function implementation
            pass
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Basic validation - can be extended
        for arg in args:
            if isinstance(arg, str) and len(arg) > 10000:
                raise ValueError("Input string too long")
        
        return func(*args, **kwargs)
    
    return wrapper
