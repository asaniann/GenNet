terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  backend "s3" {
    bucket = "gennet-terraform-state"
    key    = "gennet-platform/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = [
      "eks",
      "get-token",
      "--cluster-name",
      module.eks.cluster_name
    ]
  }
}

module "vpc" {
  source = "./modules/vpc"
  
  name                 = "${var.project_name}-vpc"
  cidr                 = var.vpc_cidr
  azs                  = var.availability_zones
  private_subnets      = var.private_subnets
  public_subnets       = var.public_subnets
  enable_nat_gateway   = true
  single_nat_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
}

module "eks" {
  source = "./modules/eks"
  
  cluster_name    = "${var.project_name}-eks"
  cluster_version = "1.28"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets
  
  node_groups = {
    general = {
      desired_size = 3
      max_size     = 10
      min_size     = 1
      instance_types = ["t3.medium"]
    }
    compute = {
      desired_size = 2
      max_size     = 20
      min_size     = 0
      instance_types = ["c5.2xlarge"]
    }
    gpu = {
      desired_size = 0
      max_size     = 10
      min_size     = 0
      instance_types = ["g4dn.xlarge"]
      gpu_enabled  = true
    }
  }
}

module "rds" {
  source = "./modules/rds"
  
  name           = "${var.project_name}-postgres"
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnets
  instance_class = var.rds_instance_class
  engine_version = "15.4"
  db_name        = "gennet"
  db_username    = var.db_username
  db_password    = var.db_password
}

module "neptune" {
  source = "./modules/neptune"
  
  cluster_identifier = "${var.project_name}-neptune"
  engine_version     = "1.2.0.2"
  instance_class     = var.neptune_instance_class
  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnets
}

module "s3" {
  source = "./modules/s3"
  
  bucket_name        = "${var.project_name}-data-${var.environment}"
  versioning_enabled = true
  lifecycle_rules = [
    {
      id     = "transition-to-glacier"
      status = "Enabled"
      transitions = [
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
    }
  ]
}

module "redis" {
  source = "./modules/redis"
  
  cluster_id         = "${var.project_name}-redis"
  node_type          = var.redis_node_type
  num_cache_nodes    = 1
  subnet_ids         = module.vpc.private_subnets
  vpc_id             = module.vpc.vpc_id
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = "gennet-terraform-state-${var.environment}"
  
  versioning {
    enabled = true
  }
  
  lifecycle {
    prevent_destroy = true
  }
}

