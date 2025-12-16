"""
Drug response prediction
Based on pharmacogenomics data
"""

from typing import Dict, List, Any, Optional
import logging
import os
import sys

logger = logging.getLogger(__name__)

# Import genomic analysis service client
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from shared.http_client import ServiceClient


class DrugResponsePredictor:
    """Predict drug response based on pharmacogenomics"""
    
    def __init__(self):
        """Initialize response predictor"""
        from drug_gene_db import DrugGeneDatabase
        self.drug_gene_db = DrugGeneDatabase()
        
        # Service clients
        genomic_service_url = os.getenv("GENOMIC_ANALYSIS_SERVICE_URL", "http://genomic-analysis-service:8000")
        self.genomic_client = ServiceClient(base_url=genomic_service_url, timeout=30.0)
    
    async def predict_response(
        self,
        patient_id: str,
        drug_name: str,
        genomic_profile_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict drug response for a patient
        
        Args:
            patient_id: Patient ID
            drug_name: Drug name
            genomic_profile_id: Optional genomic profile ID
            token: Optional auth token
            
        Returns:
            Prediction dictionary
        """
        # Get drug-gene interactions
        interactions = self.drug_gene_db.get_interactions(drug_name)
        
        if not interactions:
            # No known interactions, return default prediction
            return {
                "drug_name": drug_name,
                "response_probability": 0.7,  # Default moderate response
                "efficacy_score": 70.0,
                "toxicity_risk": 20.0,
                "recommended_dose": None,
                "dose_adjustment": "normal",
                "confidence": 0.5,
                "contributing_genes": [],
                "note": "No known pharmacogenomic interactions"
            }
        
        # Get patient genomic data
        contributing_genes = []
        contributing_variants = []
        dose_adjustments = []
        monitoring_required = False
        
        # For each interaction, check patient genotype
        for interaction in interactions:
            gene = interaction["gene"]
            
            # Get patient variants for this gene
            # In production, would query genomic profile
            # For now, use placeholder
            patient_genotype = self._get_patient_genotype(patient_id, gene, genomic_profile_id, token)
            
            if patient_genotype:
                phenotype = self.drug_gene_db.get_phenotype_from_genotype(gene, patient_genotype)
                
                contributing_genes.append({
                    "gene": gene,
                    "genotype": patient_genotype,
                    "phenotype": phenotype
                })
                
                # Determine impact
                if interaction["phenotype"] == phenotype:
                    # Patient has relevant phenotype
                    if interaction["clinical_significance"] == "actionable":
                        dose_adjustments.append(interaction.get("dosing_recommendation", ""))
                        monitoring_required = True
                
                contributing_variants.append({
                    "gene": gene,
                    "variant": interaction.get("variant"),
                    "phenotype": phenotype
                })
        
        # Calculate response probability
        response_probability = self._calculate_response_probability(
            interactions,
            contributing_genes,
            dose_adjustments
        )
        
        # Calculate efficacy and toxicity
        efficacy_score = self._calculate_efficacy(interactions, contributing_genes)
        toxicity_risk = self._calculate_toxicity(interactions, contributing_genes)
        
        # Determine dose adjustment
        dose_adjustment = self._determine_dose_adjustment(dose_adjustments)
        recommended_dose = self._calculate_recommended_dose(drug_name, dose_adjustment)
        
        # Calculate confidence
        confidence = self._calculate_confidence(interactions, contributing_genes)
        
        return {
            "drug_name": drug_name,
            "response_probability": response_probability,
            "efficacy_score": efficacy_score,
            "toxicity_risk": toxicity_risk,
            "recommended_dose": recommended_dose,
            "dose_adjustment": dose_adjustment,
            "monitoring_required": monitoring_required,
            "confidence": confidence,
            "contributing_genes": contributing_genes,
            "contributing_variants": contributing_variants,
            "interactions": interactions
        }
    
    def _get_patient_genotype(
        self,
        patient_id: str,
        gene: str,
        genomic_profile_id: Optional[str],
        token: Optional[str]
    ) -> Optional[str]:
        """Get patient genotype for a gene"""
        # Placeholder - would query genomic profile
        # For now, return None (would use genomic analysis service)
        return None
    
    def _calculate_response_probability(
        self,
        interactions: List[Dict],
        contributing_genes: List[Dict],
        dose_adjustments: List[str]
    ) -> float:
        """Calculate response probability"""
        base_probability = 0.7
        
        # Adjust based on interactions
        if dose_adjustments:
            # If dose adjustments needed, response may be affected
            base_probability -= 0.1
        
        # Adjust based on phenotype
        for gene_info in contributing_genes:
            phenotype = gene_info.get("phenotype", "")
            if "poor" in phenotype:
                base_probability -= 0.15
            elif "ultra_rapid" in phenotype:
                base_probability += 0.1
        
        return max(0.0, min(1.0, base_probability))
    
    def _calculate_efficacy(
        self,
        interactions: List[Dict],
        contributing_genes: List[Dict]
    ) -> float:
        """Calculate efficacy score (0-100)"""
        base_efficacy = 75.0
        
        for gene_info in contributing_genes:
            phenotype = gene_info.get("phenotype", "")
            if "poor" in phenotype:
                base_efficacy -= 20.0
            elif "intermediate" in phenotype:
                base_efficacy -= 10.0
        
        return max(0.0, min(100.0, base_efficacy))
    
    def _calculate_toxicity(
        self,
        interactions: List[Dict],
        contributing_genes: List[Dict]
    ) -> float:
        """Calculate toxicity risk (0-100)"""
        base_toxicity = 20.0
        
        for gene_info in contributing_genes:
            phenotype = gene_info.get("phenotype", "")
            if "ultra_rapid" in phenotype:
                base_toxicity += 30.0
            elif "poor" in phenotype:
                base_toxicity += 15.0
        
        return max(0.0, min(100.0, base_toxicity))
    
    def _determine_dose_adjustment(self, dose_adjustments: List[str]) -> str:
        """Determine overall dose adjustment"""
        if not dose_adjustments:
            return "normal"
        
        # If any adjustment recommends avoiding or significant reduction
        for adj in dose_adjustments:
            if "avoid" in adj.lower() or "alternative" in adj.lower():
                return "avoid"
            if "reduce" in adj.lower():
                return "decrease"
            if "increase" in adj.lower():
                return "increase"
        
        return "decrease"  # Default to decrease if adjustments present
    
    def _calculate_recommended_dose(
        self,
        drug_name: str,
        dose_adjustment: str
    ) -> Optional[float]:
        """Calculate recommended dose"""
        # Placeholder - would use drug-specific dosing guidelines
        # For now, return None (would calculate based on standard dosing)
        return None
    
    def _calculate_confidence(
        self,
        interactions: List[Dict],
        contributing_genes: List[Dict]
    ) -> float:
        """Calculate prediction confidence (0-1)"""
        if not interactions:
            return 0.5  # Low confidence if no interactions
        
        if not contributing_genes:
            return 0.6  # Moderate confidence if interactions but no patient data
        
        # Higher confidence if we have patient genotype data
        evidence_levels = [i.get("evidence_level", "C") for i in interactions]
        if "A" in evidence_levels:
            return 0.9  # High confidence with level A evidence
        elif "B" in evidence_levels:
            return 0.8  # Good confidence with level B evidence
        else:
            return 0.7  # Moderate confidence

