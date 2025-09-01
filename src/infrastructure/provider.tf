terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = "us-east-1"
  s3_use_path_style          = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    apigateway     = "http://localhost:4567"
    apigatewayv2   = "http://localhost:4567"
    cloudformation = "http://localhost:4567"
    cloudwatch     = "http://localhost:4567"
    dynamodb       = "http://localhost:4567"
    ec2            = "http://localhost:4567"
    ecs            = "http://localhost:4567"
    elasticache    = "http://localhost:4567"
    firehose       = "http://localhost:4567"
    iam            = "http://localhost:4567"
    kinesis        = "http://localhost:4567"
    lambda         = "http://localhost:4567"
    logs           = "http://localhost:4567"
    rds            = "http://localhost:4567"
    redshift       = "http://localhost:4567"
    route53        = "http://localhost:4567"
    s3             = "http://localhost:4567"
    secretsmanager = "http://localhost:4567"
    ses            = "http://localhost:4567"
    sns            = "http://localhost:4567"
    sqs            = "http://localhost:4567"
    ssm            = "http://localhost:4567"
    stepfunctions  = "http://localhost:4567"
    sts            = "http://localhost:4567"
  }
}
