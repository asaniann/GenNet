# GenNet Platform - Quick Deployment Guide

## 🚀 One-Command Deployment

### Local (Development) - Docker Only

**If you don't have python3-venv installed or want Docker-only deployment:**

```bash
SKIP_VENV=true ./scripts/deploy.sh local
```

This will:
- ✅ Use Docker for everything (no local Python venv needed)
- ✅ Build and start all services in containers
- ✅ Skip Python dependency installation locally

### Local (Development) - Full Setup

**If you have python3-venv installed:**

```bash
./scripts/deploy.sh local
```

This will:
- ✅ Create Python virtual environment
- ✅ Install Python dependencies
- ✅ Build Docker images
- ✅ Start all services

**Note:** If you get an error about `python3-venv`, either:
1. Install it: `sudo apt install python3.12-venv` (then run without SKIP_VENV)
2. Or use Docker-only: `SKIP_VENV=true ./scripts/deploy.sh local`

### Production

```bash
# 1. Configure Terraform (first time only)
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your AWS credentials

# 2. Deploy
cd ../..
./scripts/deploy.sh production prod
```

## 📋 What Gets Deployed

### Local Mode (Docker)
- PostgreSQL database
- Redis cache
- Neo4j graph database
- InfluxDB time-series DB
- All microservices (via Docker Compose)

### Production Mode
- Complete AWS infrastructure (VPC, EKS, RDS, Neptune, S3)
- All services deployed to Kubernetes
- Load balancers and networking
- Monitoring and logging

## 🔍 Verify Deployment

### Local
```bash
# Check services
docker-compose ps

# Test API
curl http://localhost:8000/api/v1/auth/health
```

### Production
```bash
# Check deployments
kubectl get deployments -n gennet-system

# Check pods
kubectl get pods -n gennet-system
```

## 🛑 Stop Services

### Local
```bash
./scripts/undeploy.sh local
# Or
docker-compose down
```

### Production
```bash
./scripts/undeploy.sh production
```

## 🆘 Troubleshooting

### "python3-venv not available" Error

**Option 1: Install python3-venv (Recommended if you need Python tools)**
```bash
sudo apt update
sudo apt install python3.12-venv
./scripts/deploy.sh local
```

**Option 2: Skip venv (Docker-only deployment)**
```bash
SKIP_VENV=true ./scripts/deploy.sh local
```

### Docker Issues

```bash
# Check Docker is running
docker info

# If not, start Docker
sudo systemctl start docker  # Linux
# Or start Docker Desktop on macOS/Windows
```

### Port Conflicts

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Stop conflicting service or change port in docker-compose.yml
```

### Services Won't Start

```bash
# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### Need More Help?

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed troubleshooting or [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) for complete documentation.

## ⚙️ Advanced Options

```bash
# Deploy with tests (requires venv)
RUN_TESTS=true ./scripts/deploy.sh local

# Skip Docker build (use existing images)
SKIP_BUILD=true ./scripts/deploy.sh local

# Docker-only (skip Python venv)
SKIP_VENV=true ./scripts/deploy.sh local

# Show help
./scripts/deploy.sh --help
```

## 💡 Common Workflows

### First Time Setup
```bash
# Docker-only (easiest)
SKIP_VENV=true ./scripts/deploy.sh local
```

### Development with Python Tools
```bash
# Install python3-venv first
sudo apt install python3.12-venv

# Full deployment
./scripts/deploy.sh local
```

### Quick Restart
```bash
docker-compose restart
```

### Clean Start
```bash
docker-compose down -v
SKIP_VENV=true ./scripts/deploy.sh local
```
