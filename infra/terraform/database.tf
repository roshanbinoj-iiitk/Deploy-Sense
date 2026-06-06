# DeploySense — Database Module (RDS PostgreSQL)
#
# WHY MANAGED RDS (not self-hosted):
#   - Automated backups (daily, 7-day retention)
#   - Point-in-time recovery
#   - Multi-AZ failover (production)
#   - Automatic minor version upgrades
#   - No operational burden
#
# BACKUP STRATEGY:
#   - Automated: Daily snapshots, 7-day retention
#   - Manual: Monthly manual snapshots, 90-day retention
#   - Point-in-time: Continuous WAL archiving, recover to any second
#
# TRADEOFF:
#   RDS costs more than self-hosted PostgreSQL, but the operational
#   savings (no backup scripts, no failover management, no patching)
#   easily justify the cost for a small team.

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${var.project_name}-db-subnet"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  vpc_id      = aws_vpc.main.id

  # Allow PostgreSQL from EKS nodes only
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
    description     = "PostgreSQL from EKS nodes"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-postgres"

  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2  # Auto-scaling

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Backup
  backup_retention_period = 7
  backup_window           = "03:00-04:00"  # UTC
  maintenance_window      = "sun:04:00-sun:05:00"

  # High Availability
  multi_az = var.environment == "production"

  # Security
  storage_encrypted = true
  deletion_protection = var.environment == "production"

  # Performance
  performance_insights_enabled = true

  # Auto-upgrade minor versions
  auto_minor_version_upgrade = true

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = "${var.project_name}-final-snapshot"

  tags = {
    Name = "${var.project_name}-postgres"
  }
}
