resource "aws_cloudwatch_log_group" "gateway" {
  name              = "/${var.project}/${var.environment}/gateway"
  retention_in_days = 14
}
