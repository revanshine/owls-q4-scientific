# OWLS Q4 Infrastructure Deployment

## 🚀 Quick Start

```bash
# 1. Configure AWS credentials
aws configure --profile your-profile

# 2. Initialize Terraform
terraform init

# 3. Deploy infrastructure
terraform apply -var-file="production.tfvars"
```

## 📋 Prerequisites

- **Terraform** >= 1.0
- **AWS CLI** configured with appropriate permissions
- **Docker** (for container builds)

## 🔧 Configuration

### Required AWS Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "sqs:*",
        "ecs:*",
        "iam:*",
        "logs:*",
        "config:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### State Backend Setup

Create `backend.tf`:
```hcl
terraform {
  backend "s3" {
    bucket = "your-terraform-state-bucket"
    key    = "owls-q4/terraform.tfstate"
    region = "us-east-1"
  }
}
```

### Environment Variables

```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
export TF_VAR_environment=production
```

## 📁 Configuration Files

### `production.tfvars`
```hcl
# Environment settings
environment = "production"
project_name = "owls-q4"

# ECS Configuration
fargate_cpu = 1024
fargate_memory = 2048

# AWS Config (cost optimization)
config_mode = "minimal"  # off|minimal|broad

# Networking (update for your VPC)
vpc_id = "vpc-xxxxxxxxx"
subnet_ids = ["subnet-xxxxxxxxx", "subnet-yyyyyyyyy"]
```

### `development.tfvars`
```hcl
environment = "development"
project_name = "owls-q4-dev"
fargate_cpu = 512
fargate_memory = 1024
config_mode = "off"
```

## 🏗️ Infrastructure Components

| Resource | Purpose | Cost Impact |
|----------|---------|-------------|
| **ECS Cluster** | Fargate task execution | Pay-per-use |
| **S3 Buckets** | Data storage (archive + artifacts) | Storage + requests |
| **SQS Queues** | Message processing | Minimal |
| **IAM Roles** | Security permissions | Free |
| **CloudWatch** | Logging (7-day retention) | Log storage |
| **AWS Config** | Compliance monitoring | Configurable |

## 🚀 Deployment Commands

### Initial Deployment
```bash
# Plan deployment
terraform plan -var-file="production.tfvars"

# Apply infrastructure
terraform apply -var-file="production.tfvars"

# Get outputs
terraform output
```

### Updates
```bash
# Update with confirmation
terraform apply -var-file="production.tfvars"

# Auto-approve (CI/CD)
terraform apply -var-file="production.tfvars" -auto-approve
```

### Cleanup
```bash
# Destroy infrastructure
terraform destroy -var-file="production.tfvars"
```

## 📊 Outputs

After deployment, Terraform provides:

```bash
archive_bucket = "owls-q4-archive"
artifacts_bucket = "owls-q4-artifacts"
work_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/owls-q4-work"
done_queue_url = "https://sqs.us-east-1.amazonaws.com/123456789012/owls-q4-done"
ecs_cluster_name = "owls-q4-cluster"
task_definition_arn = "arn:aws:ecs:us-east-1:123456789012:task-definition/owls-q4-scientific-processor:1"
```

## 🔧 Troubleshooting

### Common Issues

**Permission Denied:**
```bash
# Check AWS credentials
aws sts get-caller-identity --profile your-profile

# Verify permissions
aws iam simulate-principal-policy --policy-source-arn $(aws sts get-caller-identity --query Arn --output text) --action-names ecs:CreateCluster
```

**State Lock:**
```bash
# Force unlock (use carefully)
terraform force-unlock LOCK_ID
```

**Resource Conflicts:**
```bash
# Import existing resources
terraform import aws_s3_bucket.q4_archive existing-bucket-name
```

### Validation
```bash
# Validate configuration
terraform validate

# Format code
terraform fmt

# Security scan
terraform plan | grep -i "security\|policy\|role"
```

## 💰 Cost Optimization

### AWS Config Settings
- **Off**: No compliance monitoring (lowest cost)
- **Minimal**: Only S3 + IAM monitoring
- **Broad**: Full resource monitoring

### Fargate Sizing
- **Development**: 512 CPU / 1024 MB
- **Production**: 1024 CPU / 2048 MB
- **Large datasets**: 2048 CPU / 4096 MB

### S3 Lifecycle
```hcl
# Add to terraform for cost savings
resource "aws_s3_bucket_lifecycle_configuration" "archive" {
  bucket = aws_s3_bucket.q4_archive.id

  rule {
    id     = "transition_to_ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }
}
```

## 🔐 Security Best Practices

### IAM Least Privilege
- ECS tasks have minimal S3/SQS permissions
- No cross-account access by default
- CloudWatch logs encrypted

### Network Security
- Fargate tasks in private subnets
- Security groups restrict access
- VPC endpoints for AWS services

### Data Protection
- S3 buckets not publicly accessible
- SQS messages encrypted in transit
- CloudWatch logs retention limited

## 📈 Monitoring

### CloudWatch Dashboards
```bash
# View Fargate metrics
aws logs describe-log-groups --log-group-name-prefix "/aws/ecs/owls-q4"

# Monitor SQS queues
aws sqs get-queue-attributes --queue-url $(terraform output -raw work_queue_url) --attribute-names All
```

### Alerts
```hcl
# Add to terraform for monitoring
resource "aws_cloudwatch_metric_alarm" "high_queue_depth" {
  alarm_name          = "owls-q4-high-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "100"
  alarm_description   = "This metric monitors SQS queue depth"
}
```

## 🧪 Testing Deployment

### Smoke Tests
```bash
# Test S3 access
aws s3 ls s3://$(terraform output -raw archive_bucket)

# Test SQS access
aws sqs send-message --queue-url $(terraform output -raw work_queue_url) --message-body "test"

# Test ECS cluster
aws ecs describe-clusters --clusters $(terraform output -raw ecs_cluster_name)
```

### Integration Tests
```bash
# Run container locally first
docker run -e AWS_PROFILE=your-profile owls-q4-scientific:latest

# Test Fargate task
aws ecs run-task --cluster $(terraform output -raw ecs_cluster_name) --task-definition $(terraform output -raw task_definition_arn) --launch-type FARGATE
```
