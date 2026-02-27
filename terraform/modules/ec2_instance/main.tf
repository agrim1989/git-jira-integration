# File: modules/ec2_instance/main.tf
variable "ami" {
  type = string
}

variable "instance_type" {
  type = string
}

resource "aws_instance" "example" {
  ami           = var.ami
  instance_type = var.instance_type
}
