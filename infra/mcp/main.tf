# Copyright 2026 by GuidoGerb Publishing, LLC
#
# Terraform configuration for MCP server deployment on AWS.
# Stack: API Gateway (HTTP API v2) + Lambda (Python 3.12)

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "ggp3d-terraform-state"
    key            = "mcp/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "ggp3d-terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "ggp3d"
      Component   = "mcp-server"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
