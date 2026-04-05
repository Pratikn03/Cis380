resource "aws_ecs_cluster" "this" {
  name = "${var.project}-${var.environment}-cluster"
}

resource "aws_lb" "gateway" {
  name               = "${var.project}-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = var.public_subnet_ids
}
