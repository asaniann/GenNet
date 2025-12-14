output "endpoint" {
  description = "Neptune cluster endpoint"
  value       = aws_neptune_cluster.main.endpoint
}

output "reader_endpoint" {
  description = "Neptune cluster reader endpoint"
  value       = aws_neptune_cluster.main.reader_endpoint
}

