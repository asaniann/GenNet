# Monitoring Setup Guide

This guide provides instructions for setting up and verifying monitoring, alerting, and dashboards for production.

## Overview

The GenNet platform uses a comprehensive monitoring stack:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Jaeger**: Distributed tracing
- **Fluentd/Fluent Bit**: Log aggregation

## Prerequisites

- Kubernetes cluster access
- `kubectl` configured
- Monitoring namespace created

## Deployment Steps

### 1. Deploy Prometheus

```bash
# Create monitoring namespace
kubectl create namespace monitoring

# Deploy Prometheus
kubectl apply -f infrastructure/kubernetes/monitoring/prometheus/

# Verify deployment
kubectl get pods -n monitoring -l app=prometheus
```

### 2. Deploy Grafana

```bash
# Deploy Grafana
kubectl apply -f infrastructure/kubernetes/monitoring/grafana/

# Get Grafana admin password
kubectl get secret grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d

# Access Grafana (port-forward)
kubectl port-forward -n monitoring service/grafana 3000:3000
# Open http://localhost:3000
```

### 3. Deploy Alertmanager

```bash
# Deploy Alertmanager
kubectl apply -f infrastructure/kubernetes/monitoring/alertmanager/

# Verify deployment
kubectl get pods -n monitoring -l app=alertmanager
```

### 4. Configure Alert Rules

```bash
# Apply alert rules
kubectl apply -f infrastructure/monitoring/prometheus/alerts/services-alerts.yaml

# Verify rules are loaded
kubectl exec -n monitoring deployment/prometheus -- wget -qO- http://localhost:9090/api/v1/rules
```

### 5. Import Grafana Dashboards

1. Access Grafana UI
2. Go to Dashboards > Import
3. Import dashboards from `infrastructure/monitoring/grafana/dashboards/`:
   - `services-overview.json`
   - `business-metrics.json`

### 6. Deploy Jaeger (Tracing)

```bash
# Create tracing namespace
kubectl create namespace tracing

# Deploy Jaeger
kubectl apply -f infrastructure/kubernetes/jaeger/

# Access Jaeger UI (port-forward)
kubectl port-forward -n tracing service/jaeger-query 16686:16686
# Open http://localhost:16686
```

### 7. Configure Logging

```bash
# Deploy Fluentd/Fluent Bit
kubectl apply -f infrastructure/kubernetes/fluentd/

# Verify logging
kubectl get pods -n logging
```

## Verification

Run the monitoring verification script:

```bash
./scripts/verify-monitoring.sh production
```

This script checks:
- Prometheus deployment and scraping
- Grafana deployment and dashboards
- Alertmanager deployment
- Alert rules configuration
- Service metrics endpoints
- Logging configuration
- Tracing configuration

## Key Metrics to Monitor

### Service Metrics

- **Request Rate**: `http_requests_total`
- **Response Time**: `http_request_duration_seconds`
- **Error Rate**: `http_requests_total{status=~"5.."}`
- **Active Connections**: `http_connections_active`

### Infrastructure Metrics

- **CPU Usage**: `container_cpu_usage_seconds_total`
- **Memory Usage**: `container_memory_usage_bytes`
- **Disk Usage**: `container_fs_usage_bytes`
- **Network Traffic**: `container_network_receive_bytes_total`

### Database Metrics

- **Connection Pool**: `db_connections_active`
- **Query Time**: `db_query_duration_seconds`
- **Query Rate**: `db_queries_total`
- **Error Rate**: `db_errors_total`

### Cache Metrics

- **Cache Hit Rate**: `cache_hits_total / cache_requests_total`
- **Cache Size**: `cache_size_bytes`
- **Evictions**: `cache_evictions_total`

## Alert Configuration

### Critical Alerts

- Service down (no replicas ready)
- High error rate (> 5%)
- High latency (p95 > 1s)
- Database connection failures
- High memory usage (> 90%)
- High CPU usage (> 80%)

### Warning Alerts

- Elevated error rate (> 1%)
- Elevated latency (p95 > 500ms)
- Low cache hit rate (< 70%)
- Disk usage > 80%

### Alert Channels

Configure alert channels in Alertmanager:
- **PagerDuty**: Critical alerts
- **Slack**: Warnings and notifications
- **Email**: Summary reports

## Dashboard Overview

### Services Overview Dashboard

- Service health status
- Request rates and latency
- Error rates
- Resource utilization

### Business Metrics Dashboard

- User registrations
- Network creations
- Workflow executions
- API usage trends

### Infrastructure Dashboard

- Cluster resource usage
- Node health
- Pod distribution
- Network traffic

## Troubleshooting

### Prometheus Not Scraping

1. Check service discovery:
   ```bash
   kubectl exec -n monitoring deployment/prometheus -- wget -qO- http://localhost:9090/api/v1/targets
   ```

2. Check service annotations:
   ```yaml
   annotations:
     prometheus.io/scrape: "true"
     prometheus.io/port: "8000"
     prometheus.io/path: "/metrics"
   ```

### Grafana Dashboards Not Loading

1. Verify data source connection
2. Check dashboard JSON syntax
3. Verify metrics are available in Prometheus

### Alerts Not Firing

1. Check alert rules syntax
2. Verify Alertmanager configuration
3. Check notification channels
4. Test alert with `kubectl exec` in Alertmanager pod

## Best Practices

1. **Regular Review**
   - Review dashboards daily
   - Review alerts weekly
   - Optimize alert thresholds monthly

2. **Documentation**
   - Document all custom alerts
   - Maintain runbook for each alert
   - Update dashboards as needed

3. **Testing**
   - Test alert channels regularly
   - Verify alert thresholds
   - Test incident response procedures

4. **Optimization**
   - Reduce alert noise
   - Optimize query performance
   - Archive old metrics

## Maintenance

### Backup Configuration

```bash
# Backup Prometheus configuration
kubectl get configmap prometheus-config -n monitoring -o yaml > prometheus-config-backup.yaml

# Backup Grafana dashboards
# Export from Grafana UI or use API
```

### Updates

- Review Prometheus retention policy
- Update Grafana dashboards as needed
- Review and update alert thresholds
- Keep monitoring stack updated

---

**Last Updated**: 2025-12-16

