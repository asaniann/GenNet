# GenNet API Documentation

## Overview

GenNet provides a comprehensive REST API for gene regulatory network analysis, qualitative and hybrid modeling, ML-based predictions, and personalized health insights.

**Base URL**: `https://api.gennet.example.com/api/v1`

**API Version**: v1

**Authentication**: Bearer token (JWT)

**Content-Type**: `application/json`

## Quick Start

### 1. Authenticate

```bash
curl -X POST "https://api.gennet.example.com/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. Use the Token

```bash
curl -X GET "https://api.gennet.example.com/api/v1/networks" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Authentication

### Login

Authenticate and receive an access token.

**Endpoint**: `POST /auth/token`

**Content-Type**: `application/x-www-form-urlencoded`

**Request Body**:
```
username=your_username&password=your_password
```

**cURL Example**:
```bash
curl -X POST "https://api.gennet.example.com/api/v1/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user&password=pass"
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Error Responses**:
- `401 Unauthorized`: Invalid credentials
  ```json
  {
    "detail": "Incorrect username or password"
  }
  ```
- `422 Unprocessable Entity`: Missing or invalid parameters

## Networks API

### List Networks
```http
GET /networks
Authorization: Bearer {token}
```

### Create Network
```http
POST /networks
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "My Network",
  "description": "Network description",
  "nodes": [...],
  "edges": [...]
}
```

### Get Network
```http
GET /networks/{network_id}
Authorization: Bearer {token}
```

## Qualitative Modeling API

### Verify CTL Formula

Verify the syntax and semantics of a CTL (Computation Tree Logic) formula.

**Endpoint**: `POST /qualitative/ctl/verify`

**Headers**:
- `Authorization: Bearer {token}`
- `Content-Type: application/json`

**Request Body**:
```json
{
  "formula": "AG(p -> AF q)",
  "description": "Property description (optional)"
}
```

**cURL Example**:
```bash
curl -X POST "https://api.gennet.example.com/api/v1/qualitative/ctl/verify" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "formula": "AG(p -> AF q)",
    "description": "Property description"
  }'
```

**Response** (200 OK):
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "formula": "AG(p -> AF q)",
  "description": "Property description",
  "parsed_structure": {
    "original": "AG(p -> AF q)",
    "operators": ["AG", "AF"],
    "complexity": 2,
    "has_temporal": true,
    "has_path_quantifiers": true
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid formula format
  ```json
  {
    "valid": false,
    "errors": ["Unbalanced parentheses"],
    "warnings": []
  }
  ```
- `500 Internal Server Error`: Server error during verification

### Generate Parameters
```http
POST /qualitative/parameters/generate?network_id={network_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "formula": "AG(p -> AF q)",
  "network_structure": {...}
}
```

### Generate State Graph
```http
POST /qualitative/state-graph/generate?network_id={network_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "parameters": {...},
  "network_structure": {...}
}
```

## Hybrid Modeling API

### Compute Time Delays
```http
POST /hybrid/time-delays/compute
Authorization: Bearer {token}
Content-Type: application/json

{
  "network_id": "net-123",
  "parameters": {...},
  "time_constraints": {...}
}
```

### Analyze Trajectory
```http
POST /hybrid/trajectory/analyze
Authorization: Bearer {token}
Content-Type: application/json

{
  "network_id": "net-123",
  "parameters": {...},
  "initial_state": {...},
  "time_horizon": 10.0,
  "time_step": 0.1
}
```

## ML Service API

### Predict Parameters
```http
POST /ml/prediction/parameters?network_id={network_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "expression_data": {...},
  "network_structure": {...}
}
```

### Detect Anomalies
```http
POST /ml/analysis/anomaly-detection?network_id={network_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "expression_data": {...},
  "baseline_data": {...}
}
```

### Predict Disease
```http
POST /ml/analysis/disease-prediction?network_id={network_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "expression_data": {...},
  "network_structure": {...}
}
```

## Health Service API

### Generate Health Report
```http
POST /health/reports/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "patient_id": "patient-123",
  "disease_code": "ICD10:C50",
  "format": "pdf"
}
```

### Get Health Predictions
```http
GET /health/predictions?patient_id={patient_id}&disease_code={code}
Authorization: Bearer {token}
```

## Workflows API

### Create Workflow
```http
POST /workflows
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Analysis Workflow",
  "workflow_type": "qualitative",
  "network_id": "net-123",
  "parameters": {
    "ctl_formula": "AG(p -> AF q)"
  }
}
```

### Get Workflow Status
```http
GET /workflows/{workflow_id}
Authorization: Bearer {token}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "Error type",
  "message": "Error message",
  "details": {...}
}
```

**Status Codes**:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

## Rate Limiting

Rate limits are applied per service:
- Auth Service: 60 requests/minute
- GRN Service: 100 requests/minute
- Workflow Service: 30 requests/minute
- ML Service: 10 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## Pagination

List endpoints support pagination:

```http
GET /networks?page=1&limit=20
```

**Response**:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

## Webhooks

Webhooks are available for workflow completion:

```http
POST /webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["workflow.completed", "workflow.failed"]
}
```

