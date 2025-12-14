resource "aws_neptune_subnet_group" "main" {
  name       = "${var.cluster_identifier}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = var.tags
}

resource "aws_security_group" "neptune" {
  name        = "${var.cluster_identifier}-sg"
  description = "Security group for Neptune"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8182
    to_port     = 8182
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

resource "aws_neptune_cluster" "main" {
  cluster_identifier                  = var.cluster_identifier
  engine                              = "neptune"
  engine_version                      = var.engine_version
  neptune_subnet_group_name           = aws_neptune_subnet_group.main.name
  vpc_security_group_ids              = [aws_security_group.neptune.id]
  skip_final_snapshot                 = var.environment == "dev"
  final_snapshot_identifier           = var.environment != "dev" ? "${var.cluster_identifier}-final-snapshot" : null
  backup_retention_period             = 7
  preferred_backup_window             = "03:00-04:00"
  preferred_maintenance_window        = "mon:04:00-mon:05:00"
  iam_database_authentication_enabled = true

  tags = var.tags
}

resource "aws_neptune_cluster_instance" "main" {
  count              = 1
  identifier         = "${var.cluster_identifier}-${count.index + 1}"
  cluster_identifier = aws_neptune_cluster.main.id
  engine             = "neptune"
  instance_class     = var.instance_class

  tags = var.tags
}

