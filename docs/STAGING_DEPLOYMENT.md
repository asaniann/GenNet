# Staging Deployment Guide

This guide provides step-by-step instructions for deploying GenNet to the staging environment.

## Overview

Staging deployment is used to:
- Validate functionality before production
- Perform integration testing
- Load testing
- User acceptance testing (UAT)

## Prerequisites

- [ ] Staging infrastructure provisioned
- [ ] Kubernetes cluster configured
- [ ] Docker images built and pushed
- [ ] All tests passing
- [ ] Security scans passed

## Pre-Deployment

### 1. Run Pre-Deployment Checks

```bash
./scripts/pre-deployment-check.sh staging
```

This verifies:
- Required tools installed
- Configuration files present
- Kubernetes access
- Dependencies available

### 2. Validate Dependencies

```bash
./scripts/validate_dependencies.sh
```

### 3. Run Test Suite

```bash
./scripts/run_tests.sh
```

All tests must pass before staging deployment.

### 4. Security Scan

```bash
./scripts/security-scan.sh
```

Review and fix any high/critical issues.

## Deployment Steps

### Option 1: Automated Deployment

```bash
./scripts/deploy-staging.sh
```

This script:
1. Runs pre-deployment checks
2. Validates dependencies
3. Runs tests
4. Deploys infrastructure (if needed)
5. Deploys to Kubernetes
6. Verifies monitoring
7. Runs smoke tests
8. Performs health checks

### Option 2: Manual Deployment

#### Step 1: Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform workspace select staging || terraform workspace new staging
terraform init
terraform plan -var-file=terraform.tfvars.staging
terraform apply
```

#### Step 2: Deploy to Kubernetes

```bash
# Set staging context
kubectl config use-context staging

# Create namespace
kubectl create namespace gennet-staging

# Apply manifests
kubectl apply -f infrastructure/kubernetes/ -n gennet-staging

# Wait for deployments
kubectl wait --for=condition=available --timeout=300s deployment --all -n gennet-staging
```

#### Step 3: Verify Deployment

```bash
# Check pod status
kubectl get pods -n gennet-staging

# Check service status
kubectl get svc -n gennet-staging

# Run smoke tests
./scripts/run_smoke_tests.sh staging https://staging-api.gennet.example.com
```

## Post-Deployment Validation

### 1. Health Checks

```bash
# Check all services
for service in auth-service grn-service workflow-service; do
    kubectl get deployment $service -n gennet-staging
    kubectl get pods -n gennet-staging -l app=$service
done
```

### 2. Smoke Tests

```bash
./scripts/run_smoke_tests.sh staging https://staging-api.gennet.example.com
```

### 3. Integration Tests

```bash
# Run integration tests against staging
pytest tests/integration/ --base-url=https://staging-api.gennet.example.com
```

### 4. Load Testing

```bash
# Use your preferred load testing tool
# Example with k6:
k6 run load-tests/staging.js
```

### 5. Monitoring Verification

```bash
./scripts/verify-monitoring.sh staging
```

## Validation Checklist

- [ ] All services deployed and healthy
- [ ] Smoke tests passing
- [ ] Integration tests passing
- [ ] Monitoring configured
- [ ] Alerts configured
- [ ] Logs flowing
- [ ] Tracing working
- [ ] Performance acceptable
- [ ] Security scan passed
- [ ] Documentation updated

## Common Issues

### Services Not Starting

1. Check logs:
   ```bash
   kubectl logs -n gennet-staging deployment/service-name
   ```

2. Check events:
   ```bash
   kubectl get events -n gennet-staging --sort-by='.lastTimestamp'
   ```

3. Check resource limits:
   ```bash
   kubectl describe deployment service-name -n gennet-staging
   ```

### Database Connection Issues

1. Verify database is accessible
2. Check connection strings in ConfigMaps/Secrets
3. Verify network policies allow connections

### High Error Rates

1. Check service logs
2. Review Prometheus metrics
3. Check external dependencies
4. Review recent changes

## Rollback

If issues are detected:

```bash
# Rollback specific service
kubectl rollout undo deployment/service-name -n gennet-staging

# Or use rollback script
./scripts/rollback.sh staging service-name
```

## Next Steps

After successful staging deployment:

1. **Testing**
   - Run full test suite
   - Perform load testing
   - User acceptance testing

2. **Monitoring**
   - Monitor for 24-48 hours
   - Review metrics and logs
   - Verify alerting

3. **Documentation**
   - Document any issues found
   - Update runbooks if needed
   - Prepare production deployment

4. **Production Deployment**
   - Review staging results
   - Complete production checklist
   - Execute production deployment

---

**Last Updated**: 2025-12-16

