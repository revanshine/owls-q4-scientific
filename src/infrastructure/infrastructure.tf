# OWLS Archive Q4 - LocalStack Free Services Only
# Four-quadrant operator with frozen control-plane design

# S3 Buckets (create once, use prefixes for organization)
resource "aws_s3_bucket" "q4_archive" {
  bucket = "owls-q4-archive"
}

resource "aws_s3_bucket" "q4_artifacts" {
  bucket = "owls-q4-artifacts"
}

# SQS Queues (create once, reuse for all processing)
resource "aws_sqs_queue" "q4_work_queue" {
  name                      = "owls-q4-work"
  delay_seconds             = 0
  max_message_size          = 262144
  message_retention_seconds = 1209600
  receive_wait_time_seconds = 10
}

resource "aws_sqs_queue" "q4_done_queue" {
  name = "owls-q4-done"
}

# IAM Role for Lambda (create once, never modify)

# IAM Policy (create once, broad permissions for data-plane operations)

# Single Lambda function (create once, reuse for all processing)

# SQS Event Source Mapping (create once)

# Outputs for runtime data-plane operations
output "archive_bucket" {
  value = aws_s3_bucket.q4_archive.bucket
  description = "Use prefixes like: run=2025-08-25/input/, run=2025-08-25/output/"
}

output "artifacts_bucket" {
  value = aws_s3_bucket.q4_artifacts.bucket
  description = "Use prefixes like: manifests/2025-08-25/, results/2025-08-25/"
}

output "work_queue_url" {
  value = aws_sqs_queue.q4_work_queue.url
  description = "Send processing messages here - no new queues per run"
}

output "done_queue_url" {
  value = aws_sqs_queue.q4_done_queue.url
  description = "Completion notifications appear here"
}

output "lambda_function_name" {
  value = aws_lambda_function.q4_processor.function_name
  description = "Invoke this function - no new versions per run"
}
