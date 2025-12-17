# CloudFront CDN Module
# Content Delivery Network for frontend and static assets

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
}

variable "origin_domain" {
  description = "Origin domain (S3 bucket or ALB)"
  type        = string
}

variable "origin_type" {
  description = "Origin type (s3 or alb)"
  type        = string
  default     = "s3"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}

variable "enable_waf" {
  description = "Enable WAF for CloudFront"
  type        = bool
  default     = true
}

variable "waf_web_acl_id" {
  description = "WAF Web ACL ID"
  type        = string
  default     = ""
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_All"
}

variable "default_root_object" {
  description = "Default root object"
  type        = string
  default     = "index.html"
}

variable "allowed_methods" {
  description = "Allowed HTTP methods"
  type        = list(string)
  default     = ["GET", "HEAD", "OPTIONS"]
}

variable "cached_methods" {
  description = "Cached HTTP methods"
  type        = list(string)
  default     = ["GET", "HEAD"]
}

# Origin access control (for S3)
resource "aws_cloudfront_origin_access_control" "main" {
  count = var.origin_type == "s3" ? 1 : 0
  
  name                              = "${var.domain_name}-oac"
  description                       = "OAC for ${var.domain_name}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "GenNet CDN Distribution"
  default_root_object = var.default_root_object
  price_class         = var.price_class
  
  aliases = [var.domain_name]
  
  # Origin configuration
  dynamic "origin" {
    for_each = var.origin_type == "s3" ? [1] : []
    content {
      domain_name              = var.origin_domain
      origin_id                = "S3-${var.domain_name}"
      origin_access_control_id = aws_cloudfront_origin_access_control.main[0].id
    }
  }
  
  dynamic "origin" {
    for_each = var.origin_type == "alb" ? [1] : []
    content {
      domain_name = var.origin_domain
      origin_id   = "ALB-${var.domain_name}"
      
      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }
  
  # Default cache behavior
  default_cache_behavior {
    allowed_methods  = var.allowed_methods
    cached_methods   = var.cached_methods
    target_origin_id = var.origin_type == "s3" ? "S3-${var.domain_name}" : "ALB-${var.domain_name}"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }
  
  # Custom error responses
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }
  
  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  
  # Viewer certificate
  viewer_certificate {
    acm_certificate_arn      = var.certificate_arn
    ssl_support_method        = "sni-only"
    minimum_protocol_version  = "TLSv1.2_2021"
  }
  
  # WAF association
  web_acl_id = var.enable_waf && var.waf_web_acl_id != "" ? var.waf_web_acl_id : null
  
  tags = {
    Name = "${var.domain_name}-cdn"
  }
}

# Outputs
output "distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.main.id
}

output "distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.main.arn
}

output "domain_name" {
  description = "CloudFront domain name"
  value       = aws_cloudfront_distribution.main.domain_name
}

