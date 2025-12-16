"""
Service clients for integrating with other GenNet services
Uses existing shared HTTP client utilities
"""

import os
import sys
from typing import Optional, Dict, Any
import logging

# Import shared HTTP client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class PatientDataServiceClient:
    """Client for Patient Data Service"""
    
    def __init__(self):
        base_url = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient-data-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=30.0)
    
    async def get_patient(self, patient_id: str, token: str) -> Optional[Dict[str, Any]]:
        """Get patient information"""
        try:
            response = await self.client.get(
                f"/patients/{patient_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            return response
        except Exception as e:
            logger.error(f"Error fetching patient {patient_id}: {e}")
            return None
    
    async def update_patient_data_flags(
        self,
        patient_id: str,
        has_genomic_data: bool,
        token: str
    ) -> bool:
        """Update patient data availability flags"""
        try:
            # This would be a PATCH endpoint in Patient Data Service
            # For now, we'll just log
            logger.info(f"Patient {patient_id} has genomic data: {has_genomic_data}")
            return True
        except Exception as e:
            logger.error(f"Error updating patient flags: {e}")
            return False


class GRNServiceClient:
    """Client for GRN Service - for network analysis integration"""
    
    def __init__(self):
        base_url = os.getenv("GRN_SERVICE_URL", "http://grn-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=60.0)
    
    async def create_network_from_variants(
        self,
        network_name: str,
        variants: list,
        user_id: int,
        token: str
    ) -> Optional[str]:
        """
        Create a GRN network from variant data
        This integrates genomic variants with network analysis
        
        Args:
            network_name: Name for the network
            variants: List of variant dictionaries
            user_id: User ID
            token: Auth token
            
        Returns:
            Network ID if successful
        """
        # Extract genes from variants
        genes = set()
        for variant in variants:
            if variant.get('gene'):
                genes.add(variant['gene'])
        
        # Create nodes from genes
        nodes = [{"id": gene, "label": gene, "type": "gene"} for gene in genes]
        
        # Create edges based on variant relationships
        # This is simplified - in practice would use pathway databases
        edges = []
        
        try:
            # Create network via GRN Service
            network_data = {
                "name": network_name,
                "description": f"Network derived from genomic variants",
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
            logger.error(f"Error creating network from variants: {e}")
            return None


class MLServiceClient:
    """Client for ML Service - for GRN inference if needed"""
    
    def __init__(self):
        base_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
        self.client = ServiceClient(base_url=base_url, timeout=120.0)
    
    async def infer_grn_from_expression(
        self,
        expression_data_path: str,
        method: str = "GENIE3",
        token: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Infer GRN from expression data using ML Service
        
        Args:
            expression_data_path: Path to expression data
            method: Inference method (ARACNE, GENIE3, GRNBoost2)
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
            logger.error(f"Error inferring GRN: {e}")
            return None

