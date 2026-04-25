output "bedrock_invoke_policy_arn" {
  description = "ARN of the IAM policy granting Bedrock InvokeModel for the chosen Claude models"
  value       = aws_iam_policy.bedrock_invoke.arn
}

output "bedrock_haiku_model_id" {
  description = "Inference profile ID for Claude Haiku 4.5 (row tagging)"
  value       = var.bedrock_haiku_model_id
}

output "bedrock_sonnet_model_id" {
  description = "Inference profile ID for Claude Sonnet 4.5 (briefs / refine)"
  value       = var.bedrock_sonnet_model_id
}

output "aws_account_id" {
  value = data.aws_caller_identity.current.account_id
}
