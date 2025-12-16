"""
Service clients for Health Service
Integrates with all analysis services
"""

import os
import sys
from typing import Optional, Dict, Any, List
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class AnalysisServiceClient:
    """Client for aggregating predictions from all analysis services"""
    
    def __init__(self):
        self.genomic_service_url = os.getenv("GENOMIC_ANALYSIS_SERVICE_URL", "http://genomic-analysis-service:8000")
        self.expression_service_url = os.getenv("EXPRESSION_ANALYSIS_SERVICE_URL", "http://expression-analysis-service:8000")
        self.ensemble_service_url = os.getenv("ENSEMBLE_SERVICE_URL", "http://ensemble-service:8000")
        
        self.genomic_client = ServiceClient(base_url=self.genomic_service_url, timeout=60.0)
        self.expression_client = ServiceClient(base_url=self.expression_service_url, timeout=60.0)
        self.ensemble_client = ServiceClient(base_url=self.ensemble_service_url, timeout=30.0)
    
    async def get_all_predictions(
        self,
        patient_id: str,
        disease_code: str,
        token: str
    ) -> Dict[str, Any]:
        """
        Get predictions from all available analysis services
        
        Args:
            patient_id: Patient ID
            disease_code: Disease code
            token: Auth token
            
        Returns:
            Dictionary with all predictions
        """
        predictions = {
            "genomic": None,
            "expression": None,
            "ensemble": None
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get genomic predictions (PRS)
        try:
            genomic_profiles = await self.genomic_client.get(
                f"/genomic-profiles?patient_id={patient_id}",
                headers=headers
            )
            if genomic_profiles:
                # Get PRS scores
                prs_scores = await self.genomic_client.get(
                    f"/genomic-profiles/{genomic_profiles[0]['id']}/prs?disease_code={disease_code}",
                    headers=headers
                )
                predictions["genomic"] = prs_scores
        except Exception as e:
            logger.warning(f"Could not get genomic predictions: {e}")
        
        # Get expression predictions
        try:
            expression_profiles = await self.expression_client.get(
                f"/expression-profiles?patient_id={patient_id}",
                headers=headers
            )
            if expression_profiles:
                # Get signature scores
                signatures = await self.expression_client.post(
                    f"/expression-profiles/{expression_profiles[0]['id']}/signatures",
                    json={"signatures": ["disease_breast_cancer"], "method": "ssGSEA"},
                    headers=headers
                )
                predictions["expression"] = signatures
        except Exception as e:
            logger.warning(f"Could not get expression predictions: {e}")
        
        return predictions

