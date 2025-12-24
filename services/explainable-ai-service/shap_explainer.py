"""
SHAP (SHapley Additive exPlanations) Integration
"""

import shap
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import base64
import io

logger = logging.getLogger(__name__)


class SHAPExplainer:
    """SHAP explanation generator"""
    
    def explain_prediction(
        self,
        model: Any,
        patient_data: pd.DataFrame,
        prediction: float,
        model_type: str = "ensemble"
    ) -> Dict[str, Any]:
        """
        Generate SHAP values for prediction explanation
        
        Args:
            model: Trained model (or model wrapper)
            patient_data: Patient feature data as DataFrame
            prediction: Model prediction value
            model_type: Type of model ("tree", "neural", "linear", "ensemble")
            
        Returns:
            Dictionary with SHAP values and visualizations
        """
        logger.info(f"Generating SHAP explanation for model type: {model_type}")
        
        try:
            # Select appropriate SHAP explainer based on model type
            if model_type in ["tree", "ensemble"]:
                explainer = shap.TreeExplainer(model)
            elif model_type == "neural":
                explainer = shap.DeepExplainer(model, patient_data)
            elif model_type == "linear":
                explainer = shap.LinearExplainer(model, patient_data)
            else:
                # Use KernelExplainer as fallback (works for any model)
                explainer = shap.KernelExplainer(model.predict, patient_data)
            
            # Calculate SHAP values
            shap_values = explainer.shap_values(patient_data)
            
            # Handle multi-output models
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # Use first output
            
            # Convert to DataFrame for easier handling
            if isinstance(shap_values, np.ndarray):
                shap_df = pd.DataFrame(
                    shap_values,
                    columns=patient_data.columns,
                    index=patient_data.index
                )
            else:
                shap_df = pd.DataFrame(shap_values)
            
            # Rank features by importance
            feature_importance = self._rank_features(shap_df)
            
            # Generate visualizations
            summary_plot = self._generate_summary_plot(shap_values, patient_data)
            waterfall_plot = self._generate_waterfall_plot(shap_values, patient_data)
            
            return {
                "shap_values": shap_df.to_dict(orient="records"),
                "feature_importance": feature_importance,
                "top_features": [f["feature"] for f in feature_importance[:10]],
                "summary_plot": summary_plot,
                "waterfall_plot": waterfall_plot,
                "base_value": explainer.expected_value if hasattr(explainer, 'expected_value') else None
            }
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {e}")
            raise ValueError(f"SHAP explanation failed: {str(e)}")
    
    def _rank_features(self, shap_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Rank features by absolute SHAP value"""
        feature_importance = []
        
        for col in shap_df.columns:
            importance = float(shap_df[col].abs().mean())
            feature_importance.append({
                "feature": col,
                "importance": importance,
                "mean_shap": float(shap_df[col].mean())
            })
        
        # Sort by importance (descending)
        feature_importance.sort(key=lambda x: x["importance"], reverse=True)
        
        return feature_importance
    
    def _generate_summary_plot(
        self,
        shap_values: np.ndarray,
        patient_data: pd.DataFrame
    ) -> str:
        """Generate SHAP summary plot as base64 image"""
        try:
            plt.figure(figsize=(10, 8))
            shap.summary_plot(shap_values, patient_data, show=False)
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error generating summary plot: {e}")
            return None
    
    def _generate_waterfall_plot(
        self,
        shap_values: np.ndarray,
        patient_data: pd.DataFrame
    ) -> str:
        """Generate SHAP waterfall plot as base64 image"""
        try:
            # For single prediction, create waterfall plot
            if len(shap_values.shape) == 1 or shap_values.shape[0] == 1:
                plt.figure(figsize=(10, 6))
                
                # Use SHAP's waterfall plot if available
                if hasattr(shap, 'waterfall_plot'):
                    shap.waterfall_plot(
                        shap.Explanation(
                            values=shap_values.flatten() if len(shap_values.shape) > 1 else shap_values,
                            base_values=0,
                            data=patient_data.iloc[0].values if len(patient_data) > 0 else patient_data.values.flatten(),
                            feature_names=patient_data.columns.tolist()
                        ),
                        show=False
                    )
                else:
                    # Fallback: bar plot
                    values = shap_values.flatten() if len(shap_values.shape) > 1 else shap_values
                    plt.barh(range(len(values)), values)
                    plt.yticks(range(len(values)), patient_data.columns)
                    plt.xlabel("SHAP Value")
                    plt.title("SHAP Waterfall Plot")
                
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
                buffer.seek(0)
                image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                plt.close()
                
                return f"data:image/png;base64,{image_base64}"
            else:
                return None
        except Exception as e:
            logger.error(f"Error generating waterfall plot: {e}")
            return None

