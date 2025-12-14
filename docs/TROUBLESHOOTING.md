# Troubleshooting Guide

## Common Issues and Solutions

### Virtual Environment Issues

#### Error: "Failed to activate virtual environment"

**Problem:** The virtual environment is corrupted or missing the activate script.

**Solution:**
```bash
# Remove corrupted venv
./scripts/clean_venv.sh
# Or manually:
rm -rf venv

# Run deployment again
./scripts/deploy.sh local
```

#### Error: "ensurepip is not available" or "python3-venv not found"

**Problem:** The `python3-venv` package is not installed on your system.

**Solution:**

On Debian/Ubuntu:
```bash
sudo apt update
sudo apt install python3-venv
```

On RHEL/CentOS/Fedora:
```bash
sudo yum install python3-venv
# Or on newer versions:
sudo dnf install python3-venv
```

On macOS (with Homebrew):
```bash
# Usually pre-installed, but if needed:
brew install python3
```

After installing, recreate the virtual environment:
```bash
./scripts/clean_venv.sh
./scripts/deploy.sh local
```

### Docker Issues

#### Error: "Docker daemon is not running"

**Problem:** Docker service is not started.

**Solution:**

On Linux:
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Enable on boot
```

On macOS/Windows:
- Start Docker Desktop application

Verify:
```bash
docker info
```

#### Error: "Permission denied" when running Docker

**Problem:** Your user is not in the docker group.

**Solution:**

On Linux:
```bash
sudo usermod -aG docker $USER
# Log out and log back in, or run:
newgrp docker
```

#### Error: "Port already in use"

**Problem:** Another service is using a required port.

**Solution:**

Check what's using the port:
```bash
# For port 8000
sudo lsof -i :8000
# Or
sudo netstat -tuln | grep 8000
```

Options:
1. Stop the conflicting service
2. Change the port in `docker-compose.yml`
3. Kill the process: `sudo kill -9 <PID>`

### Python Dependencies Issues

#### Error: "Failed to install dependencies"

**Problem:** Package installation fails, often due to missing system libraries.

**Solution:**

Install system dependencies:

On Debian/Ubuntu:
```bash
sudo apt update
sudo apt install build-essential python3-dev libpq-dev
```

On RHEL/CentOS:
```bash
sudo yum groupinstall "Development Tools"
sudo yum install python3-devel postgresql-devel
```

For specific services:
- **PostgreSQL**: Install `libpq-dev` (Debian) or `postgresql-devel` (RHEL)
- **Neo4j**: Usually handled via Docker, no system dependencies needed
- **Redis**: Usually handled via Docker

#### Error: "ModuleNotFoundError" when running services

**Problem:** Dependencies not installed or wrong virtual environment.

**Solution:**

```bash
# Activate venv
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements-dev.txt
find services -name "requirements.txt" -exec pip install -r {} \;
```

### Terraform Issues

#### Error: "AWS credentials not found"

**Problem:** AWS CLI not configured.

**Solution:**

```bash
# Configure AWS credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1

# Verify
aws sts get-caller-identity
```

#### Error: "Terraform state lock"

**Problem:** Another process is using Terraform state.

**Solution:**

```bash
cd infrastructure/terraform

# Check for lock file
ls -la .terraform.tfstate.lock.info

# If stuck, force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Kubernetes Issues

#### Error: "kubectl: command not found"

**Problem:** kubectl not installed.

**Solution:**

Install kubectl:
```bash
# On Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# On macOS
brew install kubectl
```

#### Error: "Unable to connect to the server"

**Problem:** kubectl context not configured or cluster not accessible.

**Solution:**

```bash
# Check current context
kubectl config current-context

# List available contexts
kubectl config get-contexts

# Switch context
kubectl config use-context <context-name>

# For EKS, update kubeconfig
aws eks update-kubeconfig --name <cluster-name> --region <region>
```

#### Error: "ImagePullBackOff" or "ErrImagePull"

**Problem:** Docker image cannot be pulled.

**Solution:**

1. Check if image exists locally:
```bash
docker images | grep gennet
```

2. Build images locally:
```bash
./scripts/deploy.sh local  # This builds images
```

3. For production, ensure images are pushed to registry:
```bash
docker tag gennet/service:latest registry/gennet/service:latest
docker push registry/gennet/service:latest
```

### Service Health Issues

#### Service health check failing

**Problem:** Service not responding to health checks.

**Solution:**

Check service logs:
```bash
# Local
docker-compose logs -f <service-name>

# Production
kubectl logs -f deployment/<service-name> -n gennet-system
```

Common causes:
- Database connection issues
- Missing environment variables
- Port conflicts
- Missing dependencies

#### Database connection errors

**Problem:** Services can't connect to database.

**Solution:**

1. Verify database is running:
```bash
# Local
docker-compose ps postgres

# Production
kubectl get pods -n gennet-system | grep postgres
```

2. Check connection string:
```bash
# Should match docker-compose.yml or Kubernetes config
echo $DATABASE_URL
```

3. Test connection:
```bash
# Local
docker-compose exec postgres psql -U gennet -d gennet -c "SELECT 1;"
```

### Network/Connectivity Issues

#### Services can't reach each other

**Problem:** Network configuration or service discovery issues.

**Solution:**

**Local (Docker Compose):**
- Services should use service names as hostnames
- Check `docker-compose.yml` network configuration
- Verify all services are on same network

**Production (Kubernetes):**
- Use Kubernetes service names
- Check service DNS: `nslookup <service-name>.gennet-system.svc.cluster.local`
- Verify service endpoints: `kubectl get endpoints -n gennet-system`

## Getting Help

### Collect Information

Before asking for help, collect:

1. **System Information:**
```bash
./scripts/validate_setup.sh
```

2. **Service Status:**
```bash
# Local
docker-compose ps
docker-compose logs

# Production
kubectl get all -n gennet-system
kubectl logs -l app=gennet -n gennet-system
```

3. **Error Messages:**
- Full error output
- Relevant log lines
- Steps to reproduce

### Debug Mode

Run with verbose output:
```bash
# Enable bash debugging
bash -x ./scripts/deploy.sh local

# Enable Docker debug
export DOCKER_BUILDKIT=0
export COMPOSE_DOCKER_CLI_BUILD=0
```

### Logs Location

**Local:**
- Docker logs: `docker-compose logs`
- Application logs: In containers

**Production:**
- Kubernetes logs: `kubectl logs`
- CloudWatch (AWS): Check log groups
- Application logs: In pod logs

## Quick Fixes

### Reset Everything (Local)

```bash
# Stop and remove everything
docker-compose down -v
rm -rf venv
./scripts/clean_venv.sh

# Clean Docker
docker system prune -a

# Start fresh
./scripts/deploy.sh local
```

### Common Commands

```bash
# Check what's running
docker-compose ps
kubectl get pods -n gennet-system

# View logs
docker-compose logs -f [service]
kubectl logs -f deployment/[service] -n gennet-system

# Restart service
docker-compose restart [service]
kubectl rollout restart deployment/[service] -n gennet-system

# Check resources
docker stats
kubectl top pods -n gennet-system
```

## Prevention

1. **Keep dependencies updated:**
```bash
pip list --outdated
npm outdated
```

2. **Regular validation:**
```bash
./scripts/validate_setup.sh
```

3. **Test before production:**
- Always test locally first
- Use staging environment
- Review Terraform plans

4. **Monitor resources:**
- Check disk space
- Monitor memory usage
- Watch for port conflicts

