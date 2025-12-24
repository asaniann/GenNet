# Patient-Specific GRN Construction Guide

## Overview

The GRN Service now supports building patient-specific Gene Regulatory Networks from patient expression data.

## Methods

### 1. Reference-Based

Adjusts a population reference GRN based on patient expression data.

### 2. De Novo

Infers GRN directly from patient expression data using inference algorithms (GENIE3, ARACNE).

### 3. Hybrid

Combines reference-based and de novo approaches for optimal results.

## API Endpoints

### Build Patient GRN

```bash
POST /api/v1/grn/patient/{patient_id}/build
Content-Type: application/json

{
  "method": "hybrid",
  "reference_grn_id": "ref-network-123"
}
```

### Get Patient Networks

```bash
GET /api/v1/grn/patient/{patient_id}/networks
```

### Compare Networks

```bash
POST /api/v1/grn/patient/{patient_id}/compare
Content-Type: application/json

{
  "network_id1": "patient-network-123",
  "network_id2": "reference-network-456",
  "analyze_perturbations": true
}
```

## Perturbation Analysis

The service can analyze perturbations between patient and reference networks:

- Edge differences (added, removed, modified)
- Perturbation scores
- Perturbed pathway identification
- Disease associations

## Integration

- **Patient Data Service**: Fetches patient expression data
- **ML Service**: Uses inference algorithms (GENIE3, ARACNE)
- **Expression Analysis Service**: Gets expression signatures

