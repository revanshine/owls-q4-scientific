# Variables for OWLS Archive Q4
# Implements frozen control-plane design with Config cost control

variable "config_mode" {
  type        = string
  default     = "minimal"
  description = "AWS Config recording mode: 'off', 'minimal', or 'broad'"
  
  validation {
    condition     = contains(["off", "minimal", "broad"], var.config_mode)
    error_message = "Config mode must be 'off', 'minimal', or 'broad'."
  }
}

variable "environment" {
  type        = string
  default     = "development"
  description = "Environment name (development, staging, production)"
}

variable "project_name" {
  type        = string
  default     = "owls-q4"
  description = "Project name for resource naming"
}

# Config recording strategy based on mode
locals {
  config_enabled = var.config_mode != "off"
  
  # Minimal mode: Only essential resources (frozen control-plane compliant)
  minimal_resource_types = [
    "AWS::S3::Bucket",
    "AWS::IAM::Role"
  ]
  
  # Broad mode: Include more types (for production environments)
  broad_resource_types = [
    "AWS::S3::Bucket",
    "AWS::IAM::Role",
    "AWS::IAM::Policy",
    "AWS::Lambda::Function",
    "AWS::SQS::Queue"
  ]
  
  # Select resource types based on mode
  config_resource_types = var.config_mode == "broad" ? local.broad_resource_types : local.minimal_resource_types
}

# Outputs for debugging
output "config_settings" {
  value = {
    mode           = var.config_mode
    enabled        = local.config_enabled
    resource_types = local.config_resource_types
  }
  description = "Current AWS Config settings"
}
