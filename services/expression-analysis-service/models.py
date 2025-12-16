"""
Data models for Expression Analysis Service
Integrates with Patient Data Service and ML Service
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class ExpressionProfile(Base):
    """Expression profile for a patient"""
    __tablename__ = "expression_profiles"
    __table_args__ = (
        Index('idx_expression_patient_id', 'patient_id'),
        Index('idx_expression_created_at', 'created_at'),
        Index('idx_expression_status', 'processing_status'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Data details
    tissue_type = Column(String, nullable=False)
    sample_date = Column(DateTime(timezone=True), nullable=True)
    platform = Column(String, nullable=False)  # "rna_seq", "microarray"
    
    # File storage
    expression_file_s3_key = Column(String, nullable=True)
    normalized_file_s3_key = Column(String, nullable=True)
    
    # Metadata
    gene_count = Column(Integer, default=0)
    sample_count = Column(Integer, default=1)  # For single-sample analysis
    processing_status = Column(String, default="uploaded")
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    rna_quality = Column(Float, nullable=True)  # RIN score for RNA-seq
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    signature_scores = relationship("SignatureScore", back_populates="expression_profile", cascade="all, delete-orphan")
    biomarkers = relationship("Biomarker", back_populates="expression_profile", cascade="all, delete-orphan")


class SignatureScore(Base):
    """Expression signature score"""
    __tablename__ = "signature_scores"
    __table_args__ = (
        Index('idx_signature_expression_profile', 'expression_profile_id'),
        Index('idx_signature_id', 'signature_id'),
        Index('idx_signature_score', 'score'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    expression_profile_id = Column(String, ForeignKey("expression_profiles.id"), nullable=False, index=True)
    
    # Signature details
    signature_id = Column(String, nullable=False, index=True)
    signature_name = Column(String, nullable=False)
    signature_type = Column(String, nullable=False)  # "disease", "treatment", "prognostic", "pathway"
    
    # Score
    score = Column(Float, nullable=False, index=True)
    percentile = Column(Float, nullable=True)
    p_value = Column(Float, nullable=True)
    fdr = Column(Float, nullable=True)  # False discovery rate
    
    # Method
    scoring_method = Column(String, nullable=False)  # "ssGSEA", "GSVA", "z_score", "mean"
    
    # Top contributing genes
    top_genes = Column(JSON, nullable=True)  # List of gene names with contributions
    
    # Timestamps
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    expression_profile = relationship("ExpressionProfile", back_populates="signature_scores")


class Biomarker(Base):
    """Biomarker identified from expression data"""
    __tablename__ = "biomarkers"
    __table_args__ = (
        Index('idx_biomarker_expression_profile', 'expression_profile_id'),
        Index('idx_biomarker_gene', 'gene'),
        Index('idx_biomarker_type', 'biomarker_type'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    expression_profile_id = Column(String, ForeignKey("expression_profiles.id"), nullable=False, index=True)
    
    # Biomarker details
    gene = Column(String, nullable=False, index=True)
    gene_id = Column(String, nullable=True)
    biomarker_type = Column(String, nullable=False)  # "diagnostic", "prognostic", "predictive", "surrogate"
    
    # Expression values
    expression_value = Column(Float, nullable=False)
    fold_change = Column(Float, nullable=True)
    log2_fold_change = Column(Float, nullable=True)
    
    # Statistical significance
    p_value = Column(Float, nullable=True)
    adjusted_p_value = Column(Float, nullable=True)  # FDR or Bonferroni
    
    # Context
    disease_code = Column(String, nullable=True)
    disease_name = Column(String, nullable=True)
    
    # Timestamps
    identified_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    expression_profile = relationship("ExpressionProfile", back_populates="biomarkers")


# Pydantic models
class ExpressionProfileCreate(BaseModel):
    """Request model for creating expression profile"""
    patient_id: str
    tissue_type: str
    platform: str = Field(..., description="rna_seq or microarray")
    sample_date: Optional[datetime] = None


class ExpressionProfileResponse(BaseModel):
    """Response model for expression profile"""
    id: str
    patient_id: str
    tissue_type: str
    platform: str
    gene_count: int
    processing_status: str
    quality_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignatureScoreRequest(BaseModel):
    """Request model for signature scoring"""
    signatures: List[str] = Field(..., description="List of signature IDs")
    method: str = Field("ssGSEA", description="Scoring method: ssGSEA, GSVA, z_score, mean")


class SignatureScoreResponse(BaseModel):
    """Response model for signature score"""
    id: str
    signature_id: str
    signature_name: str
    signature_type: str
    score: float
    percentile: Optional[float] = None
    p_value: Optional[float] = None
    scoring_method: str
    top_genes: Optional[List[Dict]] = None
    
    class Config:
        from_attributes = True

