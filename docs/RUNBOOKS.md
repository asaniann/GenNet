# GenNet Runbooks

This document provides operational runbooks for common scenarios, troubleshooting, and maintenance procedures.

## Table of Contents

1. [Incident Response](#incident-response)
2. [Deployment Procedures](#deployment-procedures)
3. [Maintenance Procedures](#maintenance-procedures)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Disaster Recovery](#disaster-recovery)
6. [Troubleshooting](#troubleshooting)

## Incident Response

### Service Down

**Symptoms**:
- Service health check failing
- 503 errors from service
- No pods running

**Steps**:
1. Check pod status: `kubectl get pods -n gennet-system -l app={service-name}`
2. Check logs: `kubectl logs -n gennet-system -l app={service-name} --tail=100`
3. Check events: `kubectl get events -n gennet-system --sort-by='.lastTimestamp'`
4. Restart deployment: `kubectl rollout restart deployment/{service-name} -n gennet-system`
5. Scale up if needed: `kubectl scale deployment/{service-name} --replicas=3 -n gennet-system`

### High Error Rate

**Symptoms**:
- Error rate > 5%
- Alert firing
- User complaints

**Steps**:
1. Check Prometheus metrics: `rate(http_requests_total{status=~"5.."}[5m])`
2. Check service logs for errors
3. Check circuit breaker status
4. Check database connections
5. Check external service dependencies
6. Rollback if recent deployment: `kubectl rollout undo deployment/{service-name}`

### Database Connection Issues

**Symptoms**:
- Database connection errors in logs
- Timeout errors
- High connection pool usage

**Steps**:
1. Check RDS status: `aws rds describe-db-instances --db-instance-identifier gennet-db`
2. Check connection pool metrics
3. Check for long-running queries
4. Restart connection pool if needed
5. Scale database if needed
6. Check network connectivity

### High Memory Usage

**Symptoms**:
- Memory usage > 90%
- OOMKilled pods
- Performance degradation

**Steps**:
1. Check memory metrics: `kubectl top pods -n gennet-system`
2. Identify memory leaks in logs
3. Increase memory limits: Update deployment resource limits
4. Scale horizontally: `kubectl scale deployment/{service-name} --replicas=5`
5. Check for memory leaks in code

### High CPU Usage

**Symptoms**:
- CPU usage > 80%
- Slow response times
- Timeout errors

**Steps**:
1. Check CPU metrics: `kubectl top pods -n gennet-system`
2. Identify CPU-intensive operations
3. Scale horizontally: `kubectl scale deployment/{service-name} --replicas=5`
4. Optimize code if needed
5. Check for infinite loops or blocking operations

## Deployment Procedures

### Standard Deployment

1. **Pre-deployment checks**:
   ```bash
   ./scripts/validate_setup.sh
   kubectl get pods -n gennet-system
   ```

2. **Deploy**:
   ```bash
   kubectl apply -f infrastructure/kubernetes/{service}-deployment.yaml
   kubectl rollout status deployment/{service-name} -n gennet-system
   ```

3. **Post-deployment verification**:
   ```bash
   kubectl get pods -n gennet-system -l app={service-name}
   curl https://api.gennet.example.com/api/v1/health/{service-name}
   ```

### Blue-Green Deployment

1. **Deploy green**:
   ```bash
   ./scripts/deploy-blue-green.sh production {service-name}
   ```

2. **Verify green**:
   ```bash
   kubectl get pods -n gennet-system -l version=green
   # Run smoke tests
   ```

3. **Switch traffic**:
   ```bash
   kubectl patch service {service-name} -n gennet-system \
     -p '{"spec":{"selector":{"version":"green"}}}'
   ```

4. **Monitor**:
   ```bash
   kubectl get pods -n gennet-system
   # Monitor metrics for 10 minutes
   ```

### Rollback Procedure

1. **Identify bad deployment**:
   ```bash
   kubectl rollout history deployment/{service-name} -n gennet-system
   ```

2. **Rollback**:
   ```bash
   kubectl rollout undo deployment/{service-name} -n gennet-system
   kubectl rollout status deployment/{service-name} -n gennet-system
   ```

3. **Verify**:
   ```bash
   kubectl get pods -n gennet-system -l app={service-name}
   # Verify service health
   ```

## Maintenance Procedures

### Database Backup

1. **Manual backup**:
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier gennet-db \
     --db-snapshot-identifier gennet-manual-$(date +%Y%m%d)
   ```

2. **Verify backup**:
   ```bash
   aws rds describe-db-snapshots --db-instance-identifier gennet-db
   ```

### Secret Rotation

1. **Rotate secret**:
   ```bash
   ./scripts/rotate-secrets.sh gennet/database/credentials
   ```

2. **Verify rotation**:
   ```bash
   kubectl get secret database-secrets -n gennet-system -o jsonpath='{.data}'
   ```

### Certificate Renewal

1. **Check certificate expiry**:
   ```bash
   kubectl get certificate -n gennet-system
   ```

2. **Renew if needed**:
   ```bash
   kubectl delete certificate {cert-name} -n gennet-system
   # Cert-manager will automatically renew
   ```

## Monitoring & Alerts

### Check Service Health

```bash
# All services
kubectl get pods -n gennet-system

# Specific service
kubectl get pods -n gennet-system -l app={service-name}

# Check health endpoint
curl https://api.gennet.example.com/api/v1/health/{service-name}
```

### View Logs

```bash
# Recent logs
kubectl logs -n gennet-system -l app={service-name} --tail=100

# Follow logs
kubectl logs -n gennet-system -l app={service-name} -f

# Logs from specific pod
kubectl logs -n gennet-system {pod-name}
```

### Check Metrics

```bash
# Prometheus query
curl 'http://prometheus:9090/api/v1/query?query=up{job="gennet-*"}'

# Grafana dashboards
# Access via: https://grafana.gennet.example.com
```

## Disaster Recovery

### Regional Failover

1. **Trigger failover**:
   ```bash
   ./scripts/dr-failover.sh us-east-1 eu-west-1
   ```

2. **Verify failover**:
   ```bash
   kubectl config use-context eu-west-1
   kubectl get pods -n gennet-system
   ```

3. **Monitor**:
   ```bash
   # Monitor service health for 30 minutes
   # Verify data replication
   ```

### Database Failover

1. **RDS failover**:
   ```bash
   aws rds failover-db-cluster --db-cluster-identifier gennet-cluster
   ```

2. **Verify**:
   ```bash
   aws rds describe-db-clusters --db-cluster-identifier gennet-cluster
   ```

## Performance Tuning

### Database Performance

**Symptoms**: Slow queries, high database CPU

**Steps**:
1. Identify slow queries:
   ```sql
   SELECT query, mean_exec_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   ```

2. Add indexes:
   ```sql
   CREATE INDEX idx_network_user_id ON networks(user_id);
   ```

3. Analyze query plans:
   ```sql
   EXPLAIN ANALYZE SELECT * FROM networks WHERE user_id = 'xxx';
   ```

4. Optimize connection pool:
   - Increase pool size if needed
   - Monitor connection usage
   - Adjust pool_recycle

### Cache Performance

**Symptoms**: Low cache hit rate, high database load

**Steps**:
1. Check cache hit rate:
   ```bash
   redis-cli INFO stats | grep keyspace_hits
   ```

2. Adjust TTL values:
   - Increase TTL for stable data
   - Decrease TTL for frequently changing data

3. Implement cache warming:
   - Pre-load frequently accessed data
   - Warm cache on service startup

### API Performance

**Symptoms**: High latency, timeout errors

**Steps**:
1. Check response times:
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s https://api.gennet.example.com/api/v1/health
   ```

2. Review slow endpoints:
   - Check Prometheus metrics
   - Identify bottlenecks
   - Optimize database queries
   - Add caching

3. Scale horizontally:
   ```bash
   kubectl scale deployment/service-name --replicas=5 -n gennet-system
   ```

## Capacity Planning

### Resource Estimation

**CPU**:
- Average: 0.5 CPU per service instance
- Peak: 2 CPU per service instance
- Plan for 2x peak capacity

**Memory**:
- Average: 512Mi per service instance
- Peak: 2Gi per service instance
- Plan for 3x peak capacity

**Database**:
- Estimate: 1GB per 10,000 networks
- Plan for 2x growth over 6 months

### Scaling Guidelines

- **Horizontal Scaling**: Preferred for stateless services
- **Vertical Scaling**: For database and stateful services
- **Auto-scaling**: Configure HPA for automatic scaling

## Troubleshooting

### Pod Not Starting

1. Check events: `kubectl describe pod {pod-name} -n gennet-system`
2. Check logs: `kubectl logs {pod-name} -n gennet-system`
3. Check resource limits
4. Check image pull errors
5. Check secrets/configmaps

### Service Unreachable

1. Check service: `kubectl get svc {service-name} -n gennet-system`
2. Check endpoints: `kubectl get endpoints {service-name} -n gennet-system`
3. Check ingress: `kubectl get ingress -n gennet-system`
4. Check network policies
5. Check firewall rules

### Performance Issues

1. Check resource usage: `kubectl top pods -n gennet-system`
2. Check database performance
3. Check cache hit rates
4. Check external service latency
5. Review slow query logs

