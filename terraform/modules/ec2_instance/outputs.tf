# Output values for the EC2 instance module
output "instance_id" {
  value       = aws_instance.example.id
  description = "The ID of the instance"
}

output "instance_ip" {
  value       = aws_instance.example.public_ip
  description = "The public IP address of the instance"
}
