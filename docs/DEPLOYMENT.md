# GenNet Cloud Platform - Deployment Guide

## Prerequisites

- AWS Account with appropriate permissions
- Terraform >= 1.5.0
- kubectl configured for EKS
- Docker
- Node.js 20+ (for frontend)

## Infrastructure Deployment

### 1. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

### 2. Configure Variables

Create `terraform.tfvars`:

```hcl
project_name = "gennet"
environment = "dev"
aws_region = "us-east-1"
db_username = "admin"
db_password = "your-secure-password"
```

### 3. Deploy Infrastructure

```bash
terraform plan
terraform apply
```

This will create:
- VPC with subnets
- EKS cluster
- RDS PostgreSQL instance
- Neptune graph database
- S3 buckets
- ElastiCache Redis
- Security groups and IAM roles

### 4. Configure kubectl

```bash
aws eks update-kubeconfig --name gennet-eks --region us-east-1
```

## Application Deployment

### 1. Build Docker Images

```bash
# Build all services
cd services
for service in */; do
    docker build -t gennet/${service%/}:latest ./${service}
done
```

### 2. Deploy to Kubernetes

```bash
# Create namespaces
kubectl apply -f infrastructure/kubernetes/namespaces.yaml

# Deploy services (using Helm charts or kubectl)
# Each service should have its own deployment manifest
```

### 3. Configure Secrets

```bash
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=your-password \
  --namespace=gennet-system
```

## Local Development

### Start Development Environment

```bash
# Start local services (Postgres, Redis, Neo4j, InfluxDB)
make dev-up

# Run services locally
cd services/auth-service
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend/web
npm install
npm run dev
```

## Monitoring

Prometheus and Grafana are configured for monitoring:

- Metrics endpoint: `http://prometheus:9090`
- Grafana dashboard: `http://grafana:3000`

## Backup and Recovery

Automated backups run daily via CronJob:

```bash
kubectl get cronjobs -n gennet-system
```

Manual backup:

```bash
kubectl create job --from=cronjob/gennet-backup manual-backup -n gennet-system
```

