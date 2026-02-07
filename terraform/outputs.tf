# Research Collaboration System - Terraform Outputs

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnets" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnets
}

output "public_subnets" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnets
}

output "eks_cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_cluster_certificate_authority_data" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

output "eks_oidc_provider_arn" {
  description = "OIDC provider ARN for IRSA"
  value       = module.eks.oidc_provider_arn
}

output "ecr_repository_api_url" {
  description = "ECR repository URL for API"
  value       = aws_ecr_repository.research_api.repository_url
}

output "ecr_repository_web_url" {
  description = "ECR repository URL for Web"
  value       = aws_ecr_repository.research_web.repository_url
}

output "mongodb_endpoint" {
  description = "DocumentDB cluster endpoint"
  value       = var.use_managed_databases ? aws_docdb_cluster.research_db[0].endpoint : "N/A - Using self-managed"
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = var.use_managed_databases ? aws_elasticache_cluster.research_redis[0].cache_nodes[0].address : "N/A - Using self-managed"
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
}

output "deployment_instructions" {
  description = "Instructions for deploying the application"
  value       = <<-EOT
    
    ===============================================
    Research Collaboration System - Deployment Guide
    ===============================================
    
    1. Update kubeconfig:
       ${module.eks.cluster_name != "" ? "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}" : "N/A"}
    
    2. Build and push Docker images:
       docker build -t ${aws_ecr_repository.research_api.repository_url}:latest .
       docker push ${aws_ecr_repository.research_api.repository_url}:latest
    
    3. Apply Kubernetes manifests:
       kubectl apply -f k8s/
    
    4. Verify deployment:
       kubectl get pods -n research-system
       kubectl get services -n research-system
    
    ===============================================
  EOT
}
