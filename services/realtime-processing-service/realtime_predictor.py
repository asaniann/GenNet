"""
Real-time prediction pipeline
"""

from typing import Dict, Any, Optional
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class RealTimePredictor:
    """Generate real-time predictions from streaming data"""
    
    def __init__(self):
        """Initialize real-time predictor"""
        # Service URLs
        ensemble_service_url = os.getenv("ENSEMBLE_SERVICE_URL", "http://ensemble-service:8000")
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
        
        self.ensemble_client = ServiceClient(base_url=ensemble_service_url, timeout=30.0)
        self.ml_client = ServiceClient(base_url=ml_service_url, timeout=60.0)
    
    async def predict_from_event(
        self,
        event: Dict[str, Any],
        token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate prediction from event data
        
        Args:
            event: Event data dictionary
            token: Optional auth token
            
        Returns:
            Prediction dictionary or None
        """
        patient_id = event.get("patient_id")
        event_type = event.get("event_type")
        event_data = event.get("event_data", {})
        
        if not patient_id:
            return None
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        try:
            if event_type == "data_upload":
                # Trigger new prediction when data is uploaded
                prediction = await self._trigger_prediction(patient_id, event_data, headers)
                return prediction
            elif event_type == "update":
                # Update existing prediction
                prediction = await self._update_prediction(patient_id, event_data, headers)
                return prediction
        except Exception as e:
            logger.error(f"Error generating real-time prediction: {e}")
            return None
        
        return None
    
    async def _trigger_prediction(
        self,
        patient_id: str,
        event_data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Trigger new prediction"""
        try:
            # Call ensemble service for prediction
            prediction = await self.ensemble_client.post(
                "/predict",
                json={
                    "patient_id": patient_id,
                    "disease_code": event_data.get("disease_code", "ICD10:C50"),
                    "predictions": event_data.get("predictions", {})
                },
                headers=headers
            )
            return prediction
        except Exception as e:
            logger.error(f"Error triggering prediction: {e}")
            return None
    
    async def _update_prediction(
        self,
        patient_id: str,
        event_data: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Update existing prediction"""
        # Similar to trigger, but for updates
        return await self._trigger_prediction(patient_id, event_data, headers)

