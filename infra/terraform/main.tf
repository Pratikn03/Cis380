provider "aws" {
  region = var.aws_region
}

module "network" {
  source               = "./modules/network"
  project              = var.project
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
}

module "storage" {
  source      = "./modules/storage"
  project     = var.project
  environment = var.environment
}

module "rds" {
  source            = "./modules/rds"
  project           = var.project
  environment       = var.environment
  vpc_id            = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
}

module "eventing" {
  source      = "./modules/eventing"
  project     = var.project
  environment = var.environment
}

module "ecs" {
  source            = "./modules/ecs"
  project           = var.project
  environment       = var.environment
  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids
}

module "observability" {
  source      = "./modules/observability"
  project     = var.project
  environment = var.environment
}
