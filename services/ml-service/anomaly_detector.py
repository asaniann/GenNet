"""
Anomaly Detection Module
Detects anomalies in network behavior using statistical and ML methods
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class AnomalyType(str, Enum):
    """Types of anomalies"""
    STATISTICAL = "statistical"
    PATTERN = "pattern"
    THRESHOLD = "threshold"
    CLUSTER = "cluster"


@dataclass
class Anomaly:
    """Anomaly detection result"""
    node_id: str
    anomaly_type: AnomalyType
    score: float
    severity: str
    description: str
    timestamp: Optional[float] = None


class AnomalyDetector:
    """Detect anomalies in network behavior"""
    
    def __init__(self):
        self.threshold_z_score = 3.0  # Standard deviations for anomaly
        self.threshold_percentile = 0.95  # Percentile threshold
    
    def detect_anomalies(
        self,
        network_id: str,
        expression_data: Dict[str, Any],
        baseline_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Detect anomalies in network expression data
        
        Args:
            network_id: Network identifier
            expression_data: Current expression data
            baseline_data: Optional baseline data for comparison
            
        Returns:
            Detected anomalies
        """
        try:
            anomalies = []
            
            # Extract expression values
            expression_values = self._extract_expression_values(expression_data)
            
            if not expression_values:
                return {
                    "network_id": network_id,
                    "anomalies": [],
                    "count": 0,
                    "detection_method": "statistical"
                }
            
            # Statistical anomaly detection
            statistical_anomalies = self._detect_statistical_anomalies(expression_values)
            anomalies.extend(statistical_anomalies)
            
            # Pattern-based detection
            pattern_anomalies = self._detect_pattern_anomalies(expression_values)
            anomalies.extend(pattern_anomalies)
            
            # Threshold-based detection
            threshold_anomalies = self._detect_threshold_anomalies(expression_values)
            anomalies.extend(threshold_anomalies)
            
            # Compare with baseline if available
            if baseline_data:
                baseline_anomalies = self._detect_baseline_anomalies(
                    expression_values,
                    baseline_data
                )
                anomalies.extend(baseline_anomalies)
            
            # Rank anomalies by score
            anomalies.sort(key=lambda x: x.score, reverse=True)
            
            return {
                "network_id": network_id,
                "anomalies": [self._anomaly_to_dict(a) for a in anomalies],
                "count": len(anomalies),
                "detection_method": "multi_method",
                "summary": self._generate_summary(anomalies)
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            raise
    
    def _extract_expression_values(self, expression_data: Dict[str, Any]) -> Dict[str, List[float]]:
        """Extract expression values from data structure"""
        values = {}
        
        if isinstance(expression_data, dict):
            # Try different data formats
            if "nodes" in expression_data:
                # Network structure with expression
                for node in expression_data["nodes"]:
                    if isinstance(node, dict):
                        node_id = node.get("id", node.get("label", ""))
                        expr_value = node.get("expression", node.get("value", 0.0))
                        if node_id:
                            values[node_id] = [expr_value] if isinstance(expr_value, (int, float)) else expr_value
            elif "expression" in expression_data:
                # Direct expression mapping
                values = expression_data["expression"]
            else:
                # Assume keys are node IDs
                for key, value in expression_data.items():
                    if isinstance(value, (int, float)):
                        values[key] = [value]
                    elif isinstance(value, list):
                        values[key] = value
        
        return values
    
    def _detect_statistical_anomalies(
        self,
        expression_values: Dict[str, List[float]]
    ) -> List[Anomaly]:
        """Detect anomalies using statistical methods (Z-score)"""
        anomalies = []
        
        # Collect all values for global statistics
        all_values = []
        for values in expression_values.values():
            all_values.extend(values if isinstance(values, list) else [values])
        
        if len(all_values) < 3:
            return anomalies  # Need at least 3 values for statistics
        
        mean = statistics.mean(all_values)
        std_dev = statistics.stdev(all_values) if len(all_values) > 1 else 0.0
        
        if std_dev == 0:
            return anomalies  # No variation
        
        # Check each node
        for node_id, values in expression_values.items():
            node_values = values if isinstance(values, list) else [values]
            
            for value in node_values:
                z_score = abs((value - mean) / std_dev)
                
                if z_score > self.threshold_z_score:
                    severity = "high" if z_score > 4.0 else "medium"
                    anomalies.append(Anomaly(
                        node_id=node_id,
                        anomaly_type=AnomalyType.STATISTICAL,
                        score=z_score,
                        severity=severity,
                        description=f"Statistical anomaly: Z-score = {z_score:.2f} (mean={mean:.2f}, std={std_dev:.2f})"
                    ))
        
        return anomalies
    
    def _detect_pattern_anomalies(
        self,
        expression_values: Dict[str, List[float]]
    ) -> List[Anomaly]:
        """Detect anomalies based on patterns"""
        anomalies = []
        
        # Detect nodes with unusual patterns
        for node_id, values in expression_values.items():
            node_values = values if isinstance(values, list) else [values]
            
            if len(node_values) < 3:
                continue
            
            # Check for sudden changes
            changes = [abs(node_values[i] - node_values[i-1]) for i in range(1, len(node_values))]
            if changes:
                max_change = max(changes)
                mean_change = statistics.mean(changes)
                std_change = statistics.stdev(changes) if len(changes) > 1 else 0.0
                
                if std_change > 0 and max_change > mean_change + 2 * std_change:
                    score = max_change / (mean_change + std_change) if (mean_change + std_change) > 0 else 0
                    anomalies.append(Anomaly(
                        node_id=node_id,
                        anomaly_type=AnomalyType.PATTERN,
                        score=score,
                        severity="medium",
                        description=f"Pattern anomaly: Sudden change detected (change={max_change:.2f})"
                    ))
        
        return anomalies
    
    def _detect_threshold_anomalies(
        self,
        expression_values: Dict[str, List[float]]
    ) -> List[Anomaly]:
        """Detect anomalies based on threshold violations"""
        anomalies = []
        
        # Collect all values for percentile calculation
        all_values = []
        for values in expression_values.values():
            all_values.extend(values if isinstance(values, list) else [values])
        
        if not all_values:
            return anomalies
        
        # Calculate thresholds
        threshold_high = np.percentile(all_values, self.threshold_percentile * 100)
        threshold_low = np.percentile(all_values, (1 - self.threshold_percentile) * 100)
        
        # Check each node
        for node_id, values in expression_values.items():
            node_values = values if isinstance(values, list) else [values]
            
            for value in node_values:
                if value > threshold_high:
                    score = (value - threshold_high) / threshold_high if threshold_high > 0 else 1.0
                    anomalies.append(Anomaly(
                        node_id=node_id,
                        anomaly_type=AnomalyType.THRESHOLD,
                        score=score,
                        severity="high" if score > 0.5 else "medium",
                        description=f"Threshold anomaly: Value {value:.2f} exceeds high threshold {threshold_high:.2f}"
                    ))
                elif value < threshold_low:
                    score = (threshold_low - value) / abs(threshold_low) if threshold_low != 0 else 1.0
                    anomalies.append(Anomaly(
                        node_id=node_id,
                        anomaly_type=AnomalyType.THRESHOLD,
                        score=score,
                        severity="high" if score > 0.5 else "medium",
                        description=f"Threshold anomaly: Value {value:.2f} below low threshold {threshold_low:.2f}"
                    ))
        
        return anomalies
    
    def _detect_baseline_anomalies(
        self,
        expression_values: Dict[str, List[float]],
        baseline_data: Dict[str, Any]
    ) -> List[Anomaly]:
        """Detect anomalies by comparing with baseline"""
        anomalies = []
        
        baseline_values = self._extract_expression_values(baseline_data)
        
        # Compare each node
        for node_id in expression_values.keys():
            if node_id not in baseline_values:
                continue
            
            current = expression_values[node_id]
            baseline = baseline_values[node_id]
            
            current_val = current[0] if isinstance(current, list) else current
            baseline_val = baseline[0] if isinstance(baseline, list) else baseline
            
            # Calculate deviation
            if baseline_val != 0:
                deviation = abs((current_val - baseline_val) / baseline_val)
                
                if deviation > 0.5:  # 50% deviation threshold
                    anomalies.append(Anomaly(
                        node_id=node_id,
                        anomaly_type=AnomalyType.STATISTICAL,
                        score=deviation,
                        severity="high" if deviation > 1.0 else "medium",
                        description=f"Baseline deviation: {deviation*100:.1f}% from baseline"
                    ))
        
        return anomalies
    
    def _anomaly_to_dict(self, anomaly: Anomaly) -> Dict[str, Any]:
        """Convert Anomaly dataclass to dictionary"""
        return {
            "node_id": anomaly.node_id,
            "anomaly_type": anomaly.anomaly_type.value,
            "score": anomaly.score,
            "severity": anomaly.severity,
            "description": anomaly.description,
            "timestamp": anomaly.timestamp
        }
    
    def _generate_summary(self, anomalies: List[Anomaly]) -> Dict[str, Any]:
        """Generate summary of anomalies"""
        if not anomalies:
            return {
                "total": 0,
                "by_severity": {},
                "by_type": {}
            }
        
        by_severity = {}
        by_type = {}
        
        for anomaly in anomalies:
            # Count by severity
            by_severity[anomaly.severity] = by_severity.get(anomaly.severity, 0) + 1
            
            # Count by type
            by_type[anomaly.anomaly_type.value] = by_type.get(anomaly.anomaly_type.value, 0) + 1
        
        return {
            "total": len(anomalies),
            "by_severity": by_severity,
            "by_type": by_type,
            "max_score": max(a.score for a in anomalies) if anomalies else 0.0
        }

