# Jira/Confluence MCP integration

This folder holds config and docs to run the [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) MCP server and connect it to Cursor (and optionally Claude Code, Copilot, Amazon Q) so the AI chat can use Jira and Confluence tools.

## Quick start

1. **Read** [SETUP_GUIDE.md](./SETUP_GUIDE.md) for:
   - How the "agent" is invoked from each AI tool's chat
   - Bringing up mcp-atlassian (uvx / Docker / pip)
   - Connecting the MCP server to Cursor and other tools

2. **Credentials**
   - Create an API token: [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
   - Copy [.env.example](./.env.example) to `.env` and fill in your Jira (and optional Confluence) values.

3. **Cursor**
   - Copy the contents of [cursor-mcp-atlassian-config.json](./cursor-mcp-atlassian-config.json) into `~/.cursor/mcp.json` under `mcpServers`, or add the server via **Settings → Tools & MCP**.
   - Replace placeholder URLs and tokens with your real values.
   - Restart Cursor and try in chat: *"Find my Jira issues"* or *"Get issue PROJ-123"*.

## REST API (FastAPI)

The `app/` directory contains a FastAPI service that: (1) fetches tickets from Jira, (2) lets users ask for a solution for a ticket, and (3) passes ticket data to any MCP server for a solution. See [API_README.md](./API_README.md) for endpoints and configuration. Use `mcp_stub_server.py` to test without an LLM.

## Files

| File | Purpose |
|------|--------|
| [SETUP_GUIDE.md](./SETUP_GUIDE.md) | Full setup and "invoke agent" explanation |
| [API_README.md](./API_README.md) | REST API docs: fetch tickets, solution, MCP integration |
| [cursor-mcp-atlassian-config.json](./cursor-mcp-atlassian-config.json) | Cursor MCP config (uvx) |
| [cursor-mcp-atlassian-docker.json](./cursor-mcp-atlassian-docker.json) | Cursor MCP config (Docker) |
| [.env.example](./.env.example) | Example env for Jira/Confluence and MCP API |
| [mcp_stub_server.py](./mcp_stub_server.py) | Stub MCP server with `generate_solution` tool (for API testing) |

## Note

**uv/uvx** was not detected on this machine. You can:

- **Install uv** (recommended): `curl -LsSf https://astral.sh/uv/install.sh | sh`, then use `cursor-mcp-atlassian-config.json`.
- **Use Docker**: ensure Docker is installed and use `cursor-mcp-atlassian-docker.json` in Cursor's MCP config.
