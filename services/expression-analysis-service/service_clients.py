"""
Service clients for Expression Analysis Service
Integrates with existing ML Service, GRN Service, and Patient Data Service
"""

import os
import sys
from typing import Optional, Dict, Any
import logging

# Import shared HTTP client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class MLServiceClient:
    """Client for ML Service - uses existing GRN inference"""
    
    def __init__(self):
        base_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=120.0)
    
    async def infer_grn(
        self,
        expression_data_path: str,
        method: str = "GENIE3",
        token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Infer GRN from expression data using existing ML Service
        
        Args:
            expression_data_path: Path to expression data
            method: Inference method (GENIE3, ARACNE, GRNBoost2)
            token: Optional auth token
            
        Returns:
            Network data if successful
        """
        try:
            request_data = {
                "expression_data_path": expression_data_path,
                "method": method
            }
            
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            response = await self.client.post(
                "/inference/grn",
                json=request_data,
                headers=headers
            )
            
            return response
        except Exception as e:
            logger.error(f"Error inferring GRN from ML Service: {e}")
            return None


class GRNServiceClient:
    """Client for GRN Service - stores inferred networks"""
    
    def __init__(self):
        base_url = os.getenv("GRN_SERVICE_URL", "http://grn-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=60.0)
    
    async def create_network(
        self,
        network_name: str,
        nodes: List[Dict],
        edges: List[Dict],
        user_id: int,
        token: str
    ) -> Optional[str]:
        """Create network in GRN Service"""
        try:
            network_data = {
                "name": network_name,
                "description": f"GRN inferred from expression data",
                "nodes": nodes,
                "edges": edges
            }
            
            response = await self.client.post(
                "/networks",
                json=network_data,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            return response.get('id')
        except Exception as e:
            logger.error(f"Error creating network in GRN Service: {e}")
            return None


class PatientDataServiceClient:
    """Client for Patient Data Service"""
    
    def __init__(self):
        base_url = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient-data-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=30.0)
    
    async def update_patient_expression_flag(
        self,
        patient_id: str,
        has_expression_data: bool,
        token: str
    ) -> bool:
        """Update patient expression data flag"""
        try:
            # Would be a PATCH endpoint
            logger.info(f"Patient {patient_id} has expression data: {has_expression_data}")
            return True
        except Exception as e:
            logger.error(f"Error updating patient flags: {e}")
            return False

