# Encryption Module
# Configures encryption at rest and in transit

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "kms_key_alias" {
  description = "KMS key alias for encryption"
  type        = string
  default     = "gennet-encryption-key"
}

variable "enable_key_rotation" {
  description = "Enable automatic key rotation"
  type        = bool
  default     = true
}

variable "key_deletion_window" {
  description = "Key deletion window in days"
  type        = number
  default     = 30
}

# KMS Key for encryption
resource "aws_kms_key" "main" {
  description             = "GenNet encryption key"
  deletion_window_in_days = var.key_deletion_window
  enable_key_rotation     = var.enable_key_rotation
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow service access"
        Effect = "Allow"
        Principal = {
          Service = [
            "rds.amazonaws.com",
            "s3.amazonaws.com",
            "secretsmanager.amazonaws.com"
          ]
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
  
  tags = {
    Name = var.kms_key_alias
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.kms_key_alias}"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_caller_identity" "current" {}

# Outputs
output "kms_key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.main.id
  sensitive   = true
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.main.arn
}

output "kms_key_alias" {
  description = "KMS key alias"
  value       = aws_kms_alias.main.name
}

