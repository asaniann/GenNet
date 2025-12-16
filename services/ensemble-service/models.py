"""
Data models for Ensemble Service
Combining predictions from multiple methods
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class EnsemblePrediction(Base):
    """Ensemble prediction combining multiple methods"""
    __tablename__ = "ensemble_predictions"
    __table_args__ = (
        Index('idx_ensemble_plan_id', 'analysis_plan_id'),
        Index('idx_ensemble_disease', 'disease_code'),
        Index('idx_ensemble_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    analysis_plan_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Ensemble details
    ensemble_strategy = Column(String, nullable=False)  # "weighted_voting", "stacking", "bayesian"
    component_prediction_ids = Column(JSON, nullable=False)  # List of prediction IDs
    
    # Final prediction
    disease_code = Column(String, nullable=False, index=True)
    disease_name = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Method contributions
    method_contributions = Column(JSON, nullable=True)  # Dict: method -> contribution
    method_weights = Column(JSON, nullable=True)  # Dict: method -> weight
    
    # Agreement metrics
    agreement_score = Column(Float, nullable=True)  # Agreement between methods (0-1)
    disagreement_details = Column(JSON, nullable=True)
    
    # Evidence summary
    evidence_summary = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Pydantic models
class EnsembleRequest(BaseModel):
    """Request model for ensemble prediction"""
    analysis_plan_id: str
    disease_code: str
    component_predictions: List[Dict[str, Any]] = Field(..., description="List of predictions from different methods")


class EnsembleResponse(BaseModel):
    """Response model for ensemble prediction"""
    id: str
    disease_code: str
    disease_name: str
    risk_score: float
    confidence: float
    ensemble_strategy: str
    agreement_score: Optional[float] = None
    method_contributions: Optional[Dict[str, float]] = None
    evidence_summary: Optional[Dict] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

