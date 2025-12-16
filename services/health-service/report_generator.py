"""
Health report generator
Generates PDF, JSON, and HTML reports
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import json

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate health reports in various formats"""
    
    def generate_pdf_report(
        self,
        patient_id: str,
        predictions: Dict,
        recommendations: List[Dict],
        output_path: str
    ) -> bool:
        """
        Generate PDF health report
        
        Args:
            patient_id: Patient ID
            predictions: Prediction data
            recommendations: List of recommendations
            output_path: Path to save PDF
            
        Returns:
            True if successful
        """
        try:
            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*inch, height - 1*inch, "Personalized Health Report")
            
            # Patient ID
            c.setFont("Helvetica", 12)
            c.drawString(1*inch, height - 1.5*inch, f"Patient ID: {patient_id}")
            
            # Predictions section
            y_pos = height - 2*inch
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1*inch, y_pos, "Health Predictions")
            
            y_pos -= 0.3*inch
            c.setFont("Helvetica", 10)
            
            ensemble_pred = predictions.get("ensemble_prediction", {})
            if ensemble_pred:
                risk_score = ensemble_pred.get("risk_score", 0.0)
                c.drawString(1.2*inch, y_pos, f"Overall Risk Score: {risk_score:.1f}")
                y_pos -= 0.2*inch
            
            # Recommendations section
            y_pos -= 0.3*inch
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1*inch, y_pos, "Recommendations")
            
            y_pos -= 0.3*inch
            c.setFont("Helvetica", 10)
            
            for rec in recommendations[:5]:  # Limit to 5 for PDF
                c.drawString(1.2*inch, y_pos, f"• {rec.get('title', '')}")
                y_pos -= 0.2*inch
                if y_pos < 1*inch:
                    c.showPage()
                    y_pos = height - 1*inch
            
            c.save()
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return False
    
    def generate_json_report(
        self,
        patient_id: str,
        predictions: Dict,
        recommendations: List[Dict]
    ) -> Dict[str, Any]:
        """Generate JSON health report"""
        return {
            "patient_id": patient_id,
            "generated_at": datetime.utcnow().isoformat(),
            "predictions": predictions,
            "recommendations": recommendations,
            "summary": self._create_summary(predictions, recommendations)
        }
    
    def generate_html_report(
        self,
        patient_id: str,
        predictions: Dict,
        recommendations: List[Dict]
    ) -> str:
        """Generate HTML health report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Health Report - {patient_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                .prediction {{ background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .recommendation {{ background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>Personalized Health Report</h1>
            <h2>Patient ID: {patient_id}</h2>
            
            <h2>Health Predictions</h2>
            <div class="prediction">
                {self._format_predictions_html(predictions)}
            </div>
            
            <h2>Recommendations</h2>
            {self._format_recommendations_html(recommendations)}
        </body>
        </html>
        """
        return html
    
    def _create_summary(
        self,
        predictions: Dict,
        recommendations: List[Dict]
    ) -> str:
        """Create text summary"""
        ensemble_pred = predictions.get("ensemble_prediction", {})
        risk_score = ensemble_pred.get("risk_score", 0.0)
        
        summary = f"Overall health risk score: {risk_score:.1f}. "
        summary += f"{len(recommendations)} recommendations provided."
        
        return summary
    
    def _format_predictions_html(self, predictions: Dict) -> str:
        """Format predictions for HTML"""
        ensemble_pred = predictions.get("ensemble_prediction", {})
        if ensemble_pred:
            risk_score = ensemble_pred.get("risk_score", 0.0)
            return f"<p><strong>Overall Risk Score:</strong> {risk_score:.1f}</p>"
        return "<p>No predictions available</p>"
    
    def _format_recommendations_html(self, recommendations: List[Dict]) -> str:
        """Format recommendations for HTML"""
        html = ""
        for rec in recommendations:
            html += f"""
            <div class="recommendation">
                <h3>{rec.get('title', '')}</h3>
                <p>{rec.get('description', '')}</p>
                <p><strong>Priority:</strong> {rec.get('priority', 'medium')}</p>
            </div>
            """
        return html

