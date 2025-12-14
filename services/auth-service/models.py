"""
Data models for authentication service
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

Base = declarative_base()


class User(Base):
    """User database model"""
    __tablename__ = "users"
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_created_at', 'created_at'),
        Index('idx_user_active', 'is_active'),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserCreate(BaseModel):
    """Pydantic model for user creation"""
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Pydantic model for user response"""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model"""
    username: Optional[str] = None
    user_id: Optional[int] = None

