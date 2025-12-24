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
        self.ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
        self.clinical_service_url = os.getenv("CLINICAL_DATA_SERVICE_URL", "http://clinical-data-service:8000")
        self.pharmacogenomics_service_url = os.getenv("PHARMACOGENOMICS_SERVICE_URL", "http://pharmacogenomics-service:8000")
        self.xai_service_url = os.getenv("XAI_SERVICE_URL", "http://explainable-ai-service:8000")
        
        self.genomic_client = ServiceClient(base_url=self.genomic_service_url, timeout=60.0)
        self.expression_client = ServiceClient(base_url=self.expression_service_url, timeout=60.0)
        self.ensemble_client = ServiceClient(base_url=self.ensemble_service_url, timeout=30.0)
        self.ml_client = ServiceClient(base_url=self.ml_service_url, timeout=60.0)
        self.clinical_client = ServiceClient(base_url=self.clinical_service_url, timeout=30.0)
        self.pharmacogenomics_client = ServiceClient(base_url=self.pharmacogenomics_service_url, timeout=30.0)
        self.xai_client = ServiceClient(base_url=self.xai_service_url, timeout=60.0)
    
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
            "ensemble": None,
            "ml": None,
            "clinical": None,
            "pharmacogenomics": None
        }
        
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
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
        
        # Get ML predictions (disease prediction, anomaly detection)
        try:
            # Get patient expression data for ML service
            patient_data = await self._get_patient_data_for_ml(patient_id, headers)
            if patient_data:
                # Disease prediction
                disease_pred = await self.ml_client.post(
                    "/analysis/disease-prediction",
                    json={
                        "network_id": f"patient_{patient_id}",
                        "expression_data": patient_data.get("expression_data", {}),
                        "network_structure": patient_data.get("network_structure")
                    },
                    headers=headers
                )
                predictions["ml"] = {
                    "disease_prediction": disease_pred,
                    "anomaly_detection": None  # Can be added if needed
                }
        except Exception as e:
            logger.warning(f"Could not get ML predictions: {e}")
        
        # Get clinical data
        try:
            clinical_data = await self.clinical_client.get(
                f"/clinical-data?patient_id={patient_id}",
                headers=headers
            )
            predictions["clinical"] = clinical_data
        except Exception as e:
            logger.warning(f"Could not get clinical data: {e}")
        
        # Get pharmacogenomics predictions
        try:
            pharm_pred = await self.pharmacogenomics_client.post(
                "/predict-response",
                json={"patient_id": patient_id, "drug_id": "default"},
                headers=headers
            )
            predictions["pharmacogenomics"] = pharm_pred
        except Exception as e:
            logger.warning(f"Could not get pharmacogenomics predictions: {e}")
        
        # Get ensemble prediction (combines all)
        try:
            ensemble_pred = await self.ensemble_client.post(
                "/predict",
                json={
                    "patient_id": patient_id,
                    "disease_code": disease_code,
                    "predictions": predictions
                },
                headers=headers
            )
            predictions["ensemble"] = ensemble_pred
        except Exception as e:
            logger.warning(f"Could not get ensemble prediction: {e}")
            # Create simple ensemble if service unavailable
            predictions["ensemble"] = self._create_simple_ensemble(predictions)
        
        return predictions
    
    async def get_explanation(
        self,
        prediction_id: str,
        patient_id: str,
        prediction_value: float,
        features: Dict[str, Any],
        method: str = "shap",
        token: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Get explanation for a prediction from XAI service
        
        Args:
            prediction_id: Prediction ID
            patient_id: Patient ID
            prediction_value: Prediction value
            features: Feature values
            method: Explanation method ("shap", "lime", "both")
            token: Auth token
            
        Returns:
            Explanation dictionary or None
        """
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        
        try:
            if method in ["shap", "both"]:
                explanation = await self.xai_client.post(
                    "/shap/explain",
                    json={
                        "prediction_id": prediction_id,
                        "patient_id": patient_id,
                        "prediction_value": prediction_value,
                        "model_type": "ensemble",
                        "features": features
                    },
                    headers=headers
                )
                return explanation
            elif method == "lime":
                explanation = await self.xai_client.post(
                    "/lime/explain",
                    json={
                        "prediction_id": prediction_id,
                        "patient_id": patient_id,
                        "prediction_value": prediction_value,
                        "features": features
                    },
                    headers=headers
                )
                return explanation
        except Exception as e:
            logger.warning(f"Could not get explanation from XAI service: {e}")
            return None
        
        return None
    
    async def _get_patient_data_for_ml(
        self,
        patient_id: str,
        headers: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Get patient data formatted for ML service"""
        try:
            # Try to get expression profile
            expression_profiles = await self.expression_client.get(
                f"/expression-profiles?patient_id={patient_id}",
                headers=headers
            )
            
            if expression_profiles and len(expression_profiles) > 0:
                profile_id = expression_profiles[0].get("id")
                profile_data = await self.expression_client.get(
                    f"/expression-profiles/{profile_id}",
                    headers=headers
                )
                
                # Format for ML service
                return {
                    "expression_data": profile_data.get("expression_data", {}),
                    "network_structure": profile_data.get("network_structure")
                }
        except Exception as e:
            logger.warning(f"Could not get patient data for ML: {e}")
        
        return None
    
    def _create_simple_ensemble(self, predictions: Dict[str, Any]) -> Dict[str, Any]:
        """Create simple ensemble prediction when ensemble service unavailable"""
        risk_scores = []
        
        # Extract risk scores from different predictions
        if predictions.get("genomic"):
            prs = predictions["genomic"].get("prs_score", 0.0)
            if prs:
                risk_scores.append(prs)
        
        if predictions.get("ml"):
            ml_pred = predictions["ml"].get("disease_prediction", {})
            top_pred = ml_pred.get("top_prediction", {})
            if top_pred:
                risk_scores.append(top_pred.get("risk_score", 0.0))
        
        # Calculate ensemble score
        ensemble_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
        
        return {
            "risk_score": ensemble_score,
            "confidence": 0.7 if len(risk_scores) > 1 else 0.5,
            "methods_used": [k for k, v in predictions.items() if v is not None],
            "ensemble_method": "simple_average"
        }

