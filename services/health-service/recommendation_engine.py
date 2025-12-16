"""
Recommendation engine for personalized health recommendations
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Generate personalized health recommendations"""
    
    def generate_recommendations(
        self,
        predictions: Dict[str, Any],
        patient_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate health recommendations based on predictions
        
        Args:
            predictions: Dictionary with predictions from various methods
            patient_data: Patient demographic and clinical data
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        
        # Risk-based recommendations
        risk_recommendations = self._generate_risk_recommendations(predictions)
        recommendations.extend(risk_recommendations)
        
        # Screening recommendations
        screening_recommendations = self._generate_screening_recommendations(predictions, patient_data)
        recommendations.extend(screening_recommendations)
        
        # Lifestyle recommendations
        lifestyle_recommendations = self._generate_lifestyle_recommendations(predictions)
        recommendations.extend(lifestyle_recommendations)
        
        # Monitoring recommendations
        monitoring_recommendations = self._generate_monitoring_recommendations(predictions)
        recommendations.extend(monitoring_recommendations)
        
        return recommendations
    
    def _generate_risk_recommendations(self, predictions: Dict) -> List[Dict]:
        """Generate recommendations based on risk scores"""
        recommendations = []
        
        ensemble_prediction = predictions.get("ensemble_prediction", {})
        risk_score = ensemble_prediction.get("risk_score", 0.0)
        
        if risk_score > 75:
            recommendations.append({
                "type": "screening",
                "title": "High Risk - Immediate Screening Recommended",
                "description": f"Your risk score of {risk_score:.1f} indicates high risk. Immediate screening is recommended.",
                "priority": "high",
                "evidence_level": "strong",
                "action_items": [
                    "Schedule appointment with healthcare provider",
                    "Consider genetic counseling",
                    "Discuss screening options"
                ]
            })
        elif risk_score > 50:
            recommendations.append({
                "type": "screening",
                "title": "Moderate Risk - Regular Screening",
                "description": f"Your risk score of {risk_score:.1f} indicates moderate risk. Regular screening is recommended.",
                "priority": "medium",
                "evidence_level": "moderate"
            })
        
        return recommendations
    
    def _generate_screening_recommendations(
        self,
        predictions: Dict,
        patient_data: Dict
    ) -> List[Dict]:
        """Generate screening recommendations"""
        recommendations = []
        
        # Age-based screening
        age_range = patient_data.get("age_range", "")
        if "50" in age_range or "60" in age_range:
            recommendations.append({
                "type": "screening",
                "title": "Age-Appropriate Screening",
                "description": "Based on your age, regular screening is recommended.",
                "priority": "medium"
            })
        
        return recommendations
    
    def _generate_lifestyle_recommendations(self, predictions: Dict) -> List[Dict]:
        """Generate lifestyle recommendations"""
        return [
            {
                "type": "lifestyle",
                "title": "Maintain Healthy Lifestyle",
                "description": "Regular exercise, balanced diet, and stress management can help reduce risk.",
                "priority": "medium",
                "evidence_level": "strong"
            }
        ]
    
    def _generate_monitoring_recommendations(self, predictions: Dict) -> List[Dict]:
        """Generate monitoring recommendations"""
        return [
            {
                "type": "monitoring",
                "title": "Regular Health Monitoring",
                "description": "Regular monitoring of your health metrics is recommended.",
                "priority": "low"
            }
        ]

