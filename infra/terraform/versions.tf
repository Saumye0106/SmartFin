terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # State is kept in this folder (terraform.tfstate, git-ignored). It contains the database
  # password and the JWT secret in plain text: never commit or share it. To keep it in S3 instead,
  # create a private, versioned bucket once by hand and uncomment:
  #
  # backend "s3" {
  #   bucket       = "smartfin-tfstate-<your-account-id>"
  #   key          = "smartfin/terraform.tfstate"
  #   region       = "ap-south-1"
  #   encrypt      = true
  #   use_lockfile = true
  # }
}

provider "aws" {
  region  = var.region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project   = "smartfin"
      ManagedBy = "terraform"
    }
  }
}
