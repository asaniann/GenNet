resource "aws_db_subnet_group" "main" {
  name       = "${var.name}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = var.tags
}

resource "aws_security_group" "rds" {
  name        = "${var.name}-sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_db_instance" "main" {
  identifier             = var.name
  engine                 = "postgres"
  engine_version         = var.engine_version
  instance_class         = var.instance_class
  allocated_storage      = 100
  storage_type           = "gp3"
  storage_encrypted      = true
  kms_key_id             = var.kms_key_id
  copy_tags_to_snapshot  = true
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  deletion_protection   = var.environment == "prod"
  multi_az               = var.environment == "prod"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  backup_retention_period = var.environment == "prod" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  
  # Point-in-time recovery
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  
  # Automated backups
  skip_final_snapshot = var.environment == "dev"
  final_snapshot_identifier = var.environment != "dev" ? "${var.name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Read replicas for HA
  replicate_source_db = var.environment == "prod" ? null : null  # Can be configured for read replicas
  
  # Monitoring
  monitoring_interval = var.environment == "prod" ? 60 : 0
  monitoring_role_arn = var.environment == "prod" ? aws_iam_role.rds_monitoring[0].arn : null
  
  # Performance Insights
  performance_insights_enabled = var.environment == "prod"
  performance_insights_retention_period = var.environment == "prod" ? 7 : null
  
  # Enhanced monitoring
  auto_minor_version_upgrade = true
  allow_major_version_upgrade = false
  
  tags = merge(var.tags, {
    Backup = "enabled"
    Monitoring = "enabled"
  })
}

# Read replica for HA (production)
resource "aws_db_instance" "replica" {
  count = var.environment == "prod" ? 1 : 0
  
  identifier             = "${var.name}-replica"
  replicate_source_db    = aws_db_instance.main.identifier
  instance_class         = var.instance_class
  publicly_accessible    = false
  storage_encrypted      = true
  kms_key_id             = var.kms_key_id
  copy_tags_to_snapshot  = true
  
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  skip_final_snapshot = true
  
  tags = merge(var.tags, {
    Type = "replica"
  })
}

# IAM role for RDS monitoring
resource "aws_iam_role" "rds_monitoring" {
  count = var.environment == "prod" ? 1 : 0
  
  name = "${var.name}-rds-monitoring-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count = var.environment == "prod" ? 1 : 0
  
  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

