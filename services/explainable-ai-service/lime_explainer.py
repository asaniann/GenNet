"""
LIME (Local Interpretable Model-agnostic Explanations) Integration
"""

import lime
import lime.lime_tabular
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io

logger = logging.getLogger(__name__)


class LIMEExplainer:
    """LIME explanation generator"""
    
    def explain_prediction(
        self,
        model: Any,
        patient_data: pd.DataFrame,
        training_data: pd.DataFrame,
        prediction: float,
        num_features: int = 10
    ) -> Dict[str, Any]:
        """
        Generate LIME explanation for local interpretability
        
        Args:
            model: Trained model with predict method
            patient_data: Patient feature data as DataFrame
            training_data: Training data for LIME explainer
            prediction: Model prediction value
            num_features: Number of top features to explain
            
        Returns:
            Dictionary with LIME explanation and visualization
        """
        logger.info(f"Generating LIME explanation with {num_features} features")
        
        try:
            # Create LIME explainer
            explainer = lime.lime_tabular.LimeTabularExplainer(
                training_data.values,
                feature_names=training_data.columns.tolist(),
                mode='regression' if isinstance(prediction, (int, float)) else 'classification',
                discretize_continuous=True
            )
            
            # Generate explanation
            explanation = explainer.explain_instance(
                patient_data.iloc[0].values if len(patient_data) > 0 else patient_data.values.flatten(),
                model.predict,
                num_features=num_features
            )
            
            # Extract feature weights
            feature_weights = explanation.as_list()
            
            # Convert to structured format
            feature_importance = [
                {
                    "feature": feature,
                    "weight": weight,
                    "importance": abs(weight)
                }
                for feature, weight in feature_weights
            ]
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            
            # Generate visualization
            visualization = self._generate_visualization(explanation, num_features)
            
            return {
                "explanation": explanation.as_list(),
                "feature_weights": feature_weights,
                "feature_importance": feature_importance,
                "top_features": [f["feature"] for f in feature_importance[:num_features]],
                "prediction": explanation.predicted_value,
                "local_prediction": explanation.local_pred,
                "visualization": visualization
            }
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {e}")
            raise ValueError(f"LIME explanation failed: {str(e)}")
    
    def _generate_visualization(
        self,
        explanation: Any,
        num_features: int
    ) -> str:
        """Generate LIME visualization as base64 image"""
        try:
            fig = explanation.as_pyplot_figure()
            
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error generating LIME visualization: {e}")
            return None

