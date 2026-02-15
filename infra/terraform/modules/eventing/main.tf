resource "aws_sqs_queue" "job_events" {
  name = "${var.project}-${var.environment}-job-events"
}

resource "aws_sqs_queue" "job_events_dlq" {
  name = "${var.project}-${var.environment}-job-events-dlq"
}

resource "aws_cloudwatch_event_bus" "this" {
  name = "${var.project}-${var.environment}-bus"
}
