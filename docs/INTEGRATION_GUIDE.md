# Integration Guide - Personalized Health Platform

## Overview

This guide documents how the new personalized health services integrate with existing GenNet infrastructure and established genomics tools.

## Service Integration Map

```
┌─────────────────────────────────────────────────────────────┐
│                    Existing Services                         │
├─────────────────────────────────────────────────────────────┤
│  Auth Service      → Authentication & Authorization          │
│  GRN Service       → Network storage (Neo4j)                │
│  ML Service        → GRN inference (GENIE3, ARACNE)         │
│  Workflow Service  → Orchestration                           │
│  Metadata Service  → Data catalog                            │
└──────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐
│ Patient Data │ │  Genomic    │ │ Expression │
│ Service      │ │  Analysis   │ │  Analysis  │
│ (NEW)        │ │  Service    │ │  Service   │
│              │ │  (NEW)      │ │  (NEW)     │
└───────┬──────┘ └─────┬──────┘ └─────┬──────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │    Analysis Router Service    │
        │         (NEW)                  │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │      Ensemble Service          │
        │         (NEW)                  │
        └────────────────────────────────┘
```

## Integration Points

### 1. Patient Data Service Integration

**Purpose**: Central patient data management

**Integrates With**:
- **Auth Service**: Uses JWT tokens for authentication
- **All Analysis Services**: Provides patient context

**API Endpoints Used**:
- `GET /patients/{patient_id}` - Get patient information
- `PUT /patients/{patient_id}` - Update data availability flags

### 2. Genomic Analysis Service Integration

**Purpose**: VCF parsing, variant annotation, PRS calculation

**Integrates With**:
- **Patient Data Service**: Fetches patient info, updates data flags
- **GRN Service**: Creates networks from variant data
- **ML Service**: Optional GRN inference from expression

**Established Tools Used**:
- **cyvcf2**: VCF file parsing (industry standard)
- **pysam**: Genomic file handling
- **NetworkX**: Network analysis (already in requirements)
- **ClinVar API**: Variant clinical significance
- **gnomAD API**: Population frequency data
- **PGS Catalog**: PRS models

**Service Clients**:
```python
# Patient Data Service
patient_client = PatientDataServiceClient()
patient = await patient_client.get_patient(patient_id, token)

# GRN Service
grn_client = GRNServiceClient()
network_id = await grn_client.create_network_from_variants(...)

# ML Service
ml_client = MLServiceClient()
grn = await ml_client.infer_grn_from_expression(...)
```

### 3. Expression Analysis Service (Planned)

**Integrates With**:
- **ML Service**: Uses existing GRN inference (GENIE3, ARACNE, GRNBoost2)
- **GRN Service**: Stores inferred networks
- **Patient Data Service**: Updates expression data flags

**Established Tools to Use**:
- **pySCENIC**: SCENIC algorithm for single-cell
- **GSVA/ssGSEA**: Signature scoring (via R or Python wrappers)
- **NetworkX**: Network analysis

### 4. Analysis Router Service (Planned)

**Purpose**: Intelligent method selection

**Integrates With**:
- **All Analysis Services**: Routes requests based on data availability
- **Workflow Service**: Orchestrates multi-step analyses
- **Ensemble Service**: Coordinates prediction aggregation

### 5. Ensemble Service (Planned)

**Purpose**: Combine predictions from multiple methods

**Integrates With**:
- **All Analysis Services**: Aggregates predictions
- **Health Service**: Provides unified health reports

## Established Tools Integration

### Genomics Tools

1. **cyvcf2** (VCF Parsing)
   - Industry standard for VCF file parsing
   - Fast C-based implementation
   - Used in: Genomic Analysis Service

2. **pysam** (Genomic Files)
   - BAM/SAM/CRAM file handling
   - Used in: Genomic Analysis Service

3. **NetworkX** (Network Analysis)
   - Already in requirements
   - Used in: GRN Service, ML Service, Genomic Analysis Service

### GRN Inference Tools

1. **GENIE3** (ML Service)
   - Already implemented (simplified)
   - Can enhance with full implementation

2. **ARACNE** (ML Service)
   - Placeholder exists
   - Can integrate with established implementations

3. **GRNBoost2** (ML Service)
   - Placeholder exists
   - Can use pySCENIC which includes GRNBoost2

4. **pySCENIC** (Future)
   - Comprehensive single-cell GRN inference
   - Includes GRNBoost2, SCENIC, AUCell
   - Can integrate into Expression Analysis Service

### Annotation Tools

1. **ClinVar API**
   - Variant clinical significance
   - Used in: Genomic Analysis Service

2. **gnomAD API**
   - Population frequency data
   - Used in: Genomic Analysis Service

3. **Ensembl VEP**
   - Variant effect prediction
   - Used in: Genomic Analysis Service

4. **PGS Catalog**
   - Polygenic Risk Score models
   - Used in: Genomic Analysis Service

## Data Flow Examples

### Example 1: Genomic Analysis Workflow

```
1. Patient uploads VCF file
   ↓
2. Patient Data Service stores file in S3
   ↓
3. Genomic Analysis Service:
   - Parses VCF (cyvcf2)
   - Annotates variants (ClinVar, gnomAD, VEP)
   - Calculates PRS (PGS Catalog models)
   ↓
4. Updates Patient Data Service (has_genomic_data = true)
   ↓
5. Optionally creates GRN from variants (GRN Service)
   ↓
6. Returns results
```

### Example 2: Expression + Genomic Integration

```
1. Patient has both genomic and expression data
   ↓
2. Genomic Analysis Service calculates PRS
   ↓
3. Expression Analysis Service scores signatures
   ↓
4. ML Service infers GRN from expression (existing GENIE3)
   ↓
5. GRN Service stores network (existing Neo4j)
   ↓
6. Ensemble Service combines PRS + signatures + GRN predictions
   ↓
7. Health Service generates unified report
```

## Code Reuse

### Shared Utilities

All services use:
- `shared/http_client.py` - Service-to-service communication
- `shared/logging_middleware.py` - Structured logging
- `shared/metrics.py` - Prometheus metrics
- `shared/error_handler.py` - Error handling
- `shared/validation.py` - Input validation

### Database Patterns

- SQLAlchemy ORM (consistent across services)
- Alembic for migrations (where applicable)
- Connection pooling (QueuePool)

### Authentication

- JWT tokens (reused from Auth Service)
- OAuth2PasswordBearer scheme
- User ID extraction pattern

## Next Steps for Integration

1. **Enhance ML Service**
   - Complete GENIE3 implementation
   - Add full ARACNE implementation
   - Integrate pySCENIC for GRNBoost2

2. **Expression Analysis Service**
   - Use existing ML Service for GRN inference
   - Integrate GSVA/ssGSEA (via R or Python)
   - Use NetworkX for network analysis

3. **Analysis Router**
   - Query Patient Data Service for data availability
   - Route to appropriate services
   - Coordinate with Workflow Service

4. **Ensemble Service**
   - Aggregate from all analysis services
   - Use existing ML Service models
   - Integrate with Health Service

## Testing Integration

All services follow existing test patterns:
- pytest with fixtures
- TestClient for API testing
- Mock services for integration tests
- Database fixtures with in-memory SQLite

## Deployment Integration

- Docker Compose: All services in `docker-compose.services.yml`
- Kubernetes: Follows existing deployment patterns
- Health checks: Standard `/health/live` and `/health/ready`
- Metrics: Prometheus endpoints at `/metrics`

---

**Last Updated**: 2024-01-15  
**Status**: Active Development

