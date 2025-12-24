# Security & Compliance Guide

## Overview

GenNet implements comprehensive security and compliance features for HIPAA and GDPR requirements.

## HIPAA Compliance

### Access Logging

All PHI (Protected Health Information) access is logged:

```python
from shared.hipaa_compliance import HIPAACompliance

hipaa = HIPAACompliance()
hipaa.log_phi_access(
    user_id=1,
    patient_id="patient-123",
    access_type="view",
    resource_type="genomic",
    resource_id="profile-456"
)
```

### Audit Trails

All data access and modifications are logged to audit database and Kafka.

### Encryption

Field-level encryption for sensitive data:

```python
from shared.encryption import encrypt_field, decrypt_field

encrypted = encrypt_field("sensitive_value")
decrypted = decrypt_field(encrypted)
```

## GDPR Compliance

### Data Subject Rights

#### Right to Access (Data Export)

```bash
POST /api/v1/patients/data-subject-rights/export/{patient_id}
```

#### Right to Erasure (Data Deletion)

```bash
DELETE /api/v1/patients/data-subject-rights/delete/{patient_id}
```

#### Right to Rectification (Data Update)

```bash
PUT /api/v1/patients/data-subject-rights/rectify/{patient_id}
```

### Consent Management

Consent is tracked and verified before processing patient data.

## Security Features

### Input Validation

All inputs are validated and sanitized:

```python
from shared.input_validation import InputValidator

validator = InputValidator()
sanitized = validator.sanitize_string(user_input)
is_safe = validator.validate_sql_safe(user_input)
```

### Rate Limiting

Rate limiting is implemented to prevent abuse (see `shared/rate_limiting.py`).

### JWT Validation

Enhanced JWT validation with optional auth service verification:

```python
from shared.jwt_validator import JWTValidator

validator = JWTValidator()
payload = validator.validate_token(token)
user_id = validator.extract_user_id(token)
```

## Compliance Checklist

- [x] Access logging
- [x] Audit trails
- [x] Data encryption
- [x] GDPR data subject rights
- [x] Consent management
- [x] Input validation
- [x] Rate limiting
- [x] Enhanced JWT validation

