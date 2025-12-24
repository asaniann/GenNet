"""
GDPR Data Subject Rights Implementation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.gdpr_compliance import GDPRCompliance
from database import get_db
from dependencies import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-subject-rights", tags=["GDPR"])


@router.post("/export/{patient_id}")
async def export_patient_data(
    patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Export all patient data (GDPR Right to Access)
    
    - **patient_id**: Patient ID
    """
    # Verify access
    from dependencies import verify_patient_access
    await verify_patient_access(patient_id, user_id, db)
    
    gdpr = GDPRCompliance(db)
    export_data = gdpr.export_patient_data(patient_id)
    
    return export_data


@router.delete("/delete/{patient_id}")
async def delete_patient_data(
    patient_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Delete all patient data (GDPR Right to Erasure)
    
    - **patient_id**: Patient ID
    """
    # Verify access
    from dependencies import verify_patient_access
    await verify_patient_access(patient_id, user_id, db)
    
    gdpr = GDPRCompliance(db)
    success = gdpr.delete_patient_data(patient_id)
    
    if success:
        return {"message": f"Data deletion initiated for patient: {patient_id}"}
    else:
        raise HTTPException(status_code=500, detail="Data deletion failed")


@router.put("/rectify/{patient_id}")
async def rectify_patient_data(
    patient_id: str,
    updates: Dict[str, Any],
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update patient data (GDPR Right to Rectification)
    
    - **patient_id**: Patient ID
    - **updates**: Dictionary of updates
    """
    # Verify access
    from dependencies import verify_patient_access
    await verify_patient_access(patient_id, user_id, db)
    
    gdpr = GDPRCompliance(db)
    success = gdpr.update_patient_data(patient_id, updates)
    
    if success:
        return {"message": f"Data updated for patient: {patient_id}"}
    else:
        raise HTTPException(status_code=500, detail="Data update failed")

