output "gateway_alb_dns" {
  value = aws_lb.gateway.dns_name
}
