"""
Data models for Multi-Omics Integration Service
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class MultiOmicsProfile(Base):
    """Multi-omics integrated profile"""
    __tablename__ = "multi_omics_profiles"
    __table_args__ = (
        Index('idx_multiomics_patient_id', 'patient_id'),
        Index('idx_multiomics_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Component profiles
    genomic_profile_id = Column(String, nullable=True)
    expression_profile_id = Column(String, nullable=True)
    proteomic_profile_id = Column(String, nullable=True)
    metabolomic_profile_id = Column(String, nullable=True)
    
    # Integration
    fusion_method = Column(String, nullable=False)  # "early", "late", "intermediate", "multi_view"
    integrated_features = Column(JSON, nullable=True)  # Combined feature vector
    
    # Metadata
    feature_count = Column(Integer, default=0)
    omics_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Pydantic models
class MultiOmicsIntegrationRequest(BaseModel):
    """Request model for multi-omics integration"""
    patient_id: str
    genomic_profile_id: Optional[str] = None
    expression_profile_id: Optional[str] = None
    proteomic_profile_id: Optional[str] = None
    metabolomic_profile_id: Optional[str] = None
    fusion_method: str = Field("multi_view", description="early, late, intermediate, multi_view")


class MultiOmicsProfileResponse(BaseModel):
    """Response model for multi-omics profile"""
    id: str
    patient_id: str
    fusion_method: str
    feature_count: int
    omics_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

