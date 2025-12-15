"""
Data models for workflow service
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, JSON, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
import enum

Base = declarative_base()


class JobStatus(str, enum.Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Workflow(Base):
    """Workflow database model"""
    __tablename__ = "workflows"
    __table_args__ = (
        Index('idx_workflow_owner_id', 'owner_id'),
        Index('idx_workflow_status', 'status'),
        Index('idx_workflow_created_at', 'created_at'),
        Index('idx_workflow_type', 'workflow_type'),
        Index('idx_workflow_network_id', 'network_id'),
        Index('idx_workflow_owner_status', 'owner_id', 'status'),
    )
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    workflow_type = Column(String, nullable=False)  # qualitative, hybrid, ml
    network_id = Column(String, nullable=False)
    parameters = Column(JSON)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Integer, default=0)  # 0-100
    results = Column(JSON)
    error_message = Column(Text)
    owner_id = Column(Integer, nullable=False)  # User ID from auth service (no FK constraint)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))


class WorkflowCreate(BaseModel):
    """Workflow creation model"""
    name: str
    description: Optional[str] = None
    workflow_type: str
    network_id: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    """Workflow response model"""
    id: str
    name: str
    description: Optional[str]
    workflow_type: str
    network_id: str
    parameters: Optional[Dict[str, Any]]
    status: JobStatus
    progress: int
    results: Optional[Dict[str, Any]]
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

