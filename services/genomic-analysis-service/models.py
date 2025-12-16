"""
Data models for Genomic Analysis Service
Integrates with Patient Data Service and GRN Service
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class GenomicProfile(Base):
    """Genomic profile for a patient"""
    __tablename__ = "genomic_profiles"
    __table_args__ = (
        Index('idx_genomic_patient_id', 'patient_id'),
        Index('idx_genomic_created_at', 'created_at'),
        Index('idx_genomic_status', 'processing_status'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)  # Reference to Patient Data Service
    
    # File storage
    vcf_file_s3_key = Column(String, nullable=True)
    vcf_file_size = Column(Integer, nullable=True)
    vcf_file_format = Column(String, default="vcf")
    
    # Processing metadata
    variant_count = Column(Integer, default=0)
    processing_status = Column(String, default="uploaded")  # uploaded, processing, completed, failed
    annotation_version = Column(String, nullable=True)
    annotation_date = Column(DateTime(timezone=True), nullable=True)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    coverage_mean = Column(Float, nullable=True)
    coverage_median = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    variants = relationship("Variant", back_populates="genomic_profile", cascade="all, delete-orphan")
    prs_scores = relationship("PRSScore", back_populates="genomic_profile", cascade="all, delete-orphan")


class Variant(Base):
    """Genetic variant"""
    __tablename__ = "variants"
    __table_args__ = (
        Index('idx_variant_genomic_profile', 'genomic_profile_id'),
        Index('idx_variant_chr_pos', 'chromosome', 'position'),
        Index('idx_variant_gene', 'gene'),
        Index('idx_variant_impact', 'impact'),
        Index('idx_variant_clinvar', 'clinvar_significance'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    genomic_profile_id = Column(String, ForeignKey("genomic_profiles.id"), nullable=False, index=True)
    
    # Variant coordinates
    chromosome = Column(String, nullable=False, index=True)
    position = Column(Integer, nullable=False, index=True)
    ref_allele = Column(String, nullable=False)
    alt_allele = Column(String, nullable=False)
    
    # Variant identifier
    rsid = Column(String, nullable=True, index=True)  # dbSNP ID
    
    # Annotation
    gene = Column(String, nullable=True, index=True)
    gene_id = Column(String, nullable=True)  # Ensembl or NCBI gene ID
    consequence = Column(String, nullable=True)  # missense_variant, etc.
    impact = Column(String, nullable=True, index=True)  # HIGH, MODERATE, LOW, MODIFIER
    
    # Prediction scores
    sift_score = Column(Float, nullable=True)
    sift_prediction = Column(String, nullable=True)
    polyphen_score = Column(Float, nullable=True)
    polyphen_prediction = Column(String, nullable=True)
    cadd_score = Column(Float, nullable=True, index=True)
    dann_score = Column(Float, nullable=True)
    
    # Population frequency
    gnomad_af = Column(Float, nullable=True)  # Allele frequency
    gnomad_af_popmax = Column(Float, nullable=True)
    gnomad_af_afr = Column(Float, nullable=True)
    gnomad_af_eur = Column(Float, nullable=True)
    gnomad_af_asj = Column(Float, nullable=True)
    gnomad_af_eas = Column(Float, nullable=True)
    
    # Clinical significance
    clinvar_significance = Column(String, nullable=True, index=True)  # Pathogenic, Benign, etc.
    clinvar_review = Column(String, nullable=True)
    clinvar_variation_id = Column(String, nullable=True)
    
    # Genotype
    genotype = Column(String, nullable=True)  # "0/1", "1/1", etc.
    quality = Column(Float, nullable=True)
    depth = Column(Integer, nullable=True)
    
    # Additional annotation (JSON for flexibility)
    additional_annotation = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    genomic_profile = relationship("GenomicProfile", back_populates="variants")


class PRSScore(Base):
    """Polygenic Risk Score for a disease"""
    __tablename__ = "prs_scores"
    __table_args__ = (
        Index('idx_prs_genomic_profile', 'genomic_profile_id'),
        Index('idx_prs_disease', 'disease_code'),
        Index('idx_prs_percentile', 'percentile'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    genomic_profile_id = Column(String, ForeignKey("genomic_profiles.id"), nullable=False, index=True)
    
    # PRS details
    disease_code = Column(String, nullable=False, index=True)  # ICD-10 or custom
    disease_name = Column(String, nullable=False)
    prs_model_id = Column(String, nullable=True)  # PGS Catalog ID
    prs_model_version = Column(String, nullable=True)
    prs_model_name = Column(String, nullable=True)
    
    # Scores
    prs_score = Column(Float, nullable=False, index=True)
    percentile = Column(Float, nullable=True, index=True)  # Population percentile
    z_score = Column(Float, nullable=True)
    
    # Confidence
    confidence_interval_lower = Column(Float, nullable=True)
    confidence_interval_upper = Column(Float, nullable=True)
    confidence_level = Column(Float, default=0.95)  # 0.95 for 95% CI
    
    # Variant information
    variant_count = Column(Integer, default=0)  # Number of variants used
    variant_details = Column(JSON, nullable=True)  # Details of contributing variants
    
    # Population
    population = Column(String, default="EUR")  # EUR, AFR, ASN, etc.
    
    # Metadata
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    model_parameters = Column(JSON, nullable=True)
    
    # Relationships
    genomic_profile = relationship("GenomicProfile", back_populates="prs_scores")


# Pydantic models for API
class GenomicProfileCreate(BaseModel):
    """Request model for creating genomic profile"""
    patient_id: str = Field(..., description="Patient ID from Patient Data Service")
    vcf_file_format: str = Field("vcf", description="File format")


class GenomicProfileResponse(BaseModel):
    """Response model for genomic profile"""
    id: str
    patient_id: str
    variant_count: int
    processing_status: str
    quality_score: Optional[float] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class VariantResponse(BaseModel):
    """Response model for variant"""
    id: str
    chromosome: str
    position: int
    ref_allele: str
    alt_allele: str
    gene: Optional[str] = None
    consequence: Optional[str] = None
    impact: Optional[str] = None
    cadd_score: Optional[float] = None
    gnomad_af: Optional[float] = None
    clinvar_significance: Optional[str] = None
    
    class Config:
        from_attributes = True


class PRSScoreRequest(BaseModel):
    """Request model for PRS calculation"""
    diseases: List[str] = Field(..., description="List of disease codes (ICD-10 or custom)")
    population: str = Field("EUR", description="Population for calibration")
    prs_model_ids: Optional[Dict[str, str]] = Field(None, description="Optional: specific PRS model IDs per disease")


class PRSScoreResponse(BaseModel):
    """Response model for PRS score"""
    id: str
    disease_code: str
    disease_name: str
    prs_score: float
    percentile: Optional[float] = None
    z_score: Optional[float] = None
    confidence_interval_lower: Optional[float] = None
    confidence_interval_upper: Optional[float] = None
    variant_count: int
    population: str
    calculated_at: datetime
    
    class Config:
        from_attributes = True

