"""
Data models for Pharmacogenomics Service
Drug-gene interactions and response prediction
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class DrugGeneInteraction(Base):
    """Drug-gene interaction"""
    __tablename__ = "drug_gene_interactions"
    __table_args__ = (
        Index('idx_interaction_drug', 'drug_name'),
        Index('idx_interaction_gene', 'gene'),
        Index('idx_interaction_phenotype', 'phenotype'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Drug details
    drug_name = Column(String, nullable=False, index=True)
    drug_code = Column(String, nullable=True)  # RxNorm, ATC code
    
    # Gene details
    gene = Column(String, nullable=False, index=True)
    variant = Column(String, nullable=True)  # rsID or variant notation
    
    # Interaction details
    phenotype = Column(String, nullable=False, index=True)  # "poor_metabolizer", "intermediate", "extensive", "ultra_rapid"
    clinical_significance = Column(String, nullable=False)  # "actionable", "informative", "testing_required"
    
    # Recommendations
    dosing_recommendation = Column(Text, nullable=True)
    alternative_drugs = Column(JSON, nullable=True)  # List of alternative drugs
    monitoring_recommendations = Column(Text, nullable=True)
    
    # Evidence
    evidence_level = Column(String, nullable=True)  # "A", "B", "C"
    guideline_reference = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DrugResponsePrediction(Base):
    """Drug response prediction for a patient"""
    __tablename__ = "drug_response_predictions"
    __table_args__ = (
        Index('idx_prediction_patient_id', 'patient_id'),
        Index('idx_prediction_drug', 'drug_name'),
        Index('idx_prediction_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Drug details
    drug_name = Column(String, nullable=False, index=True)
    drug_code = Column(String, nullable=True)
    indication = Column(String, nullable=True)  # Disease/condition
    
    # Prediction
    response_probability = Column(Float, nullable=False)  # 0-1
    efficacy_score = Column(Float, nullable=True)  # 0-100
    toxicity_risk = Column(Float, nullable=True)  # 0-100
    
    # Genomic factors
    contributing_genes = Column(JSON, nullable=True)  # List of genes with contributions
    contributing_variants = Column(JSON, nullable=True)  # List of variants
    
    # Recommendations
    recommended_dose = Column(Float, nullable=True)
    dose_adjustment = Column(String, nullable=True)  # "increase", "decrease", "normal", "avoid"
    monitoring_required = Column(Boolean, default=False)
    
    # Confidence
    confidence = Column(Float, nullable=False)  # 0-1
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Pydantic models
class DrugResponseRequest(BaseModel):
    """Request model for drug response prediction"""
    patient_id: str
    drug_name: str
    drug_code: Optional[str] = None
    indication: Optional[str] = None
    genomic_profile_id: Optional[str] = None


class DrugResponseResponse(BaseModel):
    """Response model for drug response prediction"""
    id: str
    patient_id: str
    drug_name: str
    response_probability: float
    efficacy_score: Optional[float] = None
    toxicity_risk: Optional[float] = None
    recommended_dose: Optional[float] = None
    dose_adjustment: Optional[str] = None
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True

