"""
Alert engine for real-time monitoring
"""

from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AlertEngine:
    """Generate alerts based on real-time events"""
    
    def __init__(self):
        """Initialize alert engine"""
        self.thresholds = {
            "risk_score": {
                "high": 75.0,
                "critical": 90.0
            },
            "prediction_change": {
                "significant": 20.0  # 20% change
            }
        }
    
    def check_event_for_alerts(
        self,
        event: Dict[str, Any],
        previous_value: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Check if event should trigger alerts
        
        Args:
            event: Event data
            previous_value: Previous value for comparison
            
        Returns:
            List of alerts (empty if none)
        """
        alerts = []
        event_type = event.get("event_type")
        event_data = event.get("event_data", {})
        
        if event_type == "prediction":
            # Check risk score thresholds
            risk_score = event_data.get("risk_score")
            if risk_score:
                if risk_score >= self.thresholds["risk_score"]["critical"]:
                    alerts.append({
                        "alert_type": "risk_change",
                        "severity": "critical",
                        "title": "Critical Risk Level Detected",
                        "message": f"Patient risk score has reached critical level: {risk_score:.1f}%",
                        "alert_data": {"risk_score": risk_score}
                    })
                elif risk_score >= self.thresholds["risk_score"]["high"]:
                    alerts.append({
                        "alert_type": "risk_change",
                        "severity": "high",
                        "title": "High Risk Level Detected",
                        "message": f"Patient risk score is elevated: {risk_score:.1f}%",
                        "alert_data": {"risk_score": risk_score}
                    })
                
                # Check for significant change
                if previous_value is not None:
                    change = abs(risk_score - previous_value)
                    if change >= self.thresholds["prediction_change"]["significant"]:
                        alerts.append({
                            "alert_type": "risk_change",
                            "severity": "medium",
                            "title": "Significant Risk Change",
                            "message": f"Risk score changed by {change:.1f}% (from {previous_value:.1f}% to {risk_score:.1f}%)",
                            "alert_data": {
                                "previous_value": previous_value,
                                "current_value": risk_score,
                                "change": change
                            }
                        })
        
        elif event_type == "anomaly":
            alerts.append({
                "alert_type": "anomaly",
                "severity": "high",
                "title": "Anomaly Detected",
                "message": "Anomalous pattern detected in patient data",
                "alert_data": event_data
            })
        
        return alerts

