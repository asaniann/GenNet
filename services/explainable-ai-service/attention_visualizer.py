"""
Attention Visualization for Neural Networks
"""

import numpy as np
from typing import Dict, List, Any, Optional
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
import io

logger = logging.getLogger(__name__)


class AttentionVisualizer:
    """Visualize attention weights for transformer/attention-based models"""
    
    def visualize_attention(
        self,
        attention_weights: np.ndarray,
        feature_names: List[str],
        layer: int = 0,
        head: int = 0
    ) -> Dict[str, Any]:
        """
        Visualize attention weights
        
        Args:
            attention_weights: Attention weight matrix (n_features x n_features)
            feature_names: List of feature names
            layer: Layer index (for multi-layer models)
            head: Head index (for multi-head attention)
            
        Returns:
            Dictionary with attention visualization
        """
        logger.info(f"Visualizing attention for layer {layer}, head {head}")
        
        try:
            # Generate attention heatmap
            heatmap = self._generate_attention_heatmap(attention_weights, feature_names)
            
            # Extract top attended features
            top_features = self._extract_top_attended_features(attention_weights, feature_names)
            
            return {
                "attention_weights": attention_weights.tolist(),
                "heatmap": heatmap,
                "top_features": top_features,
                "layer": layer,
                "head": head
            }
        except Exception as e:
            logger.error(f"Error visualizing attention: {e}")
            raise ValueError(f"Attention visualization failed: {str(e)}")
    
    def _generate_attention_heatmap(
        self,
        attention_weights: np.ndarray,
        feature_names: List[str]
    ) -> str:
        """Generate attention heatmap as base64 image"""
        try:
            plt.figure(figsize=(12, 10))
            plt.imshow(attention_weights, cmap='viridis', aspect='auto')
            plt.colorbar(label='Attention Weight')
            plt.xlabel('Target Features')
            plt.ylabel('Source Features')
            plt.title('Attention Weight Heatmap')
            plt.xticks(range(len(feature_names)), feature_names, rotation=45, ha='right')
            plt.yticks(range(len(feature_names)), feature_names)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            logger.error(f"Error generating attention heatmap: {e}")
            return None
    
    def _extract_top_attended_features(
        self,
        attention_weights: np.ndarray,
        feature_names: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Extract top attended features"""
        # Average attention weights across all targets
        avg_attention = attention_weights.mean(axis=1)
        
        # Get top k features
        top_indices = np.argsort(avg_attention)[-top_k:][::-1]
        
        top_features = [
            {
                "feature": feature_names[i],
                "attention_score": float(avg_attention[i]),
                "rank": rank + 1
            }
            for rank, i in enumerate(top_indices)
        ]
        
        return top_features

