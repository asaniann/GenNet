"""
Intelligent method selection based on data availability
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class MethodSelector:
    """Select optimal analysis methods based on data availability"""
    
    def select_methods(
        self,
        data_assessment: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Select analysis methods based on data availability
        
        Args:
            data_assessment: Data availability assessment
            preferences: User preferences
            
        Returns:
            Dictionary with selected methods and ensemble strategy
        """
        methods = []
        
        # Genomic methods
        if data_assessment.get("has_genomic_data"):
            methods.append("prs")
            methods.append("variant_annotation")
            methods.append("pharmacogenomics")
        
        # Expression methods
        if data_assessment.get("has_expression_data"):
            methods.append("expression_signatures")
            methods.append("biomarker_identification")
            
            # GRN construction if feasible
            grn_feasible, reason = self._check_grn_feasibility(data_assessment)
            if grn_feasible:
                methods.append("grn_construction")
                methods.append("network_perturbation")
        
        # Clinical methods
        if data_assessment.get("has_clinical_data"):
            methods.append("clinical_integration")
            methods.append("clinical_decision_support")
        
        # Multi-omics if multiple data types
        omics_count = sum([
            data_assessment.get("has_genomic_data", False),
            data_assessment.get("has_expression_data", False),
            data_assessment.get("has_clinical_data", False)
        ])
        
        if omics_count >= 2:
            methods.append("multi_omics_fusion")
            methods.append("integrated_analysis")
        
        # Determine ensemble strategy
        ensemble_strategy = self._determine_ensemble_strategy(methods, preferences)
        
        return {
            "methods": methods,
            "ensemble_strategy": ensemble_strategy,
            "grn_feasible": grn_feasible if data_assessment.get("has_expression_data") else False,
            "grn_feasibility_reason": reason if data_assessment.get("has_expression_data") else "No expression data"
        }
    
    def _check_grn_feasibility(self, assessment: Dict) -> tuple[bool, str]:
        """Check if GRN construction is feasible"""
        expr_quality = assessment.get("data_quality", {}).get("expression", 0.0)
        if expr_quality >= 0.8:
            return (True, "High quality expression data")
        elif expr_quality >= 0.6:
            return (True, "Moderate quality expression data")
        else:
            return (False, f"Expression data quality too low: {expr_quality}")
    
    def _determine_ensemble_strategy(
        self,
        methods: List[str],
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine optimal ensemble strategy"""
        if preferences and preferences.get("ensemble_strategy"):
            return preferences["ensemble_strategy"]
        
        # Default strategy based on number of methods
        if len(methods) >= 4:
            return "stacking"  # More methods, use stacking
        elif len(methods) >= 2:
            return "weighted_voting"  # Fewer methods, use weighted voting
        else:
            return "single_method"  # Only one method available

