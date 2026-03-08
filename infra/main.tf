terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# -------------------------------------------------------------------
# AMI Ubuntu 24.04 LTS (Canonical)
# -------------------------------------------------------------------
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# -------------------------------------------------------------------
# Security Group
# -------------------------------------------------------------------
resource "aws_security_group" "jobboard" {
  name        = "jobboard-sg"
  description = "Jobboard - SSH, API, Frontend"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Frontend"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jobboard-sg"
  }
}

# -------------------------------------------------------------------
# Key Pair
# -------------------------------------------------------------------
resource "aws_key_pair" "jobboard" {
  key_name   = "jobboard-key"
  public_key = file(var.public_key_path)
}

# -------------------------------------------------------------------
# EC2 Instance
# -------------------------------------------------------------------
resource "aws_instance" "jobboard" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.jobboard.key_name
  vpc_security_group_ids = [aws_security_group.jobboard.id]

  # Volume root suffisant pour les images Docker
  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name = "jobboard"
  }
}

# -------------------------------------------------------------------
# Elastic IP (IP fixe, connue avant et après redémarrage)
# -------------------------------------------------------------------
resource "aws_eip" "jobboard" {
  instance = aws_instance.jobboard.id
  domain   = "vpc"

  tags = {
    Name = "jobboard-eip"
  }
}
