# Create an IAM policy
resource "aws_iam_policy" "example" {
  name        = "example-policy"
  description = "Example policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:DescribeInstances",
        ]
        Effect = "Allow"
        Resource = "*"
      },
    ]
  })
}
