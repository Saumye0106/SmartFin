# PostgreSQL on RDS, in the private subnets, reachable only from the k3s node.

resource "aws_db_subnet_group" "main" {
  name       = var.name
  subnet_ids = aws_subnet.private[*].id
}

resource "random_password" "db" {
  length = 32
  # RDS forbids / @ " and space in the master password; the rest must survive inside a URL.
  special          = true
  override_special = "-_"
}

resource "aws_db_instance" "main" {
  identifier = var.name

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage_gb
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = "smartfin"
  username = "smartfin"
  password = random_password.db.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]
  publicly_accessible    = false
  multi_az               = false

  backup_retention_period    = var.db_backup_retention_days
  auto_minor_version_upgrade = true
  deletion_protection        = var.db_deletion_protection
  skip_final_snapshot        = var.db_skip_final_snapshot
  final_snapshot_identifier  = var.db_skip_final_snapshot ? null : "${var.name}-final"
  apply_immediately          = true
}

# ── Secrets the app needs, in SSM Parameter Store (encrypted, free) ──────────
# Ansible reads these on the node and turns them into a Kubernetes Secret, so they never
# pass through the repository or a laptop.

resource "random_password" "jwt_secret" {
  length  = 64
  special = false
}

resource "aws_ssm_parameter" "database_url" {
  name  = "/${var.name}/database_url"
  type  = "SecureString"
  value = "postgresql://${aws_db_instance.main.username}:${random_password.db.result}@${aws_db_instance.main.endpoint}/${aws_db_instance.main.db_name}?sslmode=require"
}

resource "aws_ssm_parameter" "jwt_secret" {
  name  = "/${var.name}/jwt_secret_key"
  type  = "SecureString"
  value = random_password.jwt_secret.result
}
