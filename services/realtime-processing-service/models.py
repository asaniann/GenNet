"""
Data models for Real-Time Processing Service
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class RealTimeEvent(Base):
    """Real-time event database model"""
    __tablename__ = "realtime_events"
    __table_args__ = (
        Index('idx_event_patient_id', 'patient_id'),
        Index('idx_event_type', 'event_type'),
        Index('idx_event_timestamp', 'timestamp'),
        Index('idx_event_processed', 'processed'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Event details
    event_type = Column(String, nullable=False, index=True)  # "prediction", "alert", "update", "data_upload"
    event_data = Column(JSON, nullable=False)
    
    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Processing
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class Alert(Base):
    """Alert database model"""
    __tablename__ = "alerts"
    __table_args__ = (
        Index('idx_alert_patient_id', 'patient_id'),
        Index('idx_alert_severity', 'severity'),
        Index('idx_alert_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Alert details
    alert_type = Column(String, nullable=False)  # "risk_change", "anomaly", "threshold_exceeded"
    severity = Column(String, nullable=False, index=True)  # "low", "medium", "high", "critical"
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Alert data
    alert_data = Column(JSON, nullable=True)
    
    # Status
    acknowledged = Column(Boolean, default=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Pydantic models
class EventRequest(BaseModel):
    """Request model for publishing event"""
    patient_id: str
    event_type: str
    event_data: Dict[str, Any]


class EventResponse(BaseModel):
    """Response model for event"""
    id: str
    patient_id: str
    event_type: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Response model for alert"""
    id: str
    patient_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True

