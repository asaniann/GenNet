data "aws_availability_zones" "available" {
  state = "available"
}

module "eks_cluster" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version
  vpc_id          = var.vpc_id
  subnet_ids      = var.subnet_ids

  cluster_endpoint_public_access = true

  eks_managed_node_groups = {
    for k, v in var.node_groups : k => {
      name            = "${var.cluster_name}-${k}"
      instance_types  = v.instance_types
      desired_size    = v.desired_size
      max_size        = v.max_size
      min_size        = v.min_size
      capacity_type   = "ON_DEMAND"

      labels = {
        role = k
      }

      taints = v.gpu_enabled ? [{
        key    = "nvidia.com/gpu"
        value  = "true"
        effect = "NO_SCHEDULE"
      }] : []

      # GPU node configuration
      ami_type       = v.gpu_enabled ? "AL2_x86_64_GPU" : "AL2_x86_64"
      k8s_labels = v.gpu_enabled ? {
        "accelerator" = "nvidia-tesla-t4"
      } : {}
    }
  }

  tags = var.tags
}

