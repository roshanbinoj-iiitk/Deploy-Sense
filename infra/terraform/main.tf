# DeploySense — Terraform Infrastructure (Phase 3)
#
# WHY TERRAFORM (not Pulumi, CloudFormation):
#   1. Cloud-agnostic: Works with AWS, GCP, Azure
#   2. Industry standard: Most platform teams use Terraform
#   3. Declarative: Desired state, not imperative scripts
#   4. State management: Tracks what's deployed
#
# ARCHITECTURE:
#   This module provisions the core infrastructure for DeploySense:
#     - EKS Cluster (Kubernetes)
#     - RDS PostgreSQL (managed database)
#     - ElastiCache Redis (managed cache)
#     - VPC + Subnets (networking)
#
# USAGE:
#   cd infra/terraform
#   terraform init
#   terraform plan -var-file="environments/production.tfvars"
#   terraform apply -var-file="environments/production.tfvars"

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Remote state — required for team collaboration
  # S3 backend prevents state file conflicts
  backend "s3" {
    bucket         = "deploysense-terraform-state"
    key            = "deploysense/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "deploysense-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "deploysense"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
