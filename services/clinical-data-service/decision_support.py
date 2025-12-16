"""
Clinical decision support engine
Guideline-based recommendations
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ClinicalDecisionSupport:
    """Clinical decision support based on guidelines"""
    
    def generate_recommendations(
        self,
        clinical_profile: Dict[str, Any],
        lab_results: List[Dict[str, Any]],
        genomic_risk: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate clinical recommendations
        
        Args:
            clinical_profile: Patient clinical profile
            lab_results: List of lab results
            genomic_risk: Optional genomic risk score
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Age-based screening
        age = clinical_profile.get("age")
        if age:
            age_recs = self._age_based_screening(age)
            recommendations.extend(age_recs)
        
        # Lab-based recommendations
        lab_recs = self._lab_based_recommendations(lab_results)
        recommendations.extend(lab_recs)
        
        # Genomic risk-based recommendations
        if genomic_risk:
            genomic_recs = self._genomic_risk_recommendations(genomic_risk)
            recommendations.extend(genomic_recs)
        
        # Medication-based recommendations
        medications = clinical_profile.get("medications", [])
        if medications:
            med_recs = self._medication_recommendations(medications)
            recommendations.extend(med_recs)
        
        return recommendations
    
    def _age_based_screening(self, age: int) -> List[Dict[str, Any]]:
        """Generate age-based screening recommendations"""
        recommendations = []
        
        if age >= 50:
            recommendations.append({
                "type": "screening",
                "title": "Colorectal Cancer Screening",
                "description": "Regular colorectal cancer screening recommended for age 50+",
                "priority": "high",
                "evidence_level": "A",
                "guideline_reference": "USPSTF 2021",
                "action_items": [
                    "Schedule colonoscopy or stool-based test",
                    "Discuss screening options with healthcare provider"
                ]
            })
        
        if age >= 40:
            recommendations.append({
                "type": "screening",
                "title": "Breast Cancer Screening",
                "description": "Regular mammography screening recommended for age 40+",
                "priority": "medium",
                "evidence_level": "B",
                "guideline_reference": "USPSTF 2016"
            })
        
        return recommendations
    
    def _lab_based_recommendations(self, lab_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on lab results"""
        recommendations = []
        
        for lab in lab_results:
            test_name = lab.get("test_name", "").lower()
            interpretation = lab.get("interpretation", "").lower()
            value = lab.get("value")
            
            # Cholesterol recommendations
            if "cholesterol" in test_name or "ldl" in test_name:
                if interpretation == "high" or (value and value > 190):
                    recommendations.append({
                        "type": "treatment",
                        "title": "High Cholesterol Management",
                        "description": "Elevated cholesterol levels detected. Lifestyle modifications and medication may be recommended.",
                        "priority": "high",
                        "evidence_level": "A",
                        "action_items": [
                            "Discuss statin therapy with healthcare provider",
                            "Implement dietary changes",
                            "Increase physical activity"
                        ]
                    })
            
            # Blood glucose recommendations
            if "glucose" in test_name or "a1c" in test_name:
                if interpretation == "high" or (value and value > 126):
                    recommendations.append({
                        "type": "treatment",
                        "title": "Diabetes Screening/Management",
                        "description": "Elevated blood glucose detected. Further evaluation for diabetes recommended.",
                        "priority": "high",
                        "evidence_level": "A"
                    })
        
        return recommendations
    
    def _genomic_risk_recommendations(self, genomic_risk: float) -> List[Dict[str, Any]]:
        """Generate recommendations based on genomic risk"""
        recommendations = []
        
        if genomic_risk > 75:
            recommendations.append({
                "type": "screening",
                "title": "High Genomic Risk - Enhanced Screening",
                "description": f"Genomic risk score of {genomic_risk:.1f} indicates high risk. Enhanced screening and monitoring recommended.",
                "priority": "high",
                "evidence_level": "B",
                "action_items": [
                    "Consider genetic counseling",
                    "Discuss enhanced screening protocols",
                    "Review family history"
                ]
            })
        elif genomic_risk > 50:
            recommendations.append({
                "type": "monitoring",
                "title": "Moderate Genomic Risk - Regular Monitoring",
                "description": f"Genomic risk score of {genomic_risk:.1f} indicates moderate risk. Regular monitoring recommended.",
                "priority": "medium",
                "evidence_level": "C"
            })
        
        return recommendations
    
    def _medication_recommendations(self, medications: List[str]) -> List[Dict[str, Any]]:
        """Generate recommendations based on medications"""
        recommendations = []
        
        # Check for drug interactions (simplified)
        if len(medications) >= 5:
            recommendations.append({
                "type": "monitoring",
                "title": "Polypharmacy Review",
                "description": "Multiple medications detected. Review for potential interactions and optimization.",
                "priority": "medium",
                "evidence_level": "B"
            })
        
        return recommendations

