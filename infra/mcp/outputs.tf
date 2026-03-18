# Copyright 2026 by GuidoGerb Publishing, LLC
#
# Exported values for the MCP server infrastructure.

output "api_endpoint" {
  description = "The MCP server API endpoint URL"
  value       = aws_apigatewayv2_api.mcp.api_endpoint
}

output "api_id" {
  description = "API Gateway API ID"
  value       = aws_apigatewayv2_api.mcp.id
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.mcp_server.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.mcp_server.arn
}
