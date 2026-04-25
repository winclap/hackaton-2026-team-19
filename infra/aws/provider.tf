terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5"
    }
  }
}

provider "aws" {
  profile = var.aws_profile
  region  = var.aws_region

  default_tags {
    tags = {
      Project   = "hackaton-2026"
      Group     = "grupo-19"
      ManagedBy = "terraform"
      Owner     = "luca.gelmini@winclap.com"
    }
  }
}
