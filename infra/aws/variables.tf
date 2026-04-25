variable "aws_profile" {
  description = "AWS named profile to use (SSO)"
  type        = string
  default     = "sandbox"
}

variable "aws_region" {
  description = "AWS region for Bedrock invocations"
  type        = string
  default     = "us-east-1"
}

variable "bedrock_haiku_model_id" {
  description = "Bedrock cross-region inference profile for Claude Haiku 4.5 (used for row tagging)"
  type        = string
  default     = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
}

variable "bedrock_sonnet_model_id" {
  description = "Bedrock cross-region inference profile for Claude Sonnet 4.5 (used for briefs/refine)"
  type        = string
  default     = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
}
