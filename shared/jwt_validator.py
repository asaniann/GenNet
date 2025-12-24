"""
Enhanced JWT validation with auth service verification
"""

import jwt
import httpx
import os
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class JWTValidator:
    """Enhanced JWT validator with auth service verification"""
    
    def __init__(self):
        """Initialize JWT validator"""
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.auth_service_url = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8000")
        self.verify_with_service = os.getenv("VERIFY_JWT_WITH_SERVICE", "false").lower() == "true"
    
    def validate_token(
        self,
        token: str,
        verify_signature: bool = True
    ) -> Dict[str, Any]:
        """
        Validate JWT token
        
        Args:
            token: JWT token string
            verify_signature: Whether to verify signature
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException if token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                self.jwt_secret_key,
                algorithms=[self.jwt_algorithm],
                options={"verify_signature": verify_signature}
            )
            
            # Verify with auth service if enabled
            if self.verify_with_service:
                is_valid = self._verify_with_auth_service(token)
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token verification failed with auth service",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            # Check token expiration
            if "exp" in payload:
                import time
                if payload["exp"] < time.time():
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has expired",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def _verify_with_auth_service(self, token: str) -> bool:
        """
        Verify token with auth service
        
        Args:
            token: JWT token
            
        Returns:
            True if token is valid
        """
        try:
            response = httpx.get(
                f"{self.auth_service_url}/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Could not verify token with auth service: {e}")
            # Fall back to local validation
            return True
    
    def extract_user_id(self, token: str) -> int:
        """
        Extract user ID from token
        
        Args:
            token: JWT token
            
        Returns:
            User ID
        """
        payload = self.validate_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return int(user_id)

