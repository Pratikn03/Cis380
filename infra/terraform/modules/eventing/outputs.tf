output "event_bus_name" {
  value = aws_cloudwatch_event_bus.this.name
}

output "job_events_queue_url" {
  value = aws_sqs_queue.job_events.url
}
