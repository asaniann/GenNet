"""
Data models for Explainable AI Service
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class PredictionExplanation(Base):
    """Prediction explanation database model"""
    __tablename__ = "prediction_explanations"
    __table_args__ = (
        Index('idx_explanation_prediction_id', 'prediction_id'),
        Index('idx_explanation_patient_id', 'patient_id'),
        Index('idx_explanation_method', 'explanation_method'),
        Index('idx_explanation_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    prediction_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Explanation method
    explanation_method = Column(String, nullable=False, index=True)  # "shap", "lime", "attention"
    
    # Explanation data
    shap_values = Column(JSON, nullable=True)
    lime_explanation = Column(JSON, nullable=True)
    attention_weights = Column(JSON, nullable=True)
    
    # Feature importance
    feature_importance = Column(JSON, nullable=True)  # List of {feature, importance}
    top_features = Column(JSON, nullable=True)  # List of top feature names
    
    # Natural language explanation
    nlp_explanation = Column(Text, nullable=True)
    
    # Visualization URLs (stored in S3 or base64)
    shap_plot_url = Column(String, nullable=True)
    lime_plot_url = Column(String, nullable=True)
    attention_plot_url = Column(String, nullable=True)
    
    # Metadata
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Pydantic models
class ExplanationRequest(BaseModel):
    """Request model for generating explanation"""
    prediction_id: str
    patient_id: str
    prediction_value: float
    model_type: str = "ensemble"  # "ensemble", "tree", "neural", "linear"
    method: str = "shap"  # "shap", "lime", "both"
    features: Dict[str, Any]  # Feature values used in prediction
    training_data: Optional[List[Dict[str, Any]]] = None  # Optional training data for LIME


class ExplanationResponse(BaseModel):
    """Response model for explanation"""
    id: str
    prediction_id: str
    patient_id: str
    explanation_method: str
    feature_importance: List[Dict[str, Any]]
    top_features: List[str]
    nlp_explanation: Optional[str] = None
    shap_plot_url: Optional[str] = None
    lime_plot_url: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

