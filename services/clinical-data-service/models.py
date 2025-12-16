"""
Data models for Clinical Data Service
FHIR integration and clinical decision support
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid

Base = declarative_base()


class ClinicalProfile(Base):
    """Clinical profile for a patient"""
    __tablename__ = "clinical_profiles"
    __table_args__ = (
        Index('idx_clinical_patient_id', 'patient_id'),
        Index('idx_clinical_created_at', 'created_at'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Demographics
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)
    ethnicity = Column(String, nullable=True)
    
    # Medical history
    medical_history = Column(JSON, nullable=True)  # List of conditions
    family_history = Column(JSON, nullable=True)
    medications = Column(JSON, nullable=True)  # List of medications
    
    # Vital signs
    vital_signs = Column(JSON, nullable=True)  # BP, HR, temperature, etc.
    
    # Lab results
    lab_results = Column(JSON, nullable=True)  # List of lab results
    
    # FHIR integration
    fhir_patient_id = Column(String, nullable=True)
    fhir_server_url = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class LabResult(Base):
    """Laboratory test result"""
    __tablename__ = "lab_results"
    __table_args__ = (
        Index('idx_lab_patient_id', 'patient_id'),
        Index('idx_lab_test_date', 'test_date'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    clinical_profile_id = Column(String, ForeignKey("clinical_profiles.id"), nullable=True)
    
    # Test details
    test_name = Column(String, nullable=False)
    test_code = Column(String, nullable=True)  # LOINC code
    test_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Results
    value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    interpretation = Column(String, nullable=True)  # "normal", "high", "low", "abnormal"
    
    # FHIR
    fhir_observation_id = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ClinicalRecommendation(Base):
    """Clinical decision support recommendation"""
    __tablename__ = "clinical_recommendations"
    __table_args__ = (
        Index('idx_recommendation_patient_id', 'patient_id'),
        Index('idx_recommendation_priority', 'priority'),
    )
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    patient_id = Column(String, nullable=False, index=True)
    
    # Recommendation details
    recommendation_type = Column(String, nullable=False)  # "screening", "treatment", "monitoring"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String, default="medium")  # "high", "medium", "low"
    
    # Evidence
    evidence_level = Column(String, nullable=True)  # "A", "B", "C"
    guideline_reference = Column(String, nullable=True)
    
    # Action items
    action_items = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


# Pydantic models
class ClinicalProfileCreate(BaseModel):
    """Request model for creating clinical profile"""
    patient_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    ethnicity: Optional[str] = None
    medical_history: Optional[List[str]] = None
    family_history: Optional[List[str]] = None
    medications: Optional[List[str]] = None


class ClinicalProfileResponse(BaseModel):
    """Response model for clinical profile"""
    id: str
    patient_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    medical_history: Optional[List[str]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class LabResultCreate(BaseModel):
    """Request model for lab result"""
    patient_id: str
    test_name: str
    test_code: Optional[str] = None
    test_date: datetime
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    interpretation: Optional[str] = None


class LabResultResponse(BaseModel):
    """Response model for lab result"""
    id: str
    patient_id: str
    test_name: str
    test_date: datetime
    value: Optional[float] = None
    interpretation: Optional[str] = None
    
    class Config:
        from_attributes = True

