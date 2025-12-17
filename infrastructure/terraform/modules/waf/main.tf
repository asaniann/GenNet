# Web Application Firewall (WAF) Module
# AWS WAF configuration for DDoS protection and security

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "name" {
  description = "WAF name"
  type        = string
}

variable "scope" {
  description = "WAF scope (CLOUDFRONT or REGIONAL)"
  type        = string
  default     = "REGIONAL"
}

variable "enable_managed_rules" {
  description = "Enable AWS managed rules"
  type        = bool
  default     = true
}

variable "enable_rate_based_rules" {
  description = "Enable rate-based rules"
  type        = bool
  default     = true
}

variable "rate_limit" {
  description = "Rate limit (requests per 5 minutes)"
  type        = number
  default     = 2000
}

# WAF Web ACL
resource "aws_wafv2_web_acl" "main" {
  name        = var.name
  description = "GenNet WAF Web ACL"
  scope       = var.scope
  
  default_action {
    allow {}
  }
  
  # AWS Managed Rules - Core Rule Set
  dynamic "rule" {
    for_each = var.enable_managed_rules ? [1] : []
    content {
      name     = "AWSManagedRulesCommonRuleSet"
      priority = 1
      
      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesCommonRuleSet"
          vendor_name = "AWS"
        }
      }
      
      override_action {
        none {}
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "CommonRuleSetMetric"
        sampled_requests_enabled   = true
      }
    }
  }
  
  # AWS Managed Rules - Known Bad Inputs
  dynamic "rule" {
    for_each = var.enable_managed_rules ? [1] : []
    content {
      name     = "AWSManagedRulesKnownBadInputsRuleSet"
      priority = 2
      
      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesKnownBadInputsRuleSet"
          vendor_name = "AWS"
        }
      }
      
      override_action {
        none {}
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "KnownBadInputsMetric"
        sampled_requests_enabled   = true
      }
    }
  }
  
  # AWS Managed Rules - Linux Operating System
  dynamic "rule" {
    for_each = var.enable_managed_rules ? [1] : []
    content {
      name     = "AWSManagedRulesLinuxRuleSet"
      priority = 3
      
      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesLinuxRuleSet"
          vendor_name = "AWS"
        }
      }
      
      override_action {
        none {}
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "LinuxRuleSetMetric"
        sampled_requests_enabled   = true
      }
    }
  }
  
  # Rate-based rule
  dynamic "rule" {
    for_each = var.enable_rate_based_rules ? [1] : []
    content {
      name     = "RateBasedRule"
      priority = 10
      
      statement {
        rate_based_statement {
          limit              = var.rate_limit
          aggregate_key_type = "IP"
        }
      }
      
      action {
        block {}
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "RateBasedRuleMetric"
        sampled_requests_enabled   = true
      }
    }
  }
  
  # IP reputation rule
  dynamic "rule" {
    for_each = var.enable_managed_rules ? [1] : []
    content {
      name     = "AWSManagedRulesAmazonIpReputationList"
      priority = 4
      
      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesAmazonIpReputationList"
          vendor_name = "AWS"
        }
      }
      
      override_action {
        none {}
      }
      
      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "IPReputationMetric"
        sampled_requests_enabled   = true
      }
    }
  }
  
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${var.name}Metric"
    sampled_requests_enabled   = true
  }
  
  tags = {
    Name = var.name
  }
}

# Outputs
output "web_acl_id" {
  description = "WAF Web ACL ID"
  value       = aws_wafv2_web_acl.main.id
}

output "web_acl_arn" {
  description = "WAF Web ACL ARN"
  value       = aws_wafv2_web_acl.main.arn
}

