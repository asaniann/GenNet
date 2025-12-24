"""
Batch operations for bulk patient creation and updates
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models import Patient
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class BatchOperations:
    """Batch operations for patient data"""
    
    def __init__(self, db: Session):
        """Initialize batch operations"""
        self.db = db
    
    def create_patients_batch(
        self,
        patients_data: List[Dict[str, Any]],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Create multiple patients in a single transaction
        
        Args:
            patients_data: List of patient data dictionaries
            user_id: User ID creating the patients
            
        Returns:
            Dictionary with results
        """
        created = []
        errors = []
        
        for patient_data in patients_data:
            try:
                # Generate anonymized ID
                anonymized_id = f"PAT-{uuid.uuid4().hex[:12].upper()}"
                
                patient = Patient(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    anonymized_id=anonymized_id,
                    age_range=patient_data.get("age_range"),
                    gender=patient_data.get("gender"),
                    ethnicity=patient_data.get("ethnicity"),
                    consent_given=patient_data.get("consent_given", False),
                    data_retention_policy=patient_data.get("data_retention_policy", "standard"),
                    created_at=datetime.utcnow()
                )
                
                self.db.add(patient)
                created.append({
                    "id": patient.id,
                    "anonymized_id": patient.anonymized_id
                })
            except Exception as e:
                errors.append({
                    "data": patient_data,
                    "error": str(e)
                })
        
        if created:
            self.db.commit()
        
        return {
            "created": len(created),
            "errors": len(errors),
            "results": created,
            "error_details": errors
        }
    
    def update_patients_batch(
        self,
        updates: List[Dict[str, Any]],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Update multiple patients in a single transaction
        
        Args:
            updates: List of update dictionaries with patient_id and updates
            user_id: User ID performing updates
            
        Returns:
            Dictionary with results
        """
        updated = []
        errors = []
        
        for update_data in updates:
            try:
                patient_id = update_data.get("patient_id")
                if not patient_id:
                    errors.append({"error": "Missing patient_id", "data": update_data})
                    continue
                
                patient = self.db.query(Patient).filter(
                    Patient.id == patient_id,
                    Patient.user_id == user_id
                ).first()
                
                if not patient:
                    errors.append({"error": "Patient not found", "patient_id": patient_id})
                    continue
                
                # Update fields
                update_fields = update_data.get("updates", {})
                for field, value in update_fields.items():
                    if hasattr(patient, field):
                        setattr(patient, field, value)
                
                patient.updated_at = datetime.utcnow()
                updated.append({"patient_id": patient_id})
                
            except Exception as e:
                errors.append({
                    "data": update_data,
                    "error": str(e)
                })
        
        if updated:
            self.db.commit()
        
        return {
            "updated": len(updated),
            "errors": len(errors),
            "results": updated,
            "error_details": errors
        }

