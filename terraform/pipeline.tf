# Create a CodePipeline
resource "aws_codepipeline" "example" {
  name     = "example-pipeline"
  role_arn = aws_iam_role.example.arn

  artifact_store {
    location = aws_s3_bucket.example.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      output_artifacts = ["source"]

      configuration = {
        BranchName           = "main"
        OutputArtifactFormat = "CODE_ZIP"
        PollForSourceChanges = false
        RepositoryName       = "example-repo"
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "CloudFormation"
      input_artifacts = ["source"]
      version         = "1"

      configuration = {
        ActionMode     = "CREATE_UPDATE"
        Capabilities  = "CAPABILITY_IAM,CAPABILITY_AUTO_EXPAND"
        OutputFileName = "CreateStackOutput.json"
        RoleArn        = aws_iam_role.example.arn
        StackName      = "example-stack"
        TemplatePath   = "source::template.yaml"
      }
    }
  }
}
