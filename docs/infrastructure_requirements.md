# Infrastructure and Resources for MCP Server for Jira

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
