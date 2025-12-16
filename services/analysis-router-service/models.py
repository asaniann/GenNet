"""
Data models for Analysis Router Service
Intelligent method selection and routing
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class AnalysisPlan(Base):
    """Analysis plan for a patient"""
    __tablename__ = "analysis_plans"
    __table_args__ = (
        Index('idx_plan_patient_id', 'patient_id'),
        Index('idx_plan_status', 'status'),
        Index('idx_plan_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Selected methods
    methods = Column(JSON, nullable=False)  # ["prs", "expression", "grn", ...]
    ensemble_strategy = Column(String, nullable=True)  # "weighted_voting", "stacking", etc.
    
    # Feasibility
    grn_feasible = Column(Boolean, default=False)
    grn_feasibility_reason = Column(Text, nullable=True)
    
    # Data availability
    has_genomic_data = Column(Boolean, default=False)
    has_expression_data = Column(Boolean, default=False)
    has_clinical_data = Column(Boolean, default=False)
    has_multi_omics = Column(Boolean, default=False)
    
    # Execution status
    status = Column(String, default="planned")  # planned, executing, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    prediction_ids = Column(JSON, nullable=True)  # IDs of component predictions
    ensemble_prediction_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic models
class AnalysisRequest(BaseModel):
    """Request model for analysis"""
    patient_id: str
    data_types: List[str] = Field(..., description="Available data types: genomic, expression, clinical")
    preferences: Optional[Dict[str, Any]] = Field(None, description="User preferences")


class AnalysisPlanResponse(BaseModel):
    """Response model for analysis plan"""
    id: str
    patient_id: str
    methods: List[str]
    ensemble_strategy: Optional[str] = None
    grn_feasible: bool
    has_genomic_data: bool
    has_expression_data: bool
    has_clinical_data: bool
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

