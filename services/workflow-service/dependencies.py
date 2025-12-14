"""
Dependencies for workflow service
"""

from fastapi import Header, HTTPException, status
from typing import Optional
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")


async def get_current_user_id(authorization: Optional[str] = Header(None)) -> int:
    """Extract user ID from JWT token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

