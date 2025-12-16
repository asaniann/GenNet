"""
Data models for Health Service
Unified health reports and recommendations
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class HealthReport(Base):
    """Health report for a patient"""
    __tablename__ = "health_reports"
    __table_args__ = (
        Index('idx_report_patient_id', 'patient_id'),
        Index('idx_report_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Report details
    report_type = Column(String, nullable=False)  # "comprehensive", "disease_risk", "drug_response"
    format = Column(String, default="pdf")  # "pdf", "json", "html"
    
    # Content
    predictions_summary = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    evidence_summary = Column(JSON, nullable=True)
    
    # File storage
    report_file_s3_key = Column(String, nullable=True)
    
    # Metadata
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class HealthRecommendation(Base):
    """Health recommendation for a patient"""
    __tablename__ = "health_recommendations"
    __table_args__ = (
        Index('idx_recommendation_patient_id', 'patient_id'),
        Index('idx_recommendation_priority', 'priority'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Recommendation details
    recommendation_type = Column(String, nullable=False)  # "screening", "lifestyle", "medication", "monitoring"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # "high", "medium", "low"
    
    # Evidence
    evidence_level = Column(String, nullable=True)  # "strong", "moderate", "weak"
    supporting_evidence = Column(JSON, nullable=True)
    
    # Action items
    action_items = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


# Pydantic models
class HealthReportRequest(BaseModel):
    """Request model for health report generation"""
    patient_id: str
    report_type: str = Field("comprehensive", description="comprehensive, disease_risk, drug_response")
    include_predictions: bool = True
    include_recommendations: bool = True
    include_network_visualization: bool = False
    format: str = Field("pdf", description="pdf, json, html")


class HealthReportResponse(BaseModel):
    """Response model for health report"""
    id: str
    patient_id: str
    report_type: str
    format: str
    generated_at: datetime
    report_url: Optional[str] = None
    
    class Config:
        from_attributes = True

