# GenNet Platform - Deployment Guide

## Quick Start

### Local Deployment (Recommended for Development)

```bash
# Simple one-command deployment
./scripts/deploy.sh local
```

This will:
- Check prerequisites
- Install all dependencies
- Build Docker images
- Start all services with Docker Compose
- Validate deployment

### Production Deployment

```bash
# Deploy to production
./scripts/deploy.sh production prod
```

## Prerequisites

### For Local Deployment
- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (optional, for frontend development)

### For Production Deployment
- All local prerequisites plus:
- Terraform >= 1.5.0
- kubectl
- AWS CLI (configured with credentials)
- AWS account with appropriate permissions

## Deployment Modes

### 1. Local Deployment

Local deployment uses Docker Compose to run all services locally.

```bash
# Deploy locally
./scripts/deploy.sh local

# Check service status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop services
docker-compose down

# Stop and remove volumes
./scripts/undeploy.sh local
```

**Services will be available at:**
- Auth Service: http://localhost:8000/api/v1/auth
- GRN Service: http://localhost:8000/api/v1/networks
- Frontend: http://localhost:3000 (if built)

### 2. Production Deployment

Production deployment uses Terraform for infrastructure and Kubernetes for orchestration.

#### Step 1: Configure Terraform

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

#### Step 2: Configure AWS Credentials

```bash
aws configure
# Or set environment variables:
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

#### Step 3: Deploy

```bash
./scripts/deploy.sh production prod
```

The script will:
1. Initialize Terraform
2. Plan infrastructure changes
3. Ask for confirmation
4. Apply infrastructure
5. Deploy to Kubernetes

#### Step 4: Verify Deployment

```bash
# Check Kubernetes deployments
kubectl get deployments -n gennet-system

# Check pods
kubectl get pods -n gennet-system

# View logs
kubectl logs -f deployment/auth-service -n gennet-system
```

## Environment Variables

### Common Variables

- `RUN_TESTS`: Set to `true` to run tests after deployment
- `SKIP_BUILD`: Set to `true` to skip Docker image building
- `DOCKER_REGISTRY`: Docker registry URL for production

### Service-Specific Variables

See individual service directories for required environment variables.

Example for auth-service:
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/gennet
export REDIS_URL=redis://host:6379/0
export JWT_SECRET_KEY=your-secret-key
```

## Advanced Usage

### Deploy with Tests

```bash
RUN_TESTS=true ./scripts/deploy.sh local
```

### Deploy without Building Images

```bash
SKIP_BUILD=true ./scripts/deploy.sh local
```

### Custom Environment

```bash
./scripts/deploy.sh production staging
```

### Manual Steps

If you prefer manual deployment:

#### Local:
```bash
# Install dependencies
pip install -r requirements-dev.txt
pip install -r services/*/requirements.txt

# Start services
docker-compose up -d
```

#### Production:
```bash
# Infrastructure
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# Kubernetes
kubectl apply -f infrastructure/kubernetes/
```

## Troubleshooting

### Common Issues

#### 1. Docker daemon not running
```bash
# Start Docker
sudo systemctl start docker
# Or start Docker Desktop
```

#### 2. Port already in use
```bash
# Check what's using the port
sudo lsof -i :8000
# Kill the process or change port in docker-compose.yml
```

#### 3. Terraform authentication errors
```bash
# Verify AWS credentials
aws sts get-caller-identity
# Reconfigure if needed
aws configure
```

#### 4. Kubernetes connection issues
```bash
# Check kubectl context
kubectl config current-context
# Switch context if needed
kubectl config use-context <context-name>
```

#### 5. Service health check failures
```bash
# Check service logs
docker-compose logs [service-name]
# Or for Kubernetes
kubectl logs -f deployment/[service-name] -n gennet-system
```

### Validation

Run validation script to check setup:
```bash
./scripts/validate_setup.sh
```

### Logs

#### Local:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth-service
```

#### Production:
```bash
# All pods
kubectl logs -f -l app=gennet -n gennet-system

# Specific deployment
kubectl logs -f deployment/auth-service -n gennet-system
```

## Undeployment

### Local
```bash
./scripts/undeploy.sh local
# Or
docker-compose down -v
```

### Production
```bash
./scripts/undeploy.sh production
# This will:
# - Remove Kubernetes resources
# - Ask for confirmation before destroying infrastructure
```

## Security Considerations

### Local Development
- Use strong passwords in docker-compose.yml
- Don't commit secrets to version control
- Use environment variables for sensitive data

### Production
- Store secrets in AWS Secrets Manager or Kubernetes secrets
- Use IAM roles instead of access keys when possible
- Enable encryption at rest and in transit
- Regular security updates
- Network security groups properly configured

## Monitoring

### Local
- Check Docker Compose logs
- Use Docker stats: `docker stats`
- Service health endpoints: `curl http://localhost:8000/api/v1/auth/health`

### Production
- Kubernetes dashboard
- Prometheus metrics
- CloudWatch logs (AWS)
- Application logs in centralized logging

## Backup and Recovery

### Database Backups
- Automated backups configured via Kubernetes CronJob
- Manual backup: See infrastructure/kubernetes/backup-job.yaml

### Infrastructure State
- Terraform state stored in S3 (configured in backend)
- Regular state backups recommended

## Rollback

### Local
```bash
docker-compose down
# Edit docker-compose.yml or code
docker-compose up -d
```

### Production
```bash
# Rollback Kubernetes deployment
kubectl rollout undo deployment/[service-name] -n gennet-system

# Rollback Terraform (if needed)
cd infrastructure/terraform
terraform plan -destroy
terraform apply -target=<resource>
```

## Next Steps

After deployment:
1. Verify all services are healthy
2. Run smoke tests
3. Check logs for errors
4. Monitor resource usage
5. Set up alerts (production)

For more details, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [API Documentation](API.md)
- [Testing Guide](TESTING.md)

