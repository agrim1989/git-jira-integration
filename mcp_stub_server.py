"""
Minimal MCP server that exposes a 'generate_solution' tool for testing the API.
Accepts ticket_data and question, returns a formatted response (no LLM required).
Run: uv run mcp_stub_server.py   or   python mcp_stub_server.py
"""
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("jira-solution-stub")


@mcp.tool()
def generate_solution(ticket_data: str, question: str = "Provide a solution or recommendations.") -> str:
    """Generate a solution or recommendations for a Jira ticket."""
    return f"""## Stub solution (no LLM)

**Your question:** {question}

**Ticket context provided:**
```
{ticket_data}
```

To get real solutions, point MCP_SERVERS_JSON to an MCP server that calls an LLM with this context.
"""


if __name__ == "__main__":
    mcp.run(transport="stdio")
