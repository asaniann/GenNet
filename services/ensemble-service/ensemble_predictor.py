"""
Ensemble prediction methods
Combining predictions from multiple analysis methods
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class EnsemblePredictor:
    """Combine predictions from multiple methods"""
    
    def predict_weighted_voting(
        self,
        predictions: List[Dict[str, Any]],
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Weighted voting ensemble
        
        Args:
            predictions: List of predictions from different methods
            weights: Optional method-specific weights
            
        Returns:
            Ensemble prediction
        """
        if not predictions:
            raise ValueError("No predictions provided")
        
        # Default weights (would be learned from validation data)
        default_weights = {
            "prs": 0.25,
            "expression": 0.30,
            "grn": 0.25,
            "multi_omics": 0.20
        }
        
        if weights is None:
            weights = default_weights
        
        # Extract scores and confidences
        scores = []
        confidences = []
        method_scores = {}
        
        for pred in predictions:
            method = pred.get("method", "unknown")
            score = pred.get("risk_score", 0.0)
            confidence = pred.get("confidence", 0.5)
            
            weight = weights.get(method, 0.1)
            weighted_score = score * weight * confidence
            
            scores.append(weighted_score)
            confidences.append(confidence)
            method_scores[method] = {
                "score": score,
                "confidence": confidence,
                "weight": weight,
                "contribution": weighted_score
            }
        
        # Calculate ensemble score
        total_weight = sum(confidences)  # Normalize by total confidence
        ensemble_score = sum(scores) / total_weight if total_weight > 0 else np.mean([p.get("risk_score", 0.0) for p in predictions])
        
        # Calculate ensemble confidence
        ensemble_confidence = np.mean(confidences)
        
        # Calculate agreement
        agreement = self._calculate_agreement(predictions)
        
        return {
            "risk_score": float(ensemble_score),
            "confidence": float(ensemble_confidence),
            "method_contributions": method_scores,
            "agreement_score": float(agreement),
            "ensemble_strategy": "weighted_voting"
        }
    
    def predict_stacking(
        self,
        predictions: List[Dict[str, Any]],
        meta_model: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Stacking ensemble (would use trained meta-learner)
        
        Args:
            predictions: List of predictions
            meta_model: Optional pre-trained meta-learner
            
        Returns:
            Ensemble prediction
        """
        # Extract features from predictions
        features = np.array([
            [
                pred.get("risk_score", 0.0),
                pred.get("confidence", 0.5),
                pred.get("method", "unknown") == "prs",  # One-hot encoding
                pred.get("method", "unknown") == "expression",
                pred.get("method", "unknown") == "grn"
            ]
            for pred in predictions
        ])
        
        if meta_model:
            # Use trained meta-learner
            ensemble_score = float(meta_model.predict(features)[0])
            ensemble_confidence = float(meta_model.predict_proba(features)[0].max())
        else:
            # Fallback to weighted voting
            return self.predict_weighted_voting(predictions)
        
        return {
            "risk_score": ensemble_score,
            "confidence": ensemble_confidence,
            "ensemble_strategy": "stacking"
        }
    
    def predict_bayesian_averaging(
        self,
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Bayesian model averaging
        
        Args:
            predictions: List of predictions
            
        Returns:
            Ensemble prediction with uncertainty
        """
        # Extract scores and uncertainties
        scores = [pred.get("risk_score", 0.0) for pred in predictions]
        confidences = [pred.get("confidence", 0.5) for pred in predictions]
        
        # Use confidence as inverse variance
        precisions = [c for c in confidences]  # Precision = confidence
        
        # Weighted average
        total_precision = sum(precisions)
        if total_precision > 0:
            ensemble_score = sum(s * p for s, p in zip(scores, precisions)) / total_precision
            ensemble_uncertainty = 1.0 / total_precision
            ensemble_confidence = 1.0 - ensemble_uncertainty
        else:
            ensemble_score = np.mean(scores)
            ensemble_confidence = np.mean(confidences)
        
        # Calculate credible interval (95%)
        std_dev = np.std(scores)
        ci_lower = ensemble_score - 1.96 * std_dev
        ci_upper = ensemble_score + 1.96 * std_dev
        
        return {
            "risk_score": float(ensemble_score),
            "confidence": float(ensemble_confidence),
            "confidence_interval_lower": float(ci_lower),
            "confidence_interval_upper": float(ci_upper),
            "ensemble_strategy": "bayesian_averaging"
        }
    
    def _calculate_agreement(self, predictions: List[Dict[str, Any]]) -> float:
        """Calculate agreement between predictions"""
        if len(predictions) < 2:
            return 1.0
        
        scores = [pred.get("risk_score", 0.0) for pred in predictions]
        
        # Calculate coefficient of variation (lower = more agreement)
        mean_score = np.mean(scores)
        std_score = np.std(scores)
        
        if mean_score > 0:
            cv = std_score / mean_score
            # Convert to agreement score (0-1, higher = more agreement)
            agreement = 1.0 / (1.0 + cv)
        else:
            agreement = 1.0 if std_score == 0 else 0.0
        
        return float(agreement)
    
    def aggregate_evidence(
        self,
        predictions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate evidence from all predictions"""
        evidence = {
            "genomic": None,
            "expression": None,
            "grn": None,
            "clinical": None,
            "multi_omics": None
        }
        
        for pred in predictions:
            method = pred.get("method", "")
            if "prs" in method or "genomic" in method:
                evidence["genomic"] = pred.get("evidence", {})
            elif "expression" in method:
                evidence["expression"] = pred.get("evidence", {})
            elif "grn" in method:
                evidence["grn"] = pred.get("evidence", {})
            elif "clinical" in method:
                evidence["clinical"] = pred.get("evidence", {})
            elif "multi_omics" in method:
                evidence["multi_omics"] = pred.get("evidence", {})
        
        # Create summary
        summary = {}
        for key, value in evidence.items():
            if value:
                summary[key] = self._summarize_evidence(value)
        
        return {
            "detailed": evidence,
            "summary": summary
        }
    
    def _summarize_evidence(self, evidence: Dict) -> str:
        """Create text summary of evidence"""
        # Placeholder - would create natural language summary
        if isinstance(evidence, dict):
            return f"Evidence from {len(evidence)} sources"
        return "Evidence available"

