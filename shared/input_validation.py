"""
Input validation and sanitization
Prevent SQL injection, XSS, and other attacks
"""

import re
import html
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            value = str(value)
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value)
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Enforce max length
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return sanitized
    
    @staticmethod
    def validate_uuid(value: str) -> bool:
        """
        Validate UUID format
        
        Args:
            value: UUID string
            
        Returns:
            True if valid UUID
        """
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(value))
    
    @staticmethod
    def validate_email(value: str) -> bool:
        """
        Validate email format
        
        Args:
            value: Email string
            
        Returns:
            True if valid email
        """
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        return bool(email_pattern.match(value))
    
    @staticmethod
    def validate_sql_safe(value: str) -> bool:
        """
        Check if value is safe for SQL (no SQL injection patterns)
        
        Args:
            value: Input string
            
        Returns:
            True if safe
        """
        # Check for common SQL injection patterns
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            r"(--|;|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\bUNION\b.*\bSELECT\b)"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {value[:50]}")
                return False
        
        return True
    
    @staticmethod
    def sanitize_for_json(value: Any) -> Any:
        """
        Sanitize value for JSON serialization
        
        Args:
            value: Value to sanitize
            
        Returns:
            Sanitized value
        """
        if isinstance(value, str):
            return InputValidator.sanitize_string(value)
        elif isinstance(value, dict):
            return {k: InputValidator.sanitize_for_json(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [InputValidator.sanitize_for_json(item) for item in value]
        else:
            return value

