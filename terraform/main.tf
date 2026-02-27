# Configure the AWS Provider
provider "aws" {
  region = "us-west-2"
  access_key = "YOUR_ACCESS_KEY"
  secret_key = "YOUR_SECRET_KEY"
}

# Create an EC2 instance
resource "aws_instance" "example" {
  ami           = "ami-abc123"
  instance_type = "t2.micro"
}

# Create an RDS database
resource "aws_db_instance" "example" {
  allocated_storage    = 20
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = "db.t2.micro"
  name                 = "exampledb"
  username             = "admin"
  password             = "password"
  parameter_group_name = "default.mysql5.7"
}

# Create an S3 bucket
resource "aws_s3_bucket" "example" {
  bucket = "example-bucket"
  acl    = "private"
}
