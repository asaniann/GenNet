# Automated Backup Module
# Handles backups for databases, S3, and Kubernetes state

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "backup_plan_name" {
  description = "Name of the backup plan"
  type        = string
  default     = "gennet-backup-plan"
}

variable "backup_vault_name" {
  description = "Name of the backup vault"
  type        = string
  default     = "gennet-backup-vault"
}

variable "retention_days" {
  description = "Backup retention in days"
  type        = number
  default     = 30
}

variable "backup_schedule" {
  description = "Backup schedule (cron expression)"
  type        = string
  default     = "cron(0 2 * * ? *)"  # Daily at 2 AM
}

variable "rds_instance_arns" {
  description = "List of RDS instance ARNs to backup"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs to backup"
  type        = list(string)
  default     = []
}

variable "efs_file_system_arns" {
  description = "List of EFS file system ARNs to backup"
  type        = list(string)
  default     = []
}

# Backup Vault
resource "aws_backup_vault" "main" {
  name        = var.backup_vault_name
  kms_key_arn = var.kms_key_arn
  
  tags = {
    Name = var.backup_vault_name
  }
}

# Backup Plan
resource "aws_backup_plan" "main" {
  name = var.backup_plan_name
  
  rule {
    rule_name         = "daily-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.backup_schedule
    
    lifecycle {
      cold_storage_after = 30
      delete_after       = var.retention_days
    }
    
    recovery_point_tags = {
      BackupPlan = var.backup_plan_name
    }
  }
  
  rule {
    rule_name         = "weekly-backup"
    target_vault_name = aws_backup_vault.main.name
    schedule          = "cron(0 3 ? * SUN *)"  # Weekly on Sunday at 3 AM
    
    lifecycle {
      cold_storage_after = 90
      delete_after       = 365
    }
    
    recovery_point_tags = {
      BackupPlan = var.backup_plan_name
      Type       = "weekly"
    }
  }
  
  tags = {
    Name = var.backup_plan_name
  }
}

# Backup Selection - RDS
resource "aws_backup_selection" "rds" {
  count = length(var.rds_instance_arns) > 0 ? 1 : 0
  
  name         = "${var.backup_plan_name}-rds"
  iam_role_arn = aws_iam_role.backup[0].arn
  plan_id      = aws_backup_plan.main.id
  
  resources = var.rds_instance_arns
  
  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Backup"
    value = "enabled"
  }
}

# Backup Selection - S3
resource "aws_backup_selection" "s3" {
  count = length(var.s3_bucket_arns) > 0 ? 1 : 0
  
  name         = "${var.backup_plan_name}-s3"
  iam_role_arn = aws_iam_role.backup[0].arn
  plan_id      = aws_backup_plan.main.id
  
  resources = var.s3_bucket_arns
}

# Backup Selection - EFS
resource "aws_backup_selection" "efs" {
  count = length(var.efs_file_system_arns) > 0 ? 1 : 0
  
  name         = "${var.backup_plan_name}-efs"
  iam_role_arn = aws_iam_role.backup[0].arn
  plan_id      = aws_backup_plan.main.id
  
  resources = var.efs_file_system_arns
}

# IAM Role for Backup
resource "aws_iam_role" "backup" {
  count = length(var.rds_instance_arns) + length(var.s3_bucket_arns) + length(var.efs_file_system_arns) > 0 ? 1 : 0
  
  name = "${var.backup_plan_name}-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  count = length(var.rds_instance_arns) + length(var.s3_bucket_arns) + length(var.efs_file_system_arns) > 0 ? 1 : 0
  
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "restore" {
  count = length(var.rds_instance_arns) + length(var.s3_bucket_arns) + length(var.efs_file_system_arns) > 0 ? 1 : 0
  
  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

variable "kms_key_arn" {
  description = "KMS key ARN for backup encryption"
  type        = string
  default     = ""
}

# Outputs
output "backup_plan_id" {
  description = "Backup plan ID"
  value       = aws_backup_plan.main.id
}

output "backup_vault_arn" {
  description = "Backup vault ARN"
  value       = aws_backup_vault.main.arn
}

