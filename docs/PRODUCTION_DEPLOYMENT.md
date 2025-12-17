# Production Deployment Guide

This guide provides step-by-step instructions for deploying GenNet to production.

## ⚠️ Important

Production deployment requires:
- Successful staging deployment
- All tests passing
- Security scans passed
- Production checklist completed
- Stakeholder approval
- Rollback plan ready

## Pre-Deployment Requirements

### 1. Complete Production Checklist

Review and complete all items in:
- `docs/PRODUCTION_DEPLOYMENT_CHECKLIST.md`

### 2. Staging Validation

- [ ] Staging deployment successful
- [ ] All tests passing in staging
- [ ] Load testing completed
- [ ] No critical issues found
- [ ] Monitoring verified

### 3. Security Review

- [ ] Security scan passed
- [ ] Dependencies updated
- [ ] Secrets rotated
- [ ] Access controls reviewed

### 4. Team Readiness

- [ ] On-call rotation scheduled
- [ ] Incident response plan ready
- [ ] Communication plan prepared
- [ ] Stakeholder notification sent

## Deployment Steps

### Option 1: Automated Deployment (Recommended)

```bash
./scripts/deploy-production.sh
```

This script:
1. Runs comprehensive pre-deployment checks
2. Validates dependencies
3. Runs security scan (must pass)
4. Confirms staging deployment
5. Reviews production checklist
6. Deploys infrastructure
7. Deploys to Kubernetes
8. Verifies monitoring
9. Runs smoke tests
10. Performs health checks

### Option 2: Manual Deployment

#### Step 1: Final Verification

```bash
# Pre-deployment checks
./scripts/pre-deployment-check.sh production

# Security scan
./scripts/security-scan.sh

# Verify staging
# Confirm staging deployment was successful
```

#### Step 2: Deploy Infrastructure

```bash
cd infrastructure/terraform
terraform workspace select production || terraform workspace new production
terraform init
terraform plan -var-file=terraform.tfvars -out=tfplan

# Review plan carefully
terraform show tfplan

# Apply (requires confirmation)
terraform apply tfplan
```

#### Step 3: Deploy to Kubernetes

```bash
# Verify production context
kubectl config current-context
# Should be production cluster

# Create namespace
kubectl create namespace gennet-system

# Apply manifests
kubectl apply -f infrastructure/kubernetes/

# Wait for deployments
kubectl wait --for=condition=available --timeout=600s deployment --all -n gennet-system
```

#### Step 4: Verify Monitoring

```bash
./scripts/verify-monitoring.sh production
```

#### Step 5: Run Smoke Tests

```bash
./scripts/run_smoke_tests.sh production https://api.gennet.example.com
```

## Post-Deployment

### Immediate (First Hour)

1. **Monitor Services**
   ```bash
   # Watch pod status
   kubectl get pods -n gennet-system -w
   
   # Check logs
   kubectl logs -f -n gennet-system deployment/service-name
   ```

2. **Verify Health**
   ```bash
   # Check all health endpoints
   curl https://api.gennet.example.com/api/v1/health
   ```

3. **Review Metrics**
   - Check Prometheus for error rates
   - Review Grafana dashboards
   - Verify alerting is working

4. **Monitor Alerts**
   - Watch for any alert notifications
   - Respond to issues immediately

### First 24 Hours

1. **Continuous Monitoring**
   - Monitor all services
   - Review logs regularly
   - Check metrics hourly

2. **User Feedback**
   - Monitor support channels
   - Review user reports
   - Track error rates

3. **Performance**
   - Monitor response times
   - Check resource usage
   - Review database performance

4. **Backup Verification**
   - Verify backups are running
   - Test backup restoration
   - Document backup status

## Rollback Procedures

### Immediate Rollback

If critical issues detected:

```bash
# Rollback specific service
kubectl rollout undo deployment/service-name -n gennet-system

# Or use rollback script
./scripts/rollback.sh production service-name
```

### Full Rollback

If multiple services affected:

```bash
# Rollback all services
./scripts/rollback.sh production all
```

### Infrastructure Rollback

If infrastructure issues:

```bash
cd infrastructure/terraform
terraform destroy -target=module.problematic_module
```

## Success Criteria

Deployment is successful when:
- [ ] All services healthy
- [ ] Smoke tests passing
- [ ] No critical errors
- [ ] Performance acceptable
- [ ] Monitoring operational
- [ ] Alerts configured
- [ ] Users can access services

## Communication

### Pre-Deployment

- Notify stakeholders of deployment window
- Schedule maintenance window if needed
- Prepare communication templates

### During Deployment

- Provide status updates
- Communicate any issues
- Keep stakeholders informed

### Post-Deployment

- Confirm successful deployment
- Share deployment summary
- Document any issues

## Troubleshooting

### Service Not Starting

1. Check logs:
   ```bash
   kubectl logs -n gennet-system deployment/service-name
   ```

2. Check events:
   ```bash
   kubectl get events -n gennet-system --sort-by='.lastTimestamp'
   ```

3. Check resource limits:
   ```bash
   kubectl describe deployment service-name -n gennet-system
   ```

### High Error Rates

1. Check service logs
2. Review Prometheus metrics
3. Check external dependencies
4. Consider rollback if critical

### Performance Issues

1. Check resource usage
2. Review database performance
3. Check cache hit rates
4. Scale services if needed

## Post-Deployment Review

### Week 1

- Review metrics and logs
- Analyze performance
- Document issues
- Plan improvements

### Month 1

- Comprehensive review
- Performance analysis
- Cost review
- User feedback analysis

## Emergency Procedures

### Critical Incident

1. **Immediate Actions**
   - Assess impact
   - Notify team
   - Begin rollback if needed

2. **Communication**
   - Notify stakeholders
   - Provide status updates
   - Document incident

3. **Resolution**
   - Fix issues
   - Verify resolution
   - Post-mortem

### Contact Information

- **On-Call**: [Contact Info]
- **Escalation**: [Contact Info]
- **Stakeholders**: [Contact Info]

---

**Last Updated**: 2025-12-16
**Next Review**: Before each production deployment

