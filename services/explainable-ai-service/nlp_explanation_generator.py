"""
Natural Language Explanation Generator
Convert technical explanations to human-readable text
"""

from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NLPExplanationGenerator:
    """Generate natural language explanations from technical explanations"""
    
    def generate_explanation(
        self,
        feature_importance: List[Dict[str, Any]],
        prediction_value: float,
        prediction_type: str = "risk_score"
    ) -> str:
        """
        Generate natural language explanation
        
        Args:
            feature_importance: List of feature importance dictionaries
            prediction_value: Model prediction value
            prediction_type: Type of prediction ("risk_score", "probability", "score")
            
        Returns:
            Natural language explanation string
        """
        logger.info("Generating natural language explanation")
        
        # Get top features
        top_features = feature_importance[:5]
        
        # Build explanation
        explanation_parts = []
        
        # Prediction summary
        if prediction_type == "risk_score":
            if prediction_value > 75:
                explanation_parts.append(f"The patient has a high risk score of {prediction_value:.1f}%.")
            elif prediction_value > 50:
                explanation_parts.append(f"The patient has a moderate risk score of {prediction_value:.1f}%.")
            else:
                explanation_parts.append(f"The patient has a low risk score of {prediction_value:.1f}%.")
        else:
            explanation_parts.append(f"The model prediction is {prediction_value:.3f}.")
        
        # Top contributing factors
        if top_features:
            explanation_parts.append("The main contributing factors are:")
            for i, feature_info in enumerate(top_features, 1):
                feature_name = feature_info.get("feature", "Unknown")
                importance = feature_info.get("importance", 0)
                
                # Format feature name (replace underscores, capitalize)
                formatted_name = feature_name.replace("_", " ").title()
                
                explanation_parts.append(
                    f"{i}. {formatted_name} (contribution: {importance:.3f})"
                )
        
        # Clinical interpretation
        explanation_parts.append(self._generate_clinical_interpretation(
            top_features, prediction_value, prediction_type
        ))
        
        return " ".join(explanation_parts)
    
    def _generate_clinical_interpretation(
        self,
        top_features: List[Dict[str, Any]],
        prediction_value: float,
        prediction_type: str
    ) -> str:
        """Generate clinical interpretation"""
        interpretation = "Clinical interpretation: "
        
        if prediction_type == "risk_score":
            if prediction_value > 75:
                interpretation += "This patient may benefit from enhanced monitoring and preventive interventions."
            elif prediction_value > 50:
                interpretation += "Regular monitoring and lifestyle modifications are recommended."
            else:
                interpretation += "Current risk level is manageable with standard care."
        else:
            interpretation += "Please consult with healthcare provider for detailed interpretation."
        
        return interpretation

