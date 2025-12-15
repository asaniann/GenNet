"""
Authentication and Authorization Service
Handles user authentication, authorization, and session management
"""

import logging
import sys
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import os
import redis
import json

from models import User, Token, TokenData
from database import get_db, init_db
from auth import verify_password, get_password_hash, create_access_token, verify_token
from dependencies import get_current_user

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import correlation ID middleware and cache
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.logging_middleware import CorrelationIDMiddleware, get_logger
from shared.cache import cached

app = FastAPI(
    title="GenNet Auth Service",
    description="Authentication and Authorization Service",
    version="1.0.0"
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

logger = get_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize Redis client (with fallback for testing)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=0,
        decode_responses=True,
        socket_connect_timeout=2
    )
    redis_client.ping()  # Test connection
except (redis.ConnectionError, redis.TimeoutError):
    redis_client = None  # Will use mock in tests


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting Auth Service...")
    init_db()
    logger.info("Auth Service started successfully")


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return access token"""
    logger.info(f"Login attempt for user: {form_data.username}")
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username, "user_id": user.id})
    
    # Store token in Redis for session management (if available)
    if redis_client:
        try:
            redis_client.setex(f"token:{access_token}", 3600, str(user.id))
        except (redis.ConnectionError, redis.TimeoutError):
            pass  # Continue without Redis in dev/test
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    """Register a new user"""
    from shared.metrics import users_registered_total
    # Check if user exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully", "user_id": user.id}


@app.get("/me")
@cached(ttl=300, key_prefix="cache")  # Cache user info for 5 minutes
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at
    }


@app.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout user by invalidating token"""
    if redis_client:
        try:
            redis_client.delete(f"token:{token}")
        except (redis.ConnectionError, redis.TimeoutError):
            pass
    return {"message": "Logged out successfully"}


@app.get("/health/live")
async def liveness():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe"""
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    
    health_status = {
        "status": "ready",
        "service": "auth-service",
        "version": "1.0.0"
    }
    checks = {}
    all_ready = True
    
    # Check database connection (critical)
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        all_ready = False
    
    # Check Redis connection (optional but preferred)
    try:
        if redis_client:
            redis_client.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_configured"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        # Redis is optional, don't fail readiness check
    
    health_status["checks"] = checks
    health_status["status"] = "ready" if all_ready else "not_ready"
    
    status_code = 200 if all_ready else 503
    return JSONResponse(
        content=health_status,
        status_code=status_code
    )


@app.get("/health")
async def health():
    """Legacy health endpoint - redirects to readiness"""
    return await readiness()

