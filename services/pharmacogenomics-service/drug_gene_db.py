"""
Drug-gene interaction database
Integrates with PharmGKB, CPIC guidelines
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DrugGeneDatabase:
    """Drug-gene interaction database"""
    
    def __init__(self):
        """Initialize drug-gene database"""
        # In production, would load from external database or API
        # For now, use curated examples
        self.interactions = {
            # Warfarin - CYP2C9, VKORC1
            ("warfarin", "CYP2C9"): {
                "gene": "CYP2C9",
                "phenotype": "poor_metabolizer",
                "clinical_significance": "actionable",
                "dosing_recommendation": "Reduce dose by 30-50%",
                "evidence_level": "A",
                "guideline_reference": "CPIC 2017"
            },
            ("warfarin", "VKORC1"): {
                "gene": "VKORC1",
                "phenotype": "reduced_function",
                "clinical_significance": "actionable",
                "dosing_recommendation": "Reduce dose by 20-30%",
                "evidence_level": "A",
                "guideline_reference": "CPIC 2017"
            },
            # Clopidogrel - CYP2C19
            ("clopidogrel", "CYP2C19"): {
                "gene": "CYP2C19",
                "phenotype": "poor_metabolizer",
                "clinical_significance": "actionable",
                "dosing_recommendation": "Consider alternative antiplatelet therapy",
                "alternative_drugs": ["prasugrel", "ticagrelor"],
                "evidence_level": "A",
                "guideline_reference": "CPIC 2013"
            },
            # Codeine - CYP2D6
            ("codeine", "CYP2D6"): {
                "gene": "CYP2D6",
                "phenotype": "ultra_rapid_metabolizer",
                "clinical_significance": "actionable",
                "dosing_recommendation": "Avoid codeine, use alternative",
                "alternative_drugs": ["tramadol", "morphine"],
                "evidence_level": "A",
                "guideline_reference": "CPIC 2014"
            },
            # Tamoxifen - CYP2D6
            ("tamoxifen", "CYP2D6"): {
                "gene": "CYP2D6",
                "phenotype": "poor_metabolizer",
                "clinical_significance": "actionable",
                "dosing_recommendation": "Consider alternative therapy",
                "alternative_drugs": ["raloxifene", "aromatase_inhibitors"],
                "evidence_level": "B",
                "guideline_reference": "CPIC 2018"
            }
        }
    
    def get_interactions(self, drug_name: str) -> List[Dict[str, Any]]:
        """
        Get drug-gene interactions for a drug
        
        Args:
            drug_name: Drug name (case-insensitive)
            
        Returns:
            List of interaction dictionaries
        """
        drug_lower = drug_name.lower()
        interactions = []
        
        for (drug, gene), interaction in self.interactions.items():
            if drug == drug_lower:
                interactions.append({
                    "drug_name": drug_name,
                    **interaction
                })
        
        return interactions
    
    def get_interaction(self, drug_name: str, gene: str) -> Optional[Dict[str, Any]]:
        """
        Get specific drug-gene interaction
        
        Args:
            drug_name: Drug name
            gene: Gene name
            
        Returns:
            Interaction dictionary or None
        """
        drug_lower = drug_name.lower()
        gene_upper = gene.upper()
        
        key = (drug_lower, gene_upper)
        if key in self.interactions:
            return {
                "drug_name": drug_name,
                "gene": gene_upper,
                **self.interactions[key]
            }
        
        return None
    
    def get_phenotype_from_genotype(
        self,
        gene: str,
        genotype: str
    ) -> Optional[str]:
        """
        Determine phenotype from genotype
        
        Args:
            gene: Gene name
            genotype: Genotype (e.g., "*1/*1", "*1/*2")
            
        Returns:
            Phenotype (poor_metabolizer, intermediate, extensive, ultra_rapid)
        """
        # Simplified phenotype prediction
        # In production, would use PharmGKB or CPIC algorithms
        
        gene_upper = gene.upper()
        
        # CYP2D6 examples
        if gene_upper == "CYP2D6":
            if "*4" in genotype or "*5" in genotype:
                return "poor_metabolizer"
            elif "*1" in genotype and "*2" in genotype:
                return "extensive_metabolizer"
            elif "*1/*1" in genotype:
                return "extensive_metabolizer"
            elif "*2/*2" in genotype:
                return "ultra_rapid_metabolizer"
        
        # CYP2C9 examples
        if gene_upper == "CYP2C9":
            if "*2" in genotype or "*3" in genotype:
                return "intermediate_metabolizer"
            elif "*3/*3" in genotype:
                return "poor_metabolizer"
            elif "*1/*1" in genotype:
                return "extensive_metabolizer"
        
        # Default
        return "extensive_metabolizer"

