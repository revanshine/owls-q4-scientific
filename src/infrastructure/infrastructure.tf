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
resource "aws_iam_role" "q4_lambda_role" {
  name = "owls-q4-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy (create once, broad permissions for data-plane operations)
resource "aws_iam_role_policy" "q4_lambda_policy" {
  name = "owls-q4-lambda-policy"
  role = aws_iam_role.q4_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "${aws_s3_bucket.q4_archive.arn}",
          "${aws_s3_bucket.q4_archive.arn}/*",
          "${aws_s3_bucket.q4_artifacts.arn}",
          "${aws_s3_bucket.q4_artifacts.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.q4_work_queue.arn,
          aws_sqs_queue.q4_done_queue.arn
        ]
      }
    ]
  })
}

# Single Lambda function (create once, reuse for all processing)
resource "aws_lambda_function" "q4_processor" {
  filename         = "q4_processor.zip"
  function_name    = "owls-q4-processor"
  role            = aws_iam_role.q4_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.10"
  timeout         = 900

  environment {
    variables = {
      ARCHIVE_BUCKET   = aws_s3_bucket.q4_archive.bucket
      ARTIFACTS_BUCKET = aws_s3_bucket.q4_artifacts.bucket
      WORK_QUEUE_URL   = aws_sqs_queue.q4_work_queue.url
      DONE_QUEUE_URL   = aws_sqs_queue.q4_done_queue.url
    }
  }
}

# SQS Event Source Mapping (create once)
resource "aws_lambda_event_source_mapping" "q4_sqs_trigger" {
  event_source_arn = aws_sqs_queue.q4_work_queue.arn
  function_name    = aws_lambda_function.q4_processor.arn
  batch_size       = 1
}

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
