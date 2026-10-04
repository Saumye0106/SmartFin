# Automatic deploys from GitHub Actions, without storing any AWS key in GitHub.
#
# GitHub proves which repository and branch a workflow run belongs to with a short-lived token
# (OIDC). AWS exchanges that token for temporary credentials of the role below, which may do
# exactly two things: push images to the two ECR repositories, and run the fixed deploy command
# on the node. It cannot open a shell on the server or run any other command.

variable "github_repository" {
  description = "GitHub repository allowed to deploy, as owner/name. Empty turns automatic deploys off."
  type        = string
  default     = "Saumye0106/SmartFin"
}

variable "github_deploy_branch" {
  description = "Only workflow runs on this branch may deploy."
  type        = string
  default     = "main"
}

locals {
  github_deploy = var.github_repository != ""
}

resource "aws_iam_openid_connect_provider" "github" {
  count = local.github_deploy ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "assume_github" {
  count = local.github_deploy ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github[0].arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    # Pull requests and other branches get a different "sub" and are refused.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/${var.github_deploy_branch}"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  count = local.github_deploy ? 1 : 0

  name                 = "${var.name}-github-deploy"
  assume_role_policy   = data.aws_iam_policy_document.assume_github[0].json
  max_session_duration = 3600
}

# The one command GitHub may run on the node. The tag is checked here and again by the script.
resource "aws_ssm_document" "deploy" {
  count = local.github_deploy ? 1 : 0

  name            = "${var.name}-deploy"
  document_type   = "Command"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "2.2"
    description   = "Roll SmartFin to an image tag that is already in ECR"
    parameters = {
      ImageTag = {
        type           = "String"
        description    = "Git commit the images were built from"
        allowedPattern = "^[0-9a-f]{7,40}$"
      }
    }
    mainSteps = [{
      action = "aws:runShellScript"
      name   = "deploy"
      inputs = {
        timeoutSeconds = "900"
        runCommand     = ["/usr/local/bin/smartfin-deploy {{ ImageTag }}"]
      }
    }]
  })
}

data "aws_iam_policy_document" "github_deploy" {
  count = local.github_deploy ? 1 : 0

  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "PushImages"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:DescribeImages",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
    ]
    resources = [for repo in aws_ecr_repository.app : repo.arn]
  }

  statement {
    sid     = "RunTheDeployCommand"
    actions = ["ssm:SendCommand"]
    resources = [
      aws_ssm_document.deploy[0].arn,
      aws_instance.node.arn,
    ]
  }

  # Reading a command's result has no resource-level permission in SSM.
  statement {
    sid       = "ReadTheResult"
    actions   = ["ssm:GetCommandInvocation", "ssm:ListCommandInvocations"]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  count = local.github_deploy ? 1 : 0

  name   = "${var.name}-github-deploy"
  role   = aws_iam_role.github_deploy[0].id
  policy = data.aws_iam_policy_document.github_deploy[0].json
}

output "github_deploy_role_arn" {
  description = "Set this as the repository variable AWS_DEPLOY_ROLE_ARN on GitHub."
  value       = local.github_deploy ? aws_iam_role.github_deploy[0].arn : null
}

output "node_instance_id" {
  description = "Set this as the repository variable AWS_INSTANCE_ID on GitHub."
  value       = aws_instance.node.id
}
