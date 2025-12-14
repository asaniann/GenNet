variable "cluster_identifier" {
  description = "Neptune cluster identifier"
  type        = string
}

variable "engine_version" {
  description = "Neptune engine version"
  type        = string
}

variable "instance_class" {
  description = "Neptune instance class"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

