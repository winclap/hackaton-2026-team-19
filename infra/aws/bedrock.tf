data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id

  # Cross-region inference profiles invoke the underlying foundation models
  # in multiple regions, so the policy must allow both the inference profile
  # ARN and the foundation model ARNs across the inference regions.
  inference_regions = ["us-east-1", "us-east-2", "us-west-2"]

  haiku_underlying_id  = replace(var.bedrock_haiku_model_id, "us.", "")
  sonnet_underlying_id = replace(var.bedrock_sonnet_model_id, "us.", "")

  bedrock_resource_arns = concat(
    [
      "arn:aws:bedrock:${var.aws_region}:${local.account_id}:inference-profile/${var.bedrock_haiku_model_id}",
      "arn:aws:bedrock:${var.aws_region}:${local.account_id}:inference-profile/${var.bedrock_sonnet_model_id}",
    ],
    [for r in local.inference_regions : "arn:aws:bedrock:${r}::foundation-model/${local.haiku_underlying_id}"],
    [for r in local.inference_regions : "arn:aws:bedrock:${r}::foundation-model/${local.sonnet_underlying_id}"],
  )
}

data "aws_iam_policy_document" "bedrock_invoke" {
  statement {
    sid    = "InvokeClaudeOnBedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
    resources = local.bedrock_resource_arns
  }

  statement {
    sid    = "ListBedrockModels"
    effect = "Allow"
    actions = [
      "bedrock:ListFoundationModels",
      "bedrock:ListInferenceProfiles",
      "bedrock:GetFoundationModel",
      "bedrock:GetInferenceProfile",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "bedrock_invoke" {
  name        = "hackaton-2026-grupo-19-bedrock-invoke"
  description = "Allow invoking Claude Haiku 4.5 and Sonnet 4.5 on Bedrock for hackaton 2026 grupo 19"
  policy      = data.aws_iam_policy_document.bedrock_invoke.json

  tags = {
    Project = "hackaton-2026"
    Group   = "grupo-19"
  }
}
