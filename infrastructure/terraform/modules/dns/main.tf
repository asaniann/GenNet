# DNS and Global Load Balancing Module
# Route 53 configuration with health checks and routing policies

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

variable "subdomain" {
  description = "Subdomain (e.g., api, www)"
  type        = string
  default     = "api"
}

variable "regions" {
  description = "List of regions with endpoints"
  type = list(object({
    region     = string
    endpoint   = string
    health_url = string
  }))
}

variable "routing_policy" {
  description = "Routing policy (latency, geolocation, weighted, failover)"
  type        = string
  default     = "latency"
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "health_check_threshold" {
  description = "Number of consecutive health checks required"
  type        = number
  default     = 3
}

# Health checks for each region
resource "aws_route53_health_check" "region" {
  for_each = { for r in var.regions : r.region => r }
  
  fqdn              = each.value.endpoint
  port              = 443
  type              = "HTTPS"
  resource_path     = each.value.health_url
  request_interval  = var.health_check_interval
  failure_threshold = var.health_check_threshold
  measure_latency   = true
  
  tags = {
    Name = "${var.domain_name}-health-${each.key}"
  }
}

# Route 53 hosted zone (assumes zone already exists)
data "aws_route53_zone" "main" {
  name = var.domain_name
}

# Route 53 records based on routing policy
resource "aws_route53_record" "main" {
  for_each = { for r in var.regions : r.region => r }
  
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${var.subdomain}.${var.domain_name}"
  type    = "A"
  
  set_identifier = each.key
  
  health_check_id = aws_route53_health_check.region[each.key].id
  
  dynamic "latency_routing_policy" {
    for_each = var.routing_policy == "latency" ? [1] : []
    content {
      region = each.value.region
    }
  }
  
  dynamic "geolocation_routing_policy" {
    for_each = var.routing_policy == "geolocation" ? [1] : []
    content {
      continent   = lookup(each.value, "continent", null)
      country     = lookup(each.value, "country", null)
      subdivision = lookup(each.value, "subdivision", null)
    }
  }
  
  dynamic "weighted_routing_policy" {
    for_each = var.routing_policy == "weighted" ? [1] : []
    content {
      weight = lookup(each.value, "weight", 1)
    }
  }
  
  dynamic "failover_routing_policy" {
    for_each = var.routing_policy == "failover" ? [1] : []
    content {
      type = lookup(each.value, "failover_type", "PRIMARY")
    }
  }
  
  alias {
    name                   = each.value.endpoint
    zone_id                = data.aws_route53_zone.main.zone_id
    evaluate_target_health = true
  }
  
  ttl = 60
}

# Outputs
output "dns_name" {
  description = "DNS name for the application"
  value       = "${var.subdomain}.${var.domain_name}"
}

output "health_check_ids" {
  description = "Health check IDs"
  value       = { for k, v in aws_route53_health_check.region : k => v.id }
}

