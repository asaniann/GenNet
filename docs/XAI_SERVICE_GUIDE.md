# Explainable AI Service Guide

## Overview

The Explainable AI (XAI) Service provides interpretable explanations for health predictions using SHAP (SHapley Additive exPlanations) and LIME (Local Interpretable Model-agnostic Explanations).

## Features

- **SHAP Explanations**: Feature importance and contribution analysis
- **LIME Explanations**: Local interpretability around predictions
- **Natural Language Explanations**: Human-readable explanations
- **Visualization**: SHAP and LIME plots
- **Integration**: Seamless integration with Health Service

## API Endpoints

### Generate SHAP Explanation

```bash
POST /api/v1/xai/shap/explain
Content-Type: application/json

{
  "prediction_id": "pred-123",
  "patient_id": "patient-456",
  "prediction_value": 75.5,
  "model_type": "ensemble",
  "features": {
    "genomic_risk": 0.65,
    "expression_score": 0.72,
    "clinical_factors": 0.58
  }
}
```

### Generate LIME Explanation

```bash
POST /api/v1/xai/lime/explain
Content-Type: application/json

{
  "prediction_id": "pred-123",
  "patient_id": "patient-456",
  "prediction_value": 75.5,
  "features": {
    "genomic_risk": 0.65,
    "expression_score": 0.72
  },
  "training_data": [...]
}
```

### Get Explanation

```bash
GET /api/v1/xai/explanations/{explanation_id}
```

## Integration with Health Service

The Health Service automatically generates explanations when creating health reports. Explanations are included in PDF and JSON reports.

## Usage Examples

See `docs/INTEGRATION_GUIDE.md` for detailed integration examples.

