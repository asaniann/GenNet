#!/bin/bash
# Script to create Kubernetes secrets for GenNet platform

set -e

NAMESPACE="${1:-gennet-system}"

echo "Creating Kubernetes secrets for namespace: $NAMESPACE"

# Check if namespace exists
if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "Creating namespace $NAMESPACE..."
    kubectl create namespace "$NAMESPACE"
fi

# Database credentials
echo "Creating database credentials secret..."
read -sp "Enter database URL: " DB_URL
echo
kubectl create secret generic db-credentials \
    --from-literal=url="$DB_URL" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

# Application secrets
echo "Creating application secrets..."
read -sp "Enter JWT secret key: " JWT_SECRET
echo
read -sp "Enter encryption key: " ENCRYPTION_KEY
echo
kubectl create secret generic app-secrets \
    --from-literal=jwt_secret="$JWT_SECRET" \
    --from-literal=encryption_key="$ENCRYPTION_KEY" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

# Neo4j credentials
echo "Creating Neo4j credentials..."
read -p "Enter Neo4j user [neo4j]: " NEO4J_USER
NEO4J_USER=${NEO4J_USER:-neo4j}
read -sp "Enter Neo4j password: " NEO4J_PASSWORD
echo
kubectl create secret generic neo4j-credentials \
    --from-literal=user="$NEO4J_USER" \
    --from-literal=password="$NEO4J_PASSWORD" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

# AWS credentials
echo "Creating AWS credentials..."
read -p "Enter AWS Access Key ID: " AWS_KEY
read -sp "Enter AWS Secret Access Key: " AWS_SECRET
echo
kubectl create secret generic aws-credentials \
    --from-literal=access_key_id="$AWS_KEY" \
    --from-literal=secret_access_key="$AWS_SECRET" \
    --namespace="$NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets created successfully!"
echo "Verify with: kubectl get secrets -n $NAMESPACE"

