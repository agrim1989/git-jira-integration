import asyncio
import os
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # Load dotenv
    from dotenv import load_dotenv
    project_root = Path(__file__).resolve().parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Server parameters
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(project_root / "custom_mcp_servers" / "jira_server.py")],
        env=os.environ.copy()
    )

    print("Connecting to Custom Python MCP server...")
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("Initializing session...")
            await session.initialize()
            
            print("Calling 'search_issues' tool...")
            try:
                result = await session.call_tool("search_issues", arguments={"max_results": 10})
                
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
