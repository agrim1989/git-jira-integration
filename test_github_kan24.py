import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

async def run():
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "custom_mcp_servers" / "github_server.py")],
        env=os.environ.copy()
    )

    print("Connecting to Custom Python GitHub MCP server for KAN-24...")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("Initializing session...")
            await session.initialize()
            
            repo_url = os.environ.get("GITHUB_DEFAULT_REPO_URL", "https://github.com/agrim1989/git-jira-integration.git")
            
            dbx_s3_script_content = '''import os
import logging
from datetime import datetime
import dropbox
import boto3
from botocore.exceptions import NoCredentialsError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def transfer_from_dropbox_to_s3():
    # Load configuration
    dropbox_token = os.environ.get('DROPBOX_ACCESS_TOKEN')
    dropbox_folder = os.environ.get('DROPBOX_FOLDER_PATH', '')
    
    aws_access_key = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    s3_bucket = os.environ.get('S3_BUCKET_NAME')
    s3_prefix = os.environ.get('S3_PREFIX', 'dropbox-sync')

    if not all([dropbox_token, aws_access_key, aws_secret_key, s3_bucket]):
        logging.error("Missing required environment variables for authentication.")
        return False

    try:
        logging.info("Initializing Dropbox client...")
        dbx = dropbox.Dropbox(dropbox_token)
        
        logging.info("Initializing AWS S3 client...")
        s3 = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        logging.info(f"Listing files in Dropbox folder: '{dropbox_folder}'")
        folder_contents = dbx.files_list_folder(dropbox_folder)
        
        for entry in folder_contents.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                local_tmp_path = f"/tmp/{entry.name}"
                s3_key = f"{s3_prefix}/{entry.name}"
                
                logging.info(f"Downloading '{entry.name}' from Dropbox...")
                dbx.files_download_to_file(local_tmp_path, entry.path_lower)
                
                logging.info(f"Uploading '{entry.name}' to S3 bucket '{s3_bucket}'...")
                s3.upload_file(local_tmp_path, s3_bucket, s3_key)
                
                logging.info(f"Successfully transferred: {entry.name}")
                
                # Cleanup local temp file
                if os.path.exists(local_tmp_path):
                    os.remove(local_tmp_path)
                    
        logging.info("All files transferred successfully.")
        return True
        
    except dropbox.exceptions.ApiError as dbx_err:
        logging.error(f"Dropbox API error occurred: {dbx_err}")
    except NoCredentialsError:
        logging.error("AWS credentials not correctly provided.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        
    return False

if __name__ == "__main__":
    logging.info("Starting scheduled Dropbox to S3 transfer job.")
    success = transfer_from_dropbox_to_s3()
    if success:
        logging.info("Job completed successfully.")
    else:
        logging.error("Job failed.")
'''

            files_to_commit = [
                {
                    "path": "scripts/dropbox_to_s3.py",
                    "content": dbx_s3_script_content
                }
            ]
            
            branch_name = "KAN-24-custom-agent"
            
            tool_args = {
                "repo_url": repo_url,
                "branch_name": branch_name,
                "message": "KAN-24: Implement automated Dropbox to S3 data transfer script",
                "files": files_to_commit
            }
            
            print(f"\n1. Calling 'git_commit_and_push_changes' tool for {repo_url} on branch {branch_name}...")
            try:
                result = await session.call_tool("git_commit_and_push_changes", arguments=tool_args)
                if getattr(result, "isError", getattr(result, "is_error", False)):
                    print(f"Error executing git push: {result.content}")
                    return
                else:
                    print("Git push successful:")
                    for block in result.content:
                        if hasattr(block, "text"): print(block.text)
                        elif isinstance(block, dict) and block.get("type") == "text": print(block.get("text"))
            except Exception as e:
                print(f"Failed to call git_commit_and_push_changes tool: {e}")
                return

            print(f"\n2. Calling 'github_create_pull_request' tool on branch {branch_name}...")
            try:
                pr_args = {
                    "repo_url": repo_url,
                    "head_branch": branch_name,
                    "title": "KAN-24: Automated Dropbox to S3 Transfer Script",
                    "body": "This PR implements the Dropbox to S3 transfer script requested in KAN-24.\n\nKey features:\n- Dropbox authentication and file listing.\n- S3 authentication and file upload.\n- Structured logging.\n- Error handling for API limits and missing creds.\n\nAutomated via custom MCP agent!"
                }
                result = await session.call_tool("github_create_pull_request", arguments=pr_args)
                if getattr(result, "isError", getattr(result, "is_error", False)):
                    print(f"Error creating PR: {result.content}")
                else:
                    print("PR creation successful:")
                    for block in result.content:
                        if hasattr(block, "text"): print(block.text)
                        elif isinstance(block, dict) and block.get("type") == "text": print(block.get("text"))
            except Exception as e:
                print(f"Failed to call github_create_pull_request tool: {e}")

if __name__ == "__main__":
    asyncio.run(run())
