"""
Data models for Patient Data Service
Unified patient data management with privacy controls
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Index, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class Patient(Base):
    """Patient database model with privacy controls"""
    __tablename__ = "patients"
    __table_args__ = (
        Index('idx_patient_user_id', 'user_id'),
        Index('idx_patient_anonymized_id', 'anonymized_id'),
        Index('idx_patient_created_at', 'created_at'),
        Index('idx_patient_consent', 'consent_given'),
        Index('idx_patient_data_flags', 'has_genomic_data', 'has_expression_data', 'has_clinical_data'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, nullable=False, index=True)  # User ID from auth service
    anonymized_id = Column(String, unique=True, index=True, nullable=False)
    
    # Demographics (anonymized)
    age_range = Column(String)  # e.g., "40-50"
    gender = Column(String, nullable=True)
    ethnicity = Column(String, nullable=True)
    
    # Data availability flags
    has_genomic_data = Column(Boolean, default=False, index=True)
    has_expression_data = Column(Boolean, default=False, index=True)
    has_clinical_data = Column(Boolean, default=False, index=True)
    has_multi_omics = Column(Boolean, default=False, index=True)
    
    # Privacy and consent
    consent_given = Column(Boolean, default=False, index=True)
    consent_date = Column(DateTime(timezone=True), nullable=True)
    consent_version = Column(String, nullable=True)
    data_retention_policy = Column(String, default="standard")  # standard, extended, minimal
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete
    
    # Relationships (will be defined when other services are created)
    # genomic_profiles: relationship("GenomicProfile", back_populates="patient")
    # expression_profiles: relationship("ExpressionProfile", back_populates="patient")
    # health_predictions: relationship("HealthPrediction", back_populates="patient")


class PatientCreate(BaseModel):
    """Pydantic model for patient creation"""
    user_id: int = Field(..., description="User ID from auth service")
    age_range: Optional[str] = Field(None, description="Age range (e.g., '40-50')")
    gender: Optional[str] = Field(None, description="Gender")
    ethnicity: Optional[str] = Field(None, description="Ethnicity")
    consent_given: bool = Field(True, description="Consent given for data processing")
    data_retention_policy: str = Field("standard", description="Data retention policy")


class PatientUpdate(BaseModel):
    """Pydantic model for patient updates"""
    age_range: Optional[str] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    consent_given: Optional[bool] = None
    data_retention_policy: Optional[str] = None


class PatientResponse(BaseModel):
    """Pydantic model for patient response"""
    id: str
    user_id: int
    anonymized_id: str
    age_range: Optional[str] = None
    gender: Optional[str] = None
    ethnicity: Optional[str] = None
    has_genomic_data: bool
    has_expression_data: bool
    has_clinical_data: bool
    has_multi_omics: bool
    consent_given: bool
    consent_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DataUploadRequest(BaseModel):
    """Request model for data upload"""
    patient_id: str
    data_type: str = Field(..., description="Type of data: genomic, expression, clinical, proteomic, metabolomic")
    file_format: str = Field(..., description="File format: vcf, csv, tsv, json, etc.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class DataUploadResponse(BaseModel):
    """Response model for data upload"""
    upload_id: str
    patient_id: str
    data_type: str
    s3_key: str
    processing_status: str
    estimated_completion: Optional[datetime] = None

