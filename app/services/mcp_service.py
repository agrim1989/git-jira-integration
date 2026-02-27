"""MCP client: connect to a server and call a tool with ticket data for solution."""
import os
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.config import settings
from app.models import TicketDetail
from app.services.jira_service import ticket_to_context_string

# Project root (parent of app/) so relative paths in MCP args resolve when running the API.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_server_config(mcp_server_key: str | None):
    servers = {s.key: s for s in settings.get_mcp_servers()}
    if not servers:
        raise ValueError(
            "No MCP servers configured. Set MCP_SERVERS_JSON (see .env.example and API_README.md)."
        )
    key = mcp_server_key or settings.default_mcp_server_key
    if not key:
        raise ValueError(
            "No MCP server key provided and DEFAULT_MCP_SERVER_KEY is not set. "
            f"Available keys: {list(servers.keys())}"
        )
    if key not in servers:
        raise ValueError(f"MCP server '{key}' not found. Available: {list(servers.keys())}")
    return servers[key]


def _extract_text_from_result(result) -> str:
    """Extract text from MCP CallToolResult content (list of ContentBlock)."""
    if result.is_error:
        return f"Error from MCP tool: {result.content}"
    parts = []
    for block in result.content or []:
        if hasattr(block, "text") and block.text:
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts) if parts else "(No text in tool response)"


async def call_mcp_solution(
    ticket: TicketDetail,
    mcp_server_key: str | None = None,
    tool_name: str | None = None,
    question: str | None = None,
    extra_tool_args: dict[str, Any] | None = None,
) -> str:
    """
    Connect to the configured MCP server, call the solution tool with ticket data (and optional question),
    return the tool's text response.
    """
    cfg = _get_server_config(mcp_server_key)
    name = tool_name or cfg.solution_tool_name
    ticket_context = ticket_to_context_string(ticket)
    args: dict[str, Any] = {
        "ticket_data": ticket_context,
        "question": question or "Provide a solution or recommendations for this ticket.",
    }
    if extra_tool_args:
        args.update(extra_tool_args)

    cwd = cfg.cwd if getattr(cfg, "cwd", None) else str(_PROJECT_ROOT)
    server_params = StdioServerParameters(
        command=cfg.command,
        args=cfg.args,
        env=cfg.env or None,
        cwd=cwd,
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        session = ClientSession(read_stream, write_stream)
        await session.initialize()
        result = await session.call_tool(name, args)
        return _extract_text_from_result(result)
