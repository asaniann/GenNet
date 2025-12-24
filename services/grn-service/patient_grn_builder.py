"""
Patient-Specific GRN Construction
Reference-based, de novo, and hybrid approaches
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
import os
import sys

# Import shared HTTP client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient

logger = logging.getLogger(__name__)


class PatientGRNBuilder:
    """Build patient-specific GRN from expression data"""
    
    def __init__(self):
        """Initialize builder with service clients"""
        # Service URLs from environment
        patient_service_url = os.getenv("PATIENT_DATA_SERVICE_URL", "http://patient-data-service:8000")
        ml_service_url = os.getenv("ML_SERVICE_URL", "http://ml-service:8000")
        expression_service_url = os.getenv("EXPRESSION_ANALYSIS_SERVICE_URL", "http://expression-analysis-service:8000")
        
        self.patient_client = ServiceClient(base_url=patient_service_url, timeout=30.0)
        self.ml_client = ServiceClient(base_url=ml_service_url, timeout=60.0)
        self.expression_client = ServiceClient(base_url=expression_service_url, timeout=30.0)
    
    async def build_patient_grn(
        self,
        patient_id: str,
        method: str = "hybrid",
        reference_grn_id: Optional[str] = None,
        expression_data: Optional[pd.DataFrame] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build patient-specific GRN
        
        Args:
            patient_id: Patient ID
            method: Construction method ("reference", "de_novo", "hybrid")
            reference_grn_id: Optional reference GRN ID for reference-based methods
            expression_data: Optional expression data (if not provided, will fetch)
            token: Optional auth token for service calls
            
        Returns:
            Dictionary with network_id, nodes, edges, and metadata
        """
        logger.info(f"Building patient-specific GRN for patient: {patient_id}, method: {method}")
        
        # Get expression data if not provided
        if expression_data is None:
            expression_data = await self._get_patient_expression_data(patient_id, token)
        
        if expression_data is None or expression_data.empty:
            raise ValueError(f"No expression data available for patient: {patient_id}")
        
        # Build GRN based on method
        if method == "reference":
            return await self._build_reference_based(patient_id, expression_data, reference_grn_id, token)
        elif method == "de_novo":
            return await self._build_de_novo(patient_id, expression_data, token)
        elif method == "hybrid":
            return await self._build_hybrid(patient_id, expression_data, reference_grn_id, token)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    async def _build_reference_based(
        self,
        patient_id: str,
        expression_data: pd.DataFrame,
        reference_grn_id: Optional[str],
        token: Optional[str]
    ) -> Dict[str, Any]:
        """Build GRN by adjusting reference network based on patient expression"""
        logger.info(f"Building reference-based GRN for patient: {patient_id}")
        
        # If no reference provided, use default population reference
        if reference_grn_id is None:
            # In production, would fetch from reference network database
            # For now, use a placeholder
            reference_grn_id = "default_population_reference"
        
        # Get reference network (would fetch from GRN service or database)
        # For now, we'll infer de novo and then adjust
        reference_edges = await self._infer_grn_from_expression(expression_data, token)
        
        # Adjust edges based on patient expression
        adjusted_edges = self._adjust_edges_from_expression(reference_edges, expression_data)
        
        # Create nodes from expression data
        nodes = self._create_nodes_from_expression(expression_data)
        
        return {
            "patient_id": patient_id,
            "method": "reference",
            "reference_grn_id": reference_grn_id,
            "nodes": nodes,
            "edges": adjusted_edges,
            "metadata": {
                "num_nodes": len(nodes),
                "num_edges": len(adjusted_edges),
                "expression_samples": expression_data.shape[0],
                "expression_genes": expression_data.shape[1]
            }
        }
    
    async def _build_de_novo(
        self,
        patient_id: str,
        expression_data: pd.DataFrame,
        token: Optional[str]
    ) -> Dict[str, Any]:
        """Build GRN de novo from patient expression data"""
        logger.info(f"Building de novo GRN for patient: {patient_id}")
        
        # Infer GRN directly from expression
        edges = await self._infer_grn_from_expression(expression_data, token)
        
        # Create nodes
        nodes = self._create_nodes_from_expression(expression_data)
        
        return {
            "patient_id": patient_id,
            "method": "de_novo",
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "num_nodes": len(nodes),
                "num_edges": len(edges),
                "expression_samples": expression_data.shape[0],
                "expression_genes": expression_data.shape[1]
            }
        }
    
    async def _build_hybrid(
        self,
        patient_id: str,
        expression_data: pd.DataFrame,
        reference_grn_id: Optional[str],
        token: Optional[str]
    ) -> Dict[str, Any]:
        """Build GRN using hybrid approach (combine reference and de novo)"""
        logger.info(f"Building hybrid GRN for patient: {patient_id}")
        
        # Build both reference-based and de novo
        reference_result = await self._build_reference_based(patient_id, expression_data, reference_grn_id, token)
        denovo_result = await self._build_de_novo(patient_id, expression_data, token)
        
        # Combine edges (weight by confidence/data quality)
        combined_edges = self._combine_edges(
            reference_result["edges"],
            denovo_result["edges"],
            expression_data
        )
        
        # Use union of nodes
        all_nodes = {node["id"]: node for node in reference_result["nodes"]}
        for node in denovo_result["nodes"]:
            all_nodes[node["id"]] = node
        
        return {
            "patient_id": patient_id,
            "method": "hybrid",
            "reference_grn_id": reference_grn_id,
            "nodes": list(all_nodes.values()),
            "edges": combined_edges,
            "metadata": {
                "num_nodes": len(all_nodes),
                "num_edges": len(combined_edges),
                "expression_samples": expression_data.shape[0],
                "expression_genes": expression_data.shape[1],
                "reference_edges": len(reference_result["edges"]),
                "denovo_edges": len(denovo_result["edges"])
            }
        }
    
    async def _get_patient_expression_data(
        self,
        patient_id: str,
        token: Optional[str]
    ) -> Optional[pd.DataFrame]:
        """Get patient expression data from Patient Data Service"""
        try:
            # In production, would fetch from S3 or expression service
            # For now, return None (would need actual implementation)
            # This would involve:
            # 1. Get patient data from Patient Data Service
            # 2. Get expression file location from S3
            # 3. Load and parse expression file
            logger.warning(f"Expression data fetching not fully implemented for patient: {patient_id}")
            return None
        except Exception as e:
            logger.error(f"Error fetching expression data: {e}")
            return None
    
    async def _infer_grn_from_expression(
        self,
        expression_data: pd.DataFrame,
        token: Optional[str],
        method: str = "genie3"
    ) -> List[Dict[str, Any]]:
        """Infer GRN edges from expression data using ML Service"""
        try:
            # Convert DataFrame to format expected by ML Service
            expression_dict = {
                "data": expression_data.to_dict(orient="records"),
                "genes": expression_data.columns.tolist(),
                "samples": expression_data.index.tolist()
            }
            
            # Call ML Service for GRN inference
            # Note: This is a placeholder - actual implementation would call ML service
            # For now, return empty edges (would be implemented with actual service call)
            logger.info(f"Inferring GRN using {method} from ML Service")
            
            # Placeholder: In production, would make actual API call:
            # response = await self.ml_client.post(
            #     f"/infer-grn?method={method}",
            #     json=expression_dict,
            #     headers={"Authorization": f"Bearer {token}"} if token else {}
            # )
            # return response.get("edges", [])
            
            # For now, return empty list (would be replaced with actual inference)
            return []
            
        except Exception as e:
            logger.error(f"Error inferring GRN: {e}")
            return []
    
    def _adjust_edges_from_expression(
        self,
        reference_edges: List[Dict[str, Any]],
        expression_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Adjust reference edges based on patient expression"""
        adjusted = []
        
        for edge in reference_edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if source in expression_data.columns and target in expression_data.columns:
                # Calculate correlation in patient data
                correlation = expression_data[source].corr(expression_data[target])
                
                # Adjust weight based on correlation
                original_weight = edge.get("weight", 0.5)
                adjusted_weight = original_weight * (1 + correlation) / 2
                
                adjusted_edge = edge.copy()
                adjusted_edge["weight"] = adjusted_weight
                adjusted_edge["patient_correlation"] = correlation
                adjusted.append(adjusted_edge)
            else:
                # Keep edge but reduce weight if genes not in patient data
                adjusted_edge = edge.copy()
                adjusted_edge["weight"] = edge.get("weight", 0.5) * 0.5
                adjusted.append(adjusted_edge)
        
        return adjusted
    
    def _create_nodes_from_expression(self, expression_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create node list from expression data genes"""
        nodes = []
        for gene in expression_data.columns:
            nodes.append({
                "id": gene,
                "label": gene,
                "node_type": "gene",
                "properties": {
                    "mean_expression": float(expression_data[gene].mean()),
                    "std_expression": float(expression_data[gene].std())
                }
            })
        return nodes
    
    def _combine_edges(
        self,
        reference_edges: List[Dict[str, Any]],
        denovo_edges: List[Dict[str, Any]],
        expression_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Combine edges from reference and de novo methods"""
        # Create edge dictionary for quick lookup
        edge_dict = {}
        
        # Add reference edges with weight 0.6
        for edge in reference_edges:
            key = (edge["source"], edge["target"])
            edge_dict[key] = {
                **edge,
                "weight": edge.get("weight", 0.5) * 0.6,
                "source": "reference"
            }
        
        # Add de novo edges with weight 0.4, or combine if exists
        for edge in denovo_edges:
            key = (edge["source"], edge["target"])
            if key in edge_dict:
                # Combine weights
                edge_dict[key]["weight"] = (
                    edge_dict[key]["weight"] * 0.6 + edge.get("weight", 0.5) * 0.4
                )
                edge_dict[key]["source"] = "hybrid"
            else:
                edge_dict[key] = {
                    **edge,
                    "weight": edge.get("weight", 0.5) * 0.4,
                    "source": "de_novo"
                }
        
        return list(edge_dict.values())

