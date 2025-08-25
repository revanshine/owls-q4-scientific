# AWS Config - Frozen Control-Plane Compliance
# Implements recording group limitations to avoid Config charges

# S3 bucket for Config logs (only if Config is enabled)
resource "aws_s3_bucket" "config_logs" {
  count         = local.config_enabled ? 1 : 0
  bucket        = "${var.project_name}-config-logs-${var.environment}"
  force_destroy = true

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "AWS Config logs storage"
  }
}

# S3 bucket policy for Config service
resource "aws_s3_bucket_policy" "config_logs_policy" {
  count  = local.config_enabled ? 1 : 0
  bucket = aws_s3_bucket.config_logs[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.config_logs[0].arn
      },
      {
        Sid    = "AWSConfigBucketExistenceCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.config_logs[0].arn
      },
      {
        Sid    = "AWSConfigBucketDelivery"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.config_logs[0].arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })
}

# IAM role for AWS Config
resource "aws_iam_role" "config_role" {
  count = local.config_enabled ? 1 : 0
  name  = "${var.project_name}-config-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Attach AWS managed policy for Config
resource "aws_iam_role_policy_attachment" "config_role_policy" {
  count      = local.config_enabled ? 1 : 0
  role       = aws_iam_role.config_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/ConfigRole"
}

# AWS Config Delivery Channel
resource "aws_config_delivery_channel" "main" {
  count          = local.config_enabled ? 1 : 0
  name           = "${var.project_name}-config-delivery-${var.environment}"
  s3_bucket_name = aws_s3_bucket.config_logs[0].bucket
  depends_on     = [aws_s3_bucket_policy.config_logs_policy]
}

# AWS Config Configuration Recorder with VARIABLE scope
# Key implementation of frozen control-plane design
resource "aws_config_configuration_recorder" "main" {
  count    = local.config_enabled ? 1 : 0
  name     = "${var.project_name}-config-recorder-${var.environment}"
  role_arn = aws_iam_role.config_role[0].arn

  # CRITICAL: Variable recording group based on config_mode
  recording_group {
    all_supported                 = false
    include_global_resource_types = false
    
    # Use variable-based resource types
    # minimal mode: Only S3::Bucket, IAM::Role (frozen control-plane)
    # broad mode: Includes Lambda, SQS (for production monitoring)
    resource_types = local.config_resource_types
  }

  depends_on = [aws_config_delivery_channel.main]
}

# Enable the Configuration Recorder
resource "aws_config_configuration_recorder_status" "main" {
  count      = local.config_enabled ? 1 : 0
  name       = aws_config_configuration_recorder.main[0].name
  is_enabled = true
  depends_on = [aws_config_configuration_recorder.main]
}

# Outputs
output "config_recorder_name" {
  value       = local.config_enabled ? aws_config_configuration_recorder.main[0].name : "disabled"
  description = "AWS Config recorder name (or 'disabled' if Config is off)"
}

output "config_cost_optimization" {
  value = {
    mode                = var.config_mode
    enabled             = local.config_enabled
    recorded_types      = local.config_enabled ? local.config_resource_types : []
    excluded_types      = [
      "AWS::Lambda::Function",
      "AWS::SQS::Queue", 
      "AWS::Lambda::EventSourceMapping",
      "AWS::CloudWatch::LogGroup",
      "AWS::Lambda::Version",
      "AWS::ECS::TaskDefinition"
    ]
    cost_impact = var.config_mode == "minimal" ? "Very Low - Only control-plane resources" : (var.config_mode == "off" ? "Zero - Config disabled" : "Medium - Includes runtime resources")
  }
  description = "AWS Config cost optimization settings for frozen control-plane design"
}
