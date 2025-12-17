# Multi-Region Infrastructure Module
# Supports deployment across multiple AWS regions

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "regions" {
  description = "List of AWS regions to deploy to"
  type        = list(string)
  default     = ["us-east-1", "eu-west-1", "ap-southeast-1"]
}

variable "primary_region" {
  description = "Primary region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "vpc_cidr_base" {
  description = "Base CIDR block for VPCs"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_cross_region_peering" {
  description = "Enable VPC peering between regions"
  type        = bool
  default     = true
}

variable "enable_transit_gateway" {
  description = "Enable AWS Transit Gateway for cross-region connectivity"
  type        = bool
  default     = true
}

# Data sources for regions
data "aws_region" "current" {
  provider = aws.primary
}

# Transit Gateway for cross-region connectivity
resource "aws_ec2_transit_gateway" "main" {
  count = var.enable_transit_gateway ? 1 : 0
  
  description                     = "GenNet Transit Gateway for multi-region connectivity"
  default_route_table_association = "enable"
  default_route_table_propagation = "enable"
  
  tags = {
    Name        = "${var.project_name}-tgw"
    Environment = "production"
  }
}

# Outputs
output "transit_gateway_id" {
  description = "Transit Gateway ID"
  value       = var.enable_transit_gateway ? aws_ec2_transit_gateway.main[0].id : null
}

output "regions" {
  description = "List of regions"
  value       = var.regions
}

output "primary_region" {
  description = "Primary region"
  value       = var.primary_region
}

