output "vpc_id" {
  value = module.network.vpc_id
}

output "graphql_alb_dns" {
  value = module.ecs.gateway_alb_dns
}

output "uploads_bucket" {
  value = module.storage.uploads_bucket_name
}
