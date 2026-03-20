variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-north-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "public_key_path" {
  description = "Path to your local SSH public key"
  type        = string
  default     = "~/.ssh/id_ed25519.pub"
}

variable "ssh_allowed_cidrs" {
  description = "Restricted CIDR blocks allowed to SSH to EC2 (e.g. [\"203.0.113.10/32\"])"
  type        = list(string)
}

variable "postgres_db" {
  description = "PostgreSQL database name used by Docker Compose"
  type        = string
  default     = "jobboard_db"
}

variable "postgres_user" {
  description = "PostgreSQL user used by Docker Compose"
  type        = string
  default     = "user"
}

variable "postgres_password" {
  description = "PostgreSQL password used by Docker Compose"
  type        = string
  sensitive   = true
  default     = "password"
}

variable "scrape_interval_hours" {
  description = "Hours between automatic sync calls"
  type        = number
  default     = 6
}
