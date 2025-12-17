"""
Disease Prediction Module
Predicts disease associations using network-based and ML methods
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DiseaseCategory(str, Enum):
    """Disease categories"""
    CANCER = "cancer"
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    METABOLIC = "metabolic"
    IMMUNE = "immune"
    OTHER = "other"


@dataclass
class DiseasePrediction:
    """Disease prediction result"""
    disease_code: str
    disease_name: str
    category: DiseaseCategory
    risk_score: float
    confidence: float
    evidence: List[str]
    network_perturbations: Dict[str, float]


class DiseasePredictor:
    """Predict disease associations from network data"""
    
    def __init__(self):
        # Disease signatures (simplified - would be loaded from database in production)
        self.disease_signatures = self._load_disease_signatures()
    
    def predict_disease(
        self,
        network_id: str,
        expression_data: Dict[str, Any],
        network_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Predict disease associations from network
        
        Args:
            network_id: Network identifier
            expression_data: Expression data
            network_structure: Network structure
            
        Returns:
            Disease predictions
        """
        try:
            # Extract network features
            features = self._extract_features(expression_data, network_structure)
            
            # Network-based prediction
            network_predictions = self._predict_from_network(features, network_structure)
            
            # Signature-based prediction
            signature_predictions = self._predict_from_signatures(features)
            
            # Ensemble prediction
            ensemble_predictions = self._ensemble_predictions(
                network_predictions,
                signature_predictions
            )
            
            # Rank predictions
            ensemble_predictions.sort(key=lambda x: x.risk_score, reverse=True)
            
            return {
                "network_id": network_id,
                "predictions": [self._prediction_to_dict(p) for p in ensemble_predictions],
                "count": len(ensemble_predictions),
                "top_prediction": self._prediction_to_dict(ensemble_predictions[0]) if ensemble_predictions else None,
                "prediction_method": "ensemble"
            }
            
        except Exception as e:
            logger.error(f"Error predicting disease: {e}")
            raise
    
    def _load_disease_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Load disease signatures (simplified version)"""
        # In production, this would load from a database
        return {
            "ICD10:C50": {  # Breast cancer
                "name": "Breast Cancer",
                "category": DiseaseCategory.CANCER,
                "signature_genes": ["BRCA1", "BRCA2", "TP53", "ERBB2"],
                "pathways": ["cell_cycle", "apoptosis"]
            },
            "ICD10:I25": {  # Ischemic heart disease
                "name": "Ischemic Heart Disease",
                "category": DiseaseCategory.CARDIOVASCULAR,
                "signature_genes": ["APOB", "LDLR", "PCSK9"],
                "pathways": ["lipid_metabolism"]
            }
        }
    
    def _extract_features(
        self,
        expression_data: Dict[str, Any],
        network_structure: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract features from expression data and network"""
        features = {
            "expression_values": {},
            "network_metrics": {}
        }
        
        # Extract expression values
        if isinstance(expression_data, dict):
            if "nodes" in expression_data:
                for node in expression_data["nodes"]:
                    if isinstance(node, dict):
                        node_id = node.get("id", node.get("label", ""))
                        expr_value = node.get("expression", node.get("value", 0.0))
                        if node_id:
                            features["expression_values"][node_id] = expr_value
        
        # Extract network metrics
        if network_structure:
            nodes = network_structure.get("nodes", [])
            edges = network_structure.get("edges", [])
            
            features["network_metrics"] = {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "density": len(edges) / (len(nodes) * (len(nodes) - 1)) if len(nodes) > 1 else 0.0
            }
        
        return features
    
    def _predict_from_network(
        self,
        features: Dict[str, Any],
        network_structure: Optional[Dict[str, Any]]
    ) -> List[DiseasePrediction]:
        """Predict diseases based on network perturbations"""
        predictions = []
        
        expression_values = features.get("expression_values", {})
        
        # Calculate network perturbations for each disease
        for disease_code, disease_info in self.disease_signatures.items():
            signature_genes = disease_info.get("signature_genes", [])
            
            # Calculate perturbation score
            perturbation_scores = {}
            total_perturbation = 0.0
            matched_genes = 0
            
            for gene in signature_genes:
                if gene in expression_values:
                    expr_value = expression_values[gene]
                    # Normalize and calculate deviation
                    perturbation = abs(expr_value - 0.5)  # Assuming 0.5 is normal
                    perturbation_scores[gene] = perturbation
                    total_perturbation += perturbation
                    matched_genes += 1
            
            # Calculate risk score
            if matched_genes > 0:
                avg_perturbation = total_perturbation / matched_genes
                risk_score = min(1.0, avg_perturbation * 2.0)  # Scale to 0-1
                confidence = min(1.0, matched_genes / len(signature_genes))
                
                evidence = [
                    f"{matched_genes}/{len(signature_genes)} signature genes present",
                    f"Average perturbation: {avg_perturbation:.2f}"
                ]
                
                predictions.append(DiseasePrediction(
                    disease_code=disease_code,
                    disease_name=disease_info["name"],
                    category=disease_info["category"],
                    risk_score=risk_score,
                    confidence=confidence,
                    evidence=evidence,
                    network_perturbations=perturbation_scores
                ))
        
        return predictions
    
    def _predict_from_signatures(
        self,
        features: Dict[str, Any]
    ) -> List[DiseasePrediction]:
        """Predict diseases based on expression signatures"""
        predictions = []
        
        expression_values = features.get("expression_values", {})
        
        # Match against disease signatures
        for disease_code, disease_info in self.disease_signatures.items():
            signature_genes = disease_info.get("signature_genes", [])
            
            # Calculate signature match score
            matches = sum(1 for gene in signature_genes if gene in expression_values)
            match_score = matches / len(signature_genes) if signature_genes else 0.0
            
            if match_score > 0.3:  # Threshold for prediction
                # Calculate risk based on expression levels
                matched_expressions = [
                    expression_values[gene] for gene in signature_genes
                    if gene in expression_values
                ]
                
                if matched_expressions:
                    avg_expression = np.mean(matched_expressions)
                    risk_score = min(1.0, avg_expression * match_score)
                    
                    evidence = [
                        f"Signature match: {matches}/{len(signature_genes)} genes",
                        f"Average expression: {avg_expression:.2f}"
                    ]
                    
                    predictions.append(DiseasePrediction(
                        disease_code=disease_code,
                        disease_name=disease_info["name"],
                        category=disease_info["category"],
                        risk_score=risk_score,
                        confidence=match_score,
                        evidence=evidence,
                        network_perturbations={}
                    ))
        
        return predictions
    
    def _ensemble_predictions(
        self,
        network_predictions: List[DiseasePrediction],
        signature_predictions: List[DiseasePrediction]
    ) -> List[DiseasePrediction]:
        """Combine predictions from multiple methods"""
        # Combine predictions by disease code
        combined = {}
        
        # Add network predictions
        for pred in network_predictions:
            if pred.disease_code not in combined:
                combined[pred.disease_code] = pred
            else:
                # Average risk scores and combine evidence
                existing = combined[pred.disease_code]
                combined[pred.disease_code] = DiseasePrediction(
                    disease_code=pred.disease_code,
                    disease_name=pred.disease_name,
                    category=pred.category,
                    risk_score=(existing.risk_score + pred.risk_score) / 2.0,
                    confidence=(existing.confidence + pred.confidence) / 2.0,
                    evidence=existing.evidence + pred.evidence,
                    network_perturbations={**existing.network_perturbations, **pred.network_perturbations}
                )
        
        # Add signature predictions
        for pred in signature_predictions:
            if pred.disease_code not in combined:
                combined[pred.disease_code] = pred
            else:
                # Weighted combination
                existing = combined[pred.disease_code]
                # Network predictions weighted 0.6, signature 0.4
                combined[pred.disease_code] = DiseasePrediction(
                    disease_code=pred.disease_code,
                    disease_name=pred.disease_name,
                    category=pred.category,
                    risk_score=0.6 * existing.risk_score + 0.4 * pred.risk_score,
                    confidence=0.6 * existing.confidence + 0.4 * pred.confidence,
                    evidence=existing.evidence + pred.evidence,
                    network_perturbations=existing.network_perturbations
                )
        
        return list(combined.values())
    
    def _prediction_to_dict(self, prediction: DiseasePrediction) -> Dict[str, Any]:
        """Convert DiseasePrediction to dictionary"""
        return {
            "disease_code": prediction.disease_code,
            "disease_name": prediction.disease_name,
            "category": prediction.category.value,
            "risk_score": prediction.risk_score,
            "confidence": prediction.confidence,
            "evidence": prediction.evidence,
            "network_perturbations": prediction.network_perturbations
        }

