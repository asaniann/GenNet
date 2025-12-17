"""
Tests for ML Service Features
"""

import pytest
from anomaly_detector import AnomalyDetector
from disease_predictor import DiseasePredictor
from parameter_predictor import predict_parameters


class TestAnomalyDetector:
    """Test anomaly detection"""
    
    def test_detect_anomalies_statistical(self):
        detector = AnomalyDetector()
        expression_data = {
            "gene1": [1.0, 1.1, 1.2, 10.0],  # Last value is anomaly
            "gene2": [0.5, 0.6, 0.7, 0.8]
        }
        result = detector.detect_anomalies(
            network_id="test_network",
            expression_data=expression_data
        )
        assert "anomalies" in result
        assert result["count"] > 0
    
    def test_detect_anomalies_threshold(self):
        detector = AnomalyDetector()
        expression_data = {
            "gene1": [0.95],  # High value
            "gene2": [0.05]   # Low value
        }
        result = detector.detect_anomalies(
            network_id="test_network",
            expression_data=expression_data
        )
        assert "anomalies" in result


class TestDiseasePredictor:
    """Test disease prediction"""
    
    def test_predict_disease(self):
        predictor = DiseasePredictor()
        expression_data = {
            "nodes": [
                {"id": "BRCA1", "expression": 0.8},
                {"id": "BRCA2", "expression": 0.9},
                {"id": "TP53", "expression": 0.7}
            ]
        }
        result = predictor.predict_disease(
            network_id="test_network",
            expression_data=expression_data
        )
        assert "predictions" in result
        assert result["count"] > 0


class TestParameterPredictor:
    """Test parameter prediction"""
    
    def test_predict_parameters(self):
        network_graph = {
            "nodes": [{"id": "gene1"}, {"id": "gene2"}],
            "edges": [{"source": "gene1", "target": "gene2"}]
        }
        expression_data = {
            "gene1": 0.7,
            "gene2": 0.5
        }
        result = predict_parameters(
            network_graph=network_graph,
            expression_data=expression_data
        )
        assert "parameters" in result
        assert result["count"] > 0

