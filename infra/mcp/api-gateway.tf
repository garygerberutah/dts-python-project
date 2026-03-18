# Copyright 2026 by GuidoGerb Publishing, LLC
#
# API Gateway HTTP API v2 for the MCP server.

resource "aws_apigatewayv2_api" "mcp" {
  name          = "ggp3d-mcp-${var.environment}"
  protocol_type = "HTTP"
  description   = "MCP server endpoint (Streamable HTTP transport)"

  cors_configuration {
    allow_origins = var.cors_allowed_origins != "" ? split(",", var.cors_allowed_origins) : []
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 86400
  }
}

# Default stage with auto-deploy
resource "aws_apigatewayv2_stage" "mcp" {
  api_id      = aws_apigatewayv2_api.mcp.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.mcp_apigw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }
}

# Lambda integration
resource "aws_apigatewayv2_integration" "mcp_lambda" {
  api_id                 = aws_apigatewayv2_api.mcp.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.mcp_server.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# POST /mcp route
resource "aws_apigatewayv2_route" "mcp_post" {
  api_id    = aws_apigatewayv2_api.mcp.id
  route_key = "POST /mcp"
  target    = "integrations/${aws_apigatewayv2_integration.mcp_lambda.id}"
}

# GET /mcp route (for SSE / endpoint info)
resource "aws_apigatewayv2_route" "mcp_get" {
  api_id    = aws_apigatewayv2_api.mcp.id
  route_key = "GET /mcp"
  target    = "integrations/${aws_apigatewayv2_integration.mcp_lambda.id}"
}

# OPTIONS /mcp route (CORS preflight — handled by API Gateway CORS config)
resource "aws_apigatewayv2_route" "mcp_options" {
  api_id    = aws_apigatewayv2_api.mcp.id
  route_key = "OPTIONS /mcp"
  target    = "integrations/${aws_apigatewayv2_integration.mcp_lambda.id}"
}

# API Gateway access log group
resource "aws_cloudwatch_log_group" "mcp_apigw" {
  name              = "/aws/apigateway/ggp3d-mcp-${var.environment}"
  retention_in_days = 14
}
