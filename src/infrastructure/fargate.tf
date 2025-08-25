# OWLS Archive Q4 - ECS Fargate for Scientific Processing
# Frozen control-plane design with Fargate for heavy computational workloads

# ECS Cluster (create once, reuse for all tasks)
resource "aws_ecs_cluster" "q4_cluster" {
  name = "owls-q4-cluster"

  tags = {
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "Scientific Q4 processing"
  }
}

# ECS Task Definition (create once, reuse with different env vars)
resource "aws_ecs_task_definition" "q4_scientific_processor" {
  family                   = "owls-q4-scientific-processor"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024  # 1 vCPU
  memory                   = 2048  # 2 GB RAM for scientific computing
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "q4-processor"
      image = "owls-q4-scientific:latest"  # Will be built and pushed to ECR
      
      # Environment variables (data-plane parameters passed at runtime)
      environment = [
        {
          name  = "ARCHIVE_BUCKET"
          value = aws_s3_bucket.q4_archive.bucket
        },
        {
          name  = "ARTIFACTS_BUCKET"
          value = aws_s3_bucket.q4_artifacts.bucket
        },
        {
          name  = "DONE_QUEUE_URL"
          value = aws_sqs_queue.q4_done_queue.url
        }
      ]
      
      # Logging configuration
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.q4_fargate_logs.name
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "fargate"
        }
      }
      
      essential = true
    }
  ])

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# CloudWatch Log Group for Fargate tasks
resource "aws_cloudwatch_log_group" "q4_fargate_logs" {
  name              = "/aws/ecs/owls-q4-fargate"
  retention_in_days = 7

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ECS Execution Role (for pulling images and logging)
resource "aws_iam_role" "ecs_execution_role" {
  name = "owls-q4-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# Attach AWS managed policy for ECS task execution
resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role (for accessing S3, SQS during task execution)
resource "aws_iam_role" "ecs_task_role" {
  name = "owls-q4-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# ECS Task Policy (same permissions as Lambda for data-plane operations)
resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "owls-q4-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

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
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.q4_done_queue.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.q4_fargate_logs.arn}:*"
      }
    ]
  })
}

# Enhanced Lambda function for task orchestration
resource "aws_lambda_function" "q4_orchestrator" {
  filename         = "q4_orchestrator.zip"
  function_name    = "owls-q4-orchestrator"
  role            = aws_iam_role.q4_orchestrator_role.arn
  handler         = "orchestrator.lambda_handler"
  runtime         = "python3.12"
  timeout         = 60  # Just for orchestration, not processing

  environment {
    variables = {
      CLUSTER_NAME           = aws_ecs_cluster.q4_cluster.name
      TASK_DEFINITION_ARN    = aws_ecs_task_definition.q4_scientific_processor.arn
      SUBNET_IDS            = "subnet-12345"  # Will be configured for actual deployment
      SECURITY_GROUP_IDS    = "sg-12345"     # Will be configured for actual deployment
    }
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# IAM Role for Lambda orchestrator
resource "aws_iam_role" "q4_orchestrator_role" {
  name = "owls-q4-orchestrator-role"

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

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# IAM Policy for Lambda orchestrator
resource "aws_iam_role_policy" "q4_orchestrator_policy" {
  name = "owls-q4-orchestrator-policy"
  role = aws_iam_role.q4_orchestrator_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.q4_work_queue.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask"
        ]
        Resource = [
          aws_ecs_task_definition.q4_scientific_processor.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      }
    ]
  })
}

# SQS trigger for orchestrator Lambda (same as before)
resource "aws_lambda_event_source_mapping" "q4_orchestrator_trigger" {
  event_source_arn = aws_sqs_queue.q4_work_queue.arn
  function_name    = aws_lambda_function.q4_orchestrator.arn
  batch_size       = 1
}

# Outputs for Fargate deployment
output "ecs_cluster_name" {
  value       = aws_ecs_cluster.q4_cluster.name
  description = "ECS cluster for scientific Q4 processing"
}

output "task_definition_arn" {
  value       = aws_ecs_task_definition.q4_scientific_processor.arn
  description = "Task definition for Q4 Fargate processing"
}

output "fargate_log_group" {
  value       = aws_cloudwatch_log_group.q4_fargate_logs.name
  description = "CloudWatch log group for Fargate tasks"
}
