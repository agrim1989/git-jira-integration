import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    from dotenv import load_dotenv
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
            
            doc_content = """# Infrastructure and Resources for MCP Server for Jira

## Runtime
- Python 3.10+
- Virtual environment for dependencies (`mcp`, `jira`, `httpx`, `fastmcp`)

## Hosting
- Local execution via Stdio transport using Cursor, Claude Desktop, or Roo Code.
- No exposed HTTP server is strictly required for the MCP interface itself.
- (Optional) Deployed via Docker depending on the architecture.

## Secrets
- `JIRA_URL`: The Atlassian domain, e.g., `https://example.atlassian.net`.
- `JIRA_USERNAME`: The email address associated with the API token.
- `JIRA_API_TOKEN`: An Atlassian API Token for basic authentication.
- `GITHUB_TOKEN`: Classic Personal Access Token with read/write access to repos (if using the GitHub flow).

## Network
- Outbound HTTPS (port 443) access to the configured `JIRA_URL`.
- Outbound HTTPS (port 443) access to `api.github.com` (if using the GitHub flow).
"""
            
            tool_args = {
                "repo_url": repo_url,
                "branch_name": "KAN-15",
                "message": "KAN-15: Add infrastructure requirements documentation",
                "files": [
                    {
                        "path": "docs/infrastructure_requirements.md",
                        "content": doc_content
                    }
                ]
            }
            
            print(f"\nCalling 'git_commit_and_push_changes' tool for {repo_url} on branch KAN-15...")
            try:
                result = await session.call_tool("git_commit_and_push_changes", arguments=tool_args)
                print("\n--- Tool Result ---")
                if getattr(result, "isError", getattr(result, "is_error", False)):
                    print(f"Error: {result.content}")
                else:
                    for block in result.content:
                        if hasattr(block, "text"):
                            print(block.text)
                        elif isinstance(block, dict) and block.get("type") == "text":
                            print(block.get("text"))
            except Exception as e:
                print(f"Failed to call tool: {e}")

if __name__ == "__main__":
    asyncio.run(run())
