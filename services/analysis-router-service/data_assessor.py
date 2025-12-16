"""
Data availability and quality assessment
Integrates with Patient Data Service
"""

import os
import sys
from typing import Dict, Any, Optional
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class DataAssessor:
    """Assess available data and determine analysis feasibility"""
    
    def __init__(self):
        """Initialize data assessor"""
        patient_service_url = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient-data-service:8000")
        self.patient_client = ServiceClient(base_url=patient_service_url, timeout=30.0)
    
    async def assess_patient_data(
        self,
        patient_id: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Assess available data for a patient
        
        Args:
            patient_id: Patient ID
            token: Auth token
            
        Returns:
            Dictionary with data availability and quality
        """
        try:
            # Get patient data from Patient Data Service
            patient_data = await self.patient_client.get(
                f"/patients/{patient_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assessment = {
                "patient_id": patient_id,
                "has_genomic_data": patient_data.get("has_genomic_data", False),
                "has_expression_data": patient_data.get("has_expression_data", False),
                "has_clinical_data": patient_data.get("has_clinical_data", False),
                "has_multi_omics": patient_data.get("has_multi_omics", False),
                "data_quality": {
                    "genomic": self._assess_genomic_quality(patient_data),
                    "expression": self._assess_expression_quality(patient_data),
                    "clinical": self._assess_clinical_quality(patient_data)
                }
            }
            
            return assessment
            
        except Exception as e:
            logger.error(f"Error assessing patient data: {e}")
            # Return default assessment
            return {
                "patient_id": patient_id,
                "has_genomic_data": False,
                "has_expression_data": False,
                "has_clinical_data": False,
                "has_multi_omics": False,
                "data_quality": {}
            }
    
    def _assess_genomic_quality(self, patient_data: Dict) -> float:
        """Assess genomic data quality (0-1)"""
        # Placeholder - would check actual data quality
        if patient_data.get("has_genomic_data"):
            return 0.9  # Assume good quality
        return 0.0
    
    def _assess_expression_quality(self, patient_data: Dict) -> float:
        """Assess expression data quality (0-1)"""
        if patient_data.get("has_expression_data"):
            return 0.85  # Assume good quality
        return 0.0
    
    def _assess_clinical_quality(self, patient_data: Dict) -> float:
        """Assess clinical data quality (0-1)"""
        if patient_data.get("has_clinical_data"):
            return 0.8  # Assume good quality
        return 0.0
    
    def determine_grn_feasibility(
        self,
        assessment: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Determine if GRN construction is feasible
        
        Returns:
            (feasible, reason)
        """
        if not assessment.get("has_expression_data"):
            return (False, "No expression data available")
        
        expr_quality = assessment.get("data_quality", {}).get("expression", 0.0)
        if expr_quality < 0.7:
            return (False, f"Expression data quality too low: {expr_quality}")
        
        return (True, "Expression data sufficient for GRN construction")

