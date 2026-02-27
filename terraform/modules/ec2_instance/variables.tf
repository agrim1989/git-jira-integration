# Input variables for the EC2 instance module
variable "ami" {
  type        = string
  description = "The ID of the AMI to use for the instance"
}

variable "instance_type" {
  type        = string
  description = "The type of instance to start"
}
