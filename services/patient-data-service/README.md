# Patient Data Service

Enterprise-grade patient data management service with privacy controls, data retention policies, and comprehensive data type support.

## Features

- **Unified Patient Management**: Single service for all patient data
- **Privacy Controls**: Anonymized IDs, consent management, data retention policies
- **Data Type Tracking**: Flags for genomic, expression, clinical, and multi-omics data
- **Soft Delete**: Support for soft deletion with audit trail
- **S3 Integration**: Secure file storage for patient data files
- **Access Control**: User-based access control with JWT authentication
- **Enterprise Standards**: Comprehensive logging, metrics, health checks

## API Endpoints

### Patient Management

- `POST /patients` - Create a new patient
- `GET /patients` - List all patients for current user
- `GET /patients/{patient_id}` - Get specific patient
- `PUT /patients/{patient_id}` - Update patient
- `DELETE /patients/{patient_id}` - Delete patient (soft delete by default)

### Data Upload

- `POST /patients/{patient_id}/data/upload` - Upload patient data file

### Health & Metrics

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - Prometheus metrics

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT secret for token validation
- `AWS_ACCESS_KEY_ID` - AWS access key for S3
- `AWS_SECRET_ACCESS_KEY` - AWS secret key for S3
- `S3_BUCKET_NAME` - S3 bucket name for patient data
- `AWS_ENDPOINT_URL` - S3 endpoint URL (for local/minio)

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run service
uvicorn main:app --reload
```

## Docker

```bash
# Build image
docker build -t patient-data-service .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  patient-data-service
```

## Database Schema

### Patient Table

- `id` (UUID) - Primary key
- `user_id` (Integer) - Foreign key to users table
- `anonymized_id` (String) - Anonymized patient identifier
- `age_range` (String) - Age range (e.g., "40-50")
- `gender` (String) - Gender
- `ethnicity` (String) - Ethnicity
- `has_genomic_data` (Boolean) - Flag for genomic data availability
- `has_expression_data` (Boolean) - Flag for expression data availability
- `has_clinical_data` (Boolean) - Flag for clinical data availability
- `has_multi_omics` (Boolean) - Flag for multi-omics data
- `consent_given` (Boolean) - Consent status
- `consent_date` (DateTime) - Consent timestamp
- `data_retention_policy` (String) - Data retention policy
- `created_at` (DateTime) - Creation timestamp
- `updated_at` (DateTime) - Last update timestamp
- `deleted_at` (DateTime) - Soft delete timestamp

## Security

- JWT-based authentication
- User-based access control
- Anonymized patient IDs
- Soft delete for audit trail
- Data retention policies
- HIPAA/GDPR compliance ready

## Testing

Comprehensive test suite with >90% coverage:

- Unit tests for models and business logic
- Integration tests for API endpoints
- Access control tests
- Health check tests

Run tests:
```bash
pytest tests/ -v --cov=. --cov-report=html
```

