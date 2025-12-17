"""
Health Monitoring Module
Tracks longitudinal health changes and generates alerts
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class HealthAlert:
    """Health monitoring alert"""
    patient_id: str
    alert_type: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metric: str
    value: float
    threshold: float


class HealthMonitor:
    """Monitor patient health over time"""
    
    def __init__(self):
        self.alert_thresholds = {
            "risk_score_increase": 0.2,  # 20% increase triggers alert
            "risk_score_high": 0.75,  # Risk score above 75% is high
            "anomaly_detected": True,  # Any anomaly triggers alert
            "disease_risk_change": 0.15  # 15% change in disease risk
        }
    
    def check_health_changes(
        self,
        patient_id: str,
        current_predictions: Dict[str, Any],
        historical_predictions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Check for significant health changes
        
        Args:
            patient_id: Patient ID
            current_predictions: Current prediction results
            historical_predictions: Historical predictions for comparison
            
        Returns:
            Health change analysis and alerts
        """
        alerts = []
        trends = {}
        
        if historical_predictions and len(historical_predictions) > 0:
            # Compare with historical data
            latest_historical = historical_predictions[-1]
            
            # Check risk score changes
            current_risk = self._extract_risk_score(current_predictions)
            historical_risk = self._extract_risk_score(latest_historical)
            
            if current_risk is not None and historical_risk is not None:
                risk_change = current_risk - historical_risk
                
                if abs(risk_change) > self.alert_thresholds["risk_score_increase"]:
                    severity = AlertSeverity.HIGH if abs(risk_change) > 0.3 else AlertSeverity.MEDIUM
                    alerts.append(HealthAlert(
                        patient_id=patient_id,
                        alert_type="risk_score_change",
                        severity=severity,
                        message=f"Risk score changed by {risk_change*100:.1f}%",
                        timestamp=datetime.utcnow(),
                        metric="risk_score",
                        value=current_risk,
                        threshold=historical_risk
                    ))
                
                trends["risk_score"] = {
                    "current": current_risk,
                    "previous": historical_risk,
                    "change": risk_change,
                    "trend": "increasing" if risk_change > 0 else "decreasing"
                }
            
            # Check disease prediction changes
            disease_changes = self._check_disease_changes(
                current_predictions,
                latest_historical
            )
            alerts.extend(disease_changes)
            trends["disease_predictions"] = disease_changes
        
        # Check for high risk scores
        current_risk = self._extract_risk_score(current_predictions)
        if current_risk and current_risk > self.alert_thresholds["risk_score_high"]:
            alerts.append(HealthAlert(
                patient_id=patient_id,
                alert_type="high_risk",
                severity=AlertSeverity.HIGH,
                message=f"High risk score detected: {current_risk*100:.1f}%",
                timestamp=datetime.utcnow(),
                metric="risk_score",
                value=current_risk,
                threshold=self.alert_thresholds["risk_score_high"]
            ))
        
        # Check for anomalies
        if "ml" in current_predictions and current_predictions["ml"]:
            ml_data = current_predictions["ml"]
            if ml_data.get("anomaly_detection"):
                anomalies = ml_data["anomaly_detection"].get("anomalies", [])
                if anomalies:
                    high_severity_anomalies = [a for a in anomalies if a.get("severity") in ["high", "critical"]]
                    if high_severity_anomalies:
                        alerts.append(HealthAlert(
                            patient_id=patient_id,
                            alert_type="anomaly_detected",
                            severity=AlertSeverity.HIGH,
                            message=f"{len(high_severity_anomalies)} high-severity anomalies detected",
                            timestamp=datetime.utcnow(),
                            metric="anomaly_count",
                            value=len(high_severity_anomalies),
                            threshold=0
                        ))
        
        return {
            "patient_id": patient_id,
            "alerts": [self._alert_to_dict(a) for a in alerts],
            "alert_count": len(alerts),
            "trends": trends,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _extract_risk_score(self, predictions: Dict[str, Any]) -> Optional[float]:
        """Extract risk score from predictions"""
        # Try ensemble prediction first
        ensemble = predictions.get("ensemble_prediction", {})
        if ensemble and "risk_score" in ensemble:
            return ensemble["risk_score"]
        
        # Try ML prediction
        if "ml" in predictions and predictions["ml"]:
            ml_pred = predictions["ml"].get("disease_prediction", {})
            top_pred = ml_pred.get("top_prediction", {})
            if top_pred and "risk_score" in top_pred:
                return top_pred["risk_score"]
        
        # Try genomic PRS
        if "genomic" in predictions and predictions["genomic"]:
            prs = predictions["genomic"].get("prs_score", 0.0)
            if prs:
                return prs / 100.0  # Normalize to 0-1
        
        return None
    
    def _check_disease_changes(
        self,
        current: Dict[str, Any],
        historical: Dict[str, Any]
    ) -> List[HealthAlert]:
        """Check for changes in disease predictions"""
        alerts = []
        
        # Extract disease predictions
        current_diseases = self._extract_disease_predictions(current)
        historical_diseases = self._extract_disease_predictions(historical)
        
        # Compare disease risks
        for disease_code, current_risk in current_diseases.items():
            historical_risk = historical_diseases.get(disease_code, 0.0)
            
            if historical_risk > 0:
                change = abs(current_risk - historical_risk) / historical_risk
                
                if change > self.alert_thresholds["disease_risk_change"]:
                    severity = AlertSeverity.MEDIUM if change < 0.3 else AlertSeverity.HIGH
                    alerts.append(HealthAlert(
                        patient_id="",  # Will be set by caller
                        alert_type="disease_risk_change",
                        severity=severity,
                        message=f"Disease {disease_code} risk changed by {change*100:.1f}%",
                        timestamp=datetime.utcnow(),
                        metric=f"disease_risk_{disease_code}",
                        value=current_risk,
                        threshold=historical_risk
                    ))
        
        return alerts
    
    def _extract_disease_predictions(self, predictions: Dict[str, Any]) -> Dict[str, float]:
        """Extract disease predictions from prediction data"""
        diseases = {}
        
        # From ML service
        if "ml" in predictions and predictions["ml"]:
            ml_pred = predictions["ml"].get("disease_prediction", {})
            pred_list = ml_pred.get("predictions", [])
            for pred in pred_list:
                disease_code = pred.get("disease_code", "")
                risk_score = pred.get("risk_score", 0.0)
                if disease_code:
                    diseases[disease_code] = risk_score
        
        return diseases
    
    def _alert_to_dict(self, alert: HealthAlert) -> Dict[str, Any]:
        """Convert HealthAlert to dictionary"""
        return {
            "patient_id": alert.patient_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold
        }

