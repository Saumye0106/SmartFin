variable "region" {
  description = "AWS region for everything."
  type        = string
  default     = "ap-south-1"
}

variable "aws_profile" {
  description = "AWS CLI profile to use (aws configure --profile smartfin). Null uses the default credentials."
  type        = string
  default     = null
}

variable "name" {
  description = "Prefix for resource names."
  type        = string
  default     = "smartfin"
}

variable "admin_cidr" {
  description = "Your public IP as a /32 (for example 203.0.113.7/32). Only this address may reach SSH (22) and the Kubernetes API (6443)."
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0)) && var.admin_cidr != "0.0.0.0/0"
    error_message = "admin_cidr must be a CIDR such as 203.0.113.7/32, and must not be 0.0.0.0/0."
  }
}

variable "ssh_public_key" {
  description = "Contents of the SSH public key allowed to log in to the server (for example the text of ~/.ssh/smartfin.pub)."
  type        = string

  validation {
    condition     = can(regex("^(ssh-ed25519|ssh-rsa|ecdsa-sha2-)", var.ssh_public_key))
    error_message = "ssh_public_key must be the contents of a public key file (it starts with ssh-ed25519, ssh-rsa or ecdsa-sha2-)."
  }
}

variable "instance_type" {
  description = "EC2 size for the k3s node. t3.small (2 GB) is the minimum that fits k3s plus two backend copies; t3.medium (4 GB) is comfortable."
  type        = string
  default     = "t3.small"
}

variable "root_volume_gb" {
  description = "Disk for the node. The backend image alone is about 1 GB."
  type        = number
  default     = 30
}

variable "db_instance_class" {
  description = "RDS size."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_engine_version" {
  description = "PostgreSQL major version on RDS (the same major version the app is tested against)."
  type        = string
  default     = "17"
}

variable "db_allocated_storage_gb" {
  type    = number
  default = 20
}

variable "db_backup_retention_days" {
  description = "Days of automated RDS backups (point-in-time restore)."
  type        = number
  default     = 7
}

variable "db_deletion_protection" {
  description = "Refuse to delete the database from Terraform. Turn on once it holds data you care about."
  type        = bool
  default     = false
}

variable "db_skip_final_snapshot" {
  description = "On destroy, skip the final snapshot. True makes teardown clean for a practice deployment; false keeps a last backup."
  type        = bool
  default     = true
}

variable "enable_bedrock" {
  description = "Let the node call Amazon Bedrock (chat assistant and AI guidance) through its IAM role."
  type        = bool
  default     = true
}
