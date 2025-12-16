"""
Disease classification from expression data
Integrates with existing ML Service
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
import logging
import os
import sys

logger = logging.getLogger(__name__)

# Import ML Service client for GRN inference
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


class DiseaseClassifier:
    """Classify diseases from expression data"""
    
    def __init__(self):
        """Initialize classifier with pre-trained models"""
        # In production, would load pre-trained models
        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
    
    def classify_disease(
        self,
        expression_data: pd.DataFrame,
        disease_types: List[str],
        use_grn: bool = False
    ) -> Dict[str, Any]:
        """
        Classify disease from expression data
        
        Args:
            expression_data: Patient expression data (genes as columns)
            disease_types: List of disease types to classify
            use_grn: Whether to use GRN-based features (integrates with ML Service)
            
        Returns:
            Dictionary with classification results
        """
        predictions = []
        
        for disease in disease_types:
            # Get or train model for disease
            model = self._get_model(disease)
            
            if model is None:
                # Use simple signature-based classification
                prediction = self._classify_by_signature(expression_data, disease)
            else:
                # Use trained classifier
                X = expression_data.values
                X_scaled = self.scaler.fit_transform(X)
                
                probabilities = model.predict_proba(X_scaled)[0]
                predicted_class = model.predict(X_scaled)[0]
                confidence = float(np.max(probabilities))
                
                # Get top contributing genes
                if hasattr(model, 'feature_importances_'):
                    feature_importance = model.feature_importances_
                    gene_importance = list(zip(expression_data.columns, feature_importance))
                    top_genes = sorted(gene_importance, key=lambda x: x[1], reverse=True)[:10]
                    top_gene_names = [g[0] for g in top_genes]
                else:
                    top_gene_names = []
                
                prediction = {
                    "disease": disease,
                    "probability": float(confidence),
                    "predicted_class": str(predicted_class),
                    "confidence": float(confidence),
                    "top_genes": top_gene_names
                }
            
            predictions.append(prediction)
        
        return {
            "predictions": predictions,
            "method": "classifier" if any(self._get_model(d) for d in disease_types) else "signature"
        }
    
    def _get_model(self, disease: str) -> Optional[Any]:
        """Get pre-trained model for disease"""
        # Placeholder - would load from model storage
        if disease in self.models:
            return self.models[disease]
        
        # For now, return None (use signature-based)
        return None
    
    def _classify_by_signature(
        self,
        expression_data: pd.DataFrame,
        disease: str
    ) -> Dict[str, Any]:
        """Classify using disease signatures (fallback method)"""
        # Simple signature-based classification
        # In practice, would use established disease signatures
        
        # Example: Check if key disease genes are expressed
        disease_genes = {
            "breast_cancer": ["ESR1", "ERBB2", "PGR"],
            "lung_cancer": ["EGFR", "KRAS", "TP53"],
            "colorectal_cancer": ["APC", "KRAS", "TP53"]
        }
        
        genes_to_check = disease_genes.get(disease.lower().replace(" ", "_"), [])
        available_genes = [g for g in genes_to_check if g in expression_data.columns]
        
        if available_genes:
            mean_expr = expression_data[available_genes].mean(axis=0).mean()
            # Simple threshold-based classification
            probability = min(mean_expr / 10.0, 1.0) if mean_expr > 0 else 0.0
        else:
            probability = 0.5  # Unknown
        
        return {
            "disease": disease,
            "probability": float(probability),
            "confidence": float(probability * 0.8),  # Lower confidence for signature-based
            "top_genes": available_genes[:5],
            "method": "signature"
        }
    
    def train_model(
        self,
        expression_data: pd.DataFrame,
        labels: pd.Series,
        disease: str
    ) -> Dict[str, Any]:
        """
        Train a classifier model for a disease
        
        Args:
            expression_data: Training expression data
            labels: Class labels
            disease: Disease name
            
        Returns:
            Training results
        """
        X = expression_data.values
        y = labels.values
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_scaled, y)
        
        # Cross-validation score
        cv_scores = cross_val_score(model, X_scaled, y, cv=5)
        
        # Store model
        self.models[disease] = model
        
        return {
            "disease": disease,
            "accuracy": float(np.mean(cv_scores)),
            "std": float(np.std(cv_scores)),
            "feature_count": X.shape[1],
            "sample_count": X.shape[0]
        }

