# DeploySense — Production Environment Variables
#
# Usage: terraform plan -var-file="environments/production.tfvars"

aws_region             = "us-east-1"
environment            = "production"
project_name           = "deploysense"

# EKS
eks_cluster_version    = "1.30"
eks_node_instance_type = "t3.large"
eks_min_nodes          = 3
eks_max_nodes          = 10
eks_desired_nodes      = 3

# Database
db_instance_class      = "db.r6g.large"
db_allocated_storage   = 100
db_name                = "deploysense"
db_username            = "deploysense"
# db_password          = "SET VIA TF_VAR_db_password environment variable"

# Redis
redis_node_type        = "cache.r6g.large"
redis_num_cache_nodes  = 2

# Network
vpc_cidr               = "10.0.0.0/16"
