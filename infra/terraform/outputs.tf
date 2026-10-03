output "node_public_ip" {
  description = "Address of the server, for SSH and Ansible. The site itself is reached through site_url."
  value       = aws_eip.node.public_ip
}

output "site_url" {
  description = "The address to give people."
  value       = "https://${aws_cloudfront_distribution.site.domain_name}"
}

output "ssh_command" {
  value = "ssh ubuntu@${aws_eip.node.public_ip}"
}

output "ecr_registry" {
  description = "Registry host for docker login."
  value       = split("/", aws_ecr_repository.app["backend"].repository_url)[0]
}

output "ecr_backend_repository" {
  value = aws_ecr_repository.app["backend"].repository_url
}

output "ecr_frontend_repository" {
  value = aws_ecr_repository.app["frontend"].repository_url
}

output "uploads_bucket" {
  value = aws_s3_bucket.uploads.bucket
}

output "database_endpoint" {
  description = "Only reachable from the node."
  value       = aws_db_instance.main.endpoint
}

output "ssm_parameter_prefix" {
  description = "Where the app's secrets are stored."
  value       = "/${var.name}/"
}

output "region" {
  value = var.region
}
