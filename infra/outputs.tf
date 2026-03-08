output "public_ip" {
  description = "Elastic IP publique de l'instance"
  value       = aws_eip.jobboard.public_ip
}

output "api_url" {
  description = "URL de l'API"
  value       = "http://${aws_eip.jobboard.public_ip}:8000"
}

output "frontend_url" {
  description = "URL du frontend"
  value       = "http://${aws_eip.jobboard.public_ip}:3000"
}

output "ssh_command" {
  description = "Commande SSH pour se connecter à l'instance"
  value       = "ssh -i ~/.ssh/id_rsa ubuntu@${aws_eip.jobboard.public_ip}"
}
