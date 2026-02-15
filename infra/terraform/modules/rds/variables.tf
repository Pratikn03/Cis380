variable "project" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "db_name" { type = string default = "sentifargo" }
variable "db_username" { type = string default = "sentifargo" }
variable "db_password" { type = string default = "change-me-in-secrets-manager" }
