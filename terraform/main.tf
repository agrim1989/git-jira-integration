# Configure the AWS Provider
provider "aws" {
  region = "us-west-2"
}

# Create an EC2 instance
resource "aws_instance" "example" {
  ami           = "ami-abc123"
  instance_type = "t2.micro"
}

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Create an RDS database
resource "aws_db_instance" "example" {
  allocated_storage    = 20
  engine               = "mysql"
  engine_version       = "5.7"
  instance_class       = "db.t2.micro"
  db_name              = "exampledb"
  username             = "admin"
  password             = random_password.db_password.result
  parameter_group_name = "default.mysql5.7"
}

# Create an S3 bucket
resource "aws_s3_bucket" "example" {
  bucket = "example-bucket-random-kan-27"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "example" {
  bucket = aws_s3_bucket.example.bucket
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
