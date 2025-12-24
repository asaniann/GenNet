"""
Network Perturbation Analysis
Compare patient GRN to reference networks and identify perturbations
"""

from typing import Dict, List, Any, Optional
import logging
import numpy as np

logger = logging.getLogger(__name__)


class PerturbationAnalyzer:
    """Analyze perturbations in patient-specific GRN compared to reference"""
    
    def analyze_perturbations(
        self,
        patient_grn: Dict[str, Any],
        reference_grn: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze perturbations between patient and reference GRN
        
        Args:
            patient_grn: Patient GRN with nodes and edges
            reference_grn: Reference GRN with nodes and edges
            
        Returns:
            Dictionary with perturbation analysis results
        """
        logger.info("Analyzing network perturbations")
        
        patient_edges = {(e["source"], e["target"]): e for e in patient_grn.get("edges", [])}
        reference_edges = {(e["source"], e["target"]): e for e in reference_grn.get("edges", [])}
        
        # Identify edge differences
        added_edges = set(patient_edges.keys()) - set(reference_edges.keys())
        removed_edges = set(reference_edges.keys()) - set(patient_edges.keys())
        common_edges = set(patient_edges.keys()) & set(reference_edges.keys())
        
        # Calculate weight changes for common edges
        weight_changes = []
        for edge_key in common_edges:
            patient_weight = patient_edges[edge_key].get("weight", 0.0)
            reference_weight = reference_edges[edge_key].get("weight", 0.0)
            weight_change = patient_weight - reference_weight
            
            if abs(weight_change) > 0.1:  # Significant change threshold
                weight_changes.append({
                    "source": edge_key[0],
                    "target": edge_key[1],
                    "patient_weight": patient_weight,
                    "reference_weight": reference_weight,
                    "change": weight_change,
                    "change_percent": (weight_change / reference_weight * 100) if reference_weight != 0 else 0
                })
        
        # Calculate perturbation scores
        perturbation_score = self._calculate_perturbation_score(
            len(added_edges),
            len(removed_edges),
            len(weight_changes),
            len(common_edges)
        )
        
        # Identify perturbed pathways (simplified - would use pathway databases)
        perturbed_pathways = self._identify_perturbed_pathways(
            list(added_edges) + list(removed_edges),
            weight_changes
        )
        
        return {
            "perturbation_score": perturbation_score,
            "edge_changes": {
                "added": len(added_edges),
                "removed": len(removed_edges),
                "modified": len(weight_changes),
                "unchanged": len(common_edges) - len(weight_changes)
            },
            "added_edges": [
                {"source": e[0], "target": e[1], "weight": patient_edges[e].get("weight")}
                for e in added_edges
            ],
            "removed_edges": [
                {"source": e[0], "target": e[1], "weight": reference_edges[e].get("weight")}
                for e in removed_edges
            ],
            "weight_changes": weight_changes,
            "perturbed_pathways": perturbed_pathways,
            "disease_associations": self._map_to_diseases(perturbed_pathways)
        }
    
    def _calculate_perturbation_score(
        self,
        added: int,
        removed: int,
        modified: int,
        common: int
    ) -> float:
        """Calculate overall perturbation score (0-100)"""
        total_edges = added + removed + common
        
        if total_edges == 0:
            return 0.0
        
        # Weight different types of changes
        change_score = (
            added * 1.0 +      # New edges are significant
            removed * 1.0 +    # Removed edges are significant
            modified * 0.5     # Modified edges are less significant
        )
        
        # Normalize to 0-100 scale
        max_possible_score = total_edges * 1.0
        score = (change_score / max_possible_score) * 100 if max_possible_score > 0 else 0
        
        return min(100.0, score)
    
    def _identify_perturbed_pathways(
        self,
        changed_edges: List[tuple],
        weight_changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Identify perturbed pathways based on edge changes
        
        Note: This is a simplified implementation.
        In production, would integrate with pathway databases (KEGG, Reactome, etc.)
        """
        # Group edges by source/target genes
        affected_genes = set()
        for edge in changed_edges:
            affected_genes.add(edge[0])
            affected_genes.add(edge[1])
        
        for change in weight_changes:
            affected_genes.add(change["source"])
            affected_genes.add(change["target"])
        
        # Placeholder pathway identification
        # In production, would query pathway databases
        pathways = []
        
        # Example: If many cancer-related genes are affected
        cancer_genes = {"TP53", "BRCA1", "BRCA2", "MYC", "EGFR"}
        if affected_genes & cancer_genes:
            pathways.append({
                "pathway_name": "Cancer Signaling",
                "pathway_id": "KEGG:05200",
                "affected_genes": list(affected_genes & cancer_genes),
                "perturbation_type": "activation" if len(affected_genes & cancer_genes) > 2 else "modification"
            })
        
        return pathways
    
    def _map_to_diseases(self, pathways: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Map perturbed pathways to associated diseases
        
        Note: This is a simplified implementation.
        In production, would integrate with disease databases (DisGeNET, etc.)
        """
        diseases = []
        
        for pathway in pathways:
            if "Cancer" in pathway.get("pathway_name", ""):
                diseases.append({
                    "disease_name": "Cancer",
                    "disease_id": "MONDO:0004992",
                    "association_strength": "moderate",
                    "evidence": "pathway_perturbation"
                })
        
        return diseases

