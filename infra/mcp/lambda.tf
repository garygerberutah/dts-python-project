# Copyright 2026 by GuidoGerb Publishing, LLC
#
# Lambda function for the MCP server.

resource "aws_lambda_function" "mcp_server" {
  function_name = "ggp3d-mcp-server-${var.environment}"
  runtime       = "python3.12"
  handler       = "mcp.servers.example_lambda.handler"
  role          = aws_iam_role.mcp_lambda.arn

  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)

  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout

  environment {
    variables = {
      CORS_ALLOWED_ORIGINS  = var.cors_allowed_origins
      COGNITO_USER_POOL_ID  = var.cognito_user_pool_id
      COGNITO_APP_CLIENT_ID = var.cognito_app_client_id
    }
  }
}

# IAM role for the Lambda function
resource "aws_iam_role" "mcp_lambda" {
  name = "ggp3d-mcp-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# CloudWatch Logs policy
resource "aws_iam_role_policy" "mcp_lambda_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.mcp_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/ggp3d-mcp-server-${var.environment}:*"
      }
    ]
  })
}

# CloudWatch Log Group with retention
resource "aws_cloudwatch_log_group" "mcp_lambda" {
  name              = "/aws/lambda/ggp3d-mcp-server-${var.environment}"
  retention_in_days = 14
}

# Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "mcp_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.mcp_server.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.mcp.execution_arn}/*/*"
}
