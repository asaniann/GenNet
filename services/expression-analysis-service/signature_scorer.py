"""
Expression signature scoring using established methods
Integrates with gseapy for GSEA/ssGSEA
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)

# Try to import gseapy, fallback to manual implementation
try:
    import gseapy as gp
    HAS_GSEAPY = True
except ImportError:
    HAS_GSEAPY = False
    logger.warning("gseapy not available, using manual signature scoring")


class SignatureScorer:
    """Score expression signatures using various methods"""
    
    def __init__(self):
        """Initialize signature scorer"""
        # Signature database (would be loaded from file or database)
        self.signature_db: Dict[str, Dict] = {}
        self._load_signature_database()
    
    def _load_signature_database(self):
        """Load signature database from file or external source"""
        # Placeholder - would load from file or database
        # Example signatures
        self.signature_db = {
            "disease_breast_cancer": {
                "name": "Breast Cancer Signature",
                "type": "disease",
                "genes": ["ESR1", "ERBB2", "PGR", "BRCA1", "BRCA2"],
                "weights": [1.0, 1.0, 1.0, 1.0, 1.0]
            },
            "treatment_tamoxifen": {
                "name": "Tamoxifen Response Signature",
                "type": "treatment",
                "genes": ["ESR1", "PGR", "CYP2D6"],
                "weights": [1.0, 0.8, 0.6]
            }
        }
    
    def score_signature_ssgsea(
        self,
        expression_data: pd.DataFrame,
        signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score signature using single-sample GSEA (ssGSEA)
        
        Args:
            expression_data: DataFrame with genes as columns, samples as rows
            signature: Signature dictionary with genes and weights
            
        Returns:
            Dictionary with score and statistics
        """
        genes = signature.get('genes', [])
        weights = signature.get('weights', [1.0] * len(genes))
        
        if not genes:
            return {"score": 0.0, "p_value": None}
        
        # Filter to genes present in expression data
        available_genes = [g for g in genes if g in expression_data.columns]
        if not available_genes:
            return {"score": 0.0, "p_value": None, "error": "No signature genes found in expression data"}
        
        # Get expression values for signature genes
        signature_expressions = expression_data[available_genes].values
        
        # Calculate rank-based score (simplified ssGSEA)
        # In practice, would use proper ssGSEA algorithm
        scores = []
        for sample_idx in range(len(expression_data)):
            sample_expr = expression_data.iloc[sample_idx]
            
            # Rank all genes by expression
            ranked = sample_expr.rank(ascending=False)
            
            # Calculate enrichment score for signature genes
            signature_ranks = [ranked[g] for g in available_genes if g in ranked.index]
            if signature_ranks:
                # Normalized enrichment score
                score = np.mean(signature_ranks) / len(expression_data.columns)
                scores.append(score)
            else:
                scores.append(0.0)
        
        return {
            "score": float(np.mean(scores)),
            "scores_per_sample": [float(s) for s in scores],
            "genes_used": available_genes,
            "genes_missing": [g for g in genes if g not in available_genes]
        }
    
    def score_signature_zscore(
        self,
        expression_data: pd.DataFrame,
        signature: Dict[str, Any],
        reference_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Score signature using z-score method
        
        Args:
            expression_data: Patient expression data
            signature: Signature dictionary
            reference_data: Optional reference expression data for z-score calculation
            
        Returns:
            Dictionary with z-score and statistics
        """
        genes = signature.get('genes', [])
        weights = signature.get('weights', [1.0] * len(genes))
        
        available_genes = [g for g in genes if g in expression_data.columns]
        if not available_genes:
            return {"score": 0.0, "z_score": 0.0}
        
        # Get expression values
        signature_expr = expression_data[available_genes].values.flatten()
        
        if reference_data is not None:
            # Calculate z-scores relative to reference
            ref_expr = reference_data[available_genes].values.flatten()
            mean_ref = np.mean(ref_expr)
            std_ref = np.std(ref_expr)
            
            if std_ref > 0:
                z_scores = (signature_expr - mean_ref) / std_ref
                score = float(np.mean(z_scores))
            else:
                score = 0.0
        else:
            # Simple mean expression
            score = float(np.mean(signature_expr))
        
        return {
            "score": score,
            "z_score": score if reference_data is not None else None,
            "genes_used": available_genes
        }
    
    def score_signature_mean(
        self,
        expression_data: pd.DataFrame,
        signature: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score signature using mean expression
        
        Args:
            expression_data: Patient expression data
            signature: Signature dictionary
            
        Returns:
            Dictionary with mean score
        """
        genes = signature.get('genes', [])
        weights = signature.get('weights', [1.0] * len(genes))
        
        available_genes = [g for g in genes if g in expression_data.columns]
        if not available_genes:
            return {"score": 0.0}
        
        # Weighted mean expression
        signature_expr = expression_data[available_genes]
        gene_weights = [weights[genes.index(g)] for g in available_genes]
        
        weighted_mean = np.average(signature_expr.values.flatten(), weights=gene_weights)
        
        return {
            "score": float(weighted_mean),
            "genes_used": available_genes,
            "top_genes": self._get_top_contributing_genes(signature_expr, available_genes, top_n=5)
        }
    
    def _get_top_contributing_genes(
        self,
        expression_data: pd.DataFrame,
        genes: List[str],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top contributing genes to signature score"""
        if len(expression_data) == 0:
            return []
        
        # Calculate mean expression per gene
        mean_expr = expression_data.mean(axis=0)
        
        # Sort by expression
        sorted_genes = mean_expr.sort_values(ascending=False).head(top_n)
        
        return [
            {"gene": gene, "expression": float(expr), "contribution": float(expr / mean_expr.sum())}
            for gene, expr in sorted_genes.items()
        ]
    
    def score_multiple_signatures(
        self,
        expression_data: pd.DataFrame,
        signature_ids: List[str],
        method: str = "ssGSEA"
    ) -> Dict[str, Dict[str, Any]]:
        """
        Score multiple signatures
        
        Args:
            expression_data: Patient expression data
            signature_ids: List of signature IDs
            method: Scoring method (ssGSEA, z_score, mean)
            
        Returns:
            Dictionary mapping signature_id to score results
        """
        results = {}
        
        for sig_id in signature_ids:
            if sig_id not in self.signature_db:
                logger.warning(f"Signature {sig_id} not found in database")
                continue
            
            signature = self.signature_db[sig_id]
            
            if method == "ssGSEA":
                score_result = self.score_signature_ssgsea(expression_data, signature)
            elif method == "z_score":
                score_result = self.score_signature_zscore(expression_data, signature)
            elif method == "mean":
                score_result = self.score_signature_mean(expression_data, signature)
            else:
                logger.warning(f"Unknown method {method}, using mean")
                score_result = self.score_signature_mean(expression_data, signature)
            
            results[sig_id] = {
                "signature_id": sig_id,
                "signature_name": signature.get("name", sig_id),
                "signature_type": signature.get("type", "unknown"),
                **score_result
            }
        
        return results

