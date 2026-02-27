import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

async def run():
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Server parameters for GitHub Server
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "custom_mcp_servers" / "github_server.py")],
        env=os.environ.copy()
    )

    print("Connecting to Custom Python GitHub MCP server...")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("Initializing session...")
            await session.initialize()
            
            repo_url = os.environ.get("GITHUB_DEFAULT_REPO_URL", "https://github.com/agrim1989/git-jira-integration.git")
            
            # Read files from local disk
            files_to_commit = []
            file_paths = [
                "custom_mcp_servers/jira_server.py",
                "custom_mcp_servers/github_server.py"
            ]
            
            for fp in file_paths:
                full_path = project_root / fp
                if full_path.exists():
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        if fp == "custom_mcp_servers/jira_server.py":
                            content += "\n# Automated commit for KAN-5 via custom MCP agent\n"
                        files_to_commit.append({
                            "path": fp,
                            "content": content
                        })
            
            tool_args = {
                "repo_url": repo_url,
                "branch_name": "KAN-5-custom-agent-retry",
                "message": "KAN-5: Create MCP server for Jira and Github integration",
                "files": files_to_commit
            }
            
            print(f"\n1. Calling 'git_commit_and_push_changes' tool for {repo_url} on branch KAN-5-custom-agent-retry...")
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

            print(f"\n2. Calling 'github_create_pull_request' tool on branch KAN-5-custom-agent-retry...")
            try:
                pr_args = {
                    "repo_url": repo_url,
                    "head_branch": "KAN-5-custom-agent-retry",
                    "title": "KAN-5: Create MCP server for Jira integration",
                    "body": "This PR introduces two custom python MCP servers (`jira_server.py` and `github_server.py`) and configures `cursor-mcp-config.json` to leverage them for fast natural language automation with Jira and Github.\n\nAutomated via MCP!"
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
