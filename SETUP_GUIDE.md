# Jira/Confluence MCP Server – Setup & Agent Invocation Guide

This guide covers:
1. **Invoking your “test agent” from Claude Code / Copilot / Amazon Q** when you type in their chat (by connecting the MCP server to each tool).
2. **Bringing up the mcp-atlassian server** on your machine, connecting it to your Jira (and optional Confluence) account, then connecting your chosen AI tool to that MCP server.

---

## Part 1: Invoking the agent from AI chat tools

Once the Jira/Confluence MCP server is configured in an AI tool, **the “agent” is that tool’s AI assistant**. When you enter a prompt in the chat, the assistant can call the MCP tools (e.g. `jira_search`, `jira_get_issue`, `confluence_search`) automatically. You don’t run a separate “test agent” app; the chat **is** the interface to the agent that uses MCP.

| Tool | How the “agent” is invoked | MCP config location |
|------|----------------------------|----------------------|
| **Cursor** | Open the AI chat (e.g. Cmd+L / Ctrl+L), type a prompt (e.g. “Find my Jira issues”). The model uses MCP tools when needed. | **Settings → Tools & MCP** or `~/.cursor/mcp.json` (see below) |
| **Claude Code / Claude Desktop** | Type in Claude’s chat; Claude uses the configured MCP servers (including mcp-atlassian) to answer. | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) |
| **VS Code + GitHub Copilot** | Use Copilot Chat; with MCP configured, Copilot can use Jira/Confluence tools. | User: `~/.vscode/mcp.json` or workspace: `.vscode/mcp.json` |
| **Amazon Q (CLI)** | Run `q chat "Use Jira to list my issues"`; Q uses the configured MCP server. | `q config set mcp.servers.<name>.command "..."` etc. |

So for “invoking a test agent from Claude Code / Copilot / Amazon Q”: you **add the mcp-atlassian server to that tool’s MCP config**, then **use that tool’s chat**; the prompts you enter there invoke the agent (the AI) which in turn uses the Jira/Confluence MCP.

---

## Part 2: Bring up mcp-atlassian and connect the agent

### Step 1: Get Atlassian credentials

1. **Jira Cloud API token**  
   Go to [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) and create a token.  
   You need:
   - **JIRA_URL**: e.g. `https://your-company.atlassian.net`
   - **JIRA_USERNAME**: your Atlassian account email
   - **JIRA_API_TOKEN**: the token you created

2. **(Optional) Confluence**  
   Same Atlassian account; create a token if you use Confluence.  
   - **CONFLUENCE_URL**: e.g. `https://your-company.atlassian.net/wiki`  
   - **CONFLUENCE_USERNAME** / **CONFLUENCE_API_TOKEN**

For **Jira/Confluence Server or Data Center**, use **Personal Access Token (PAT)** instead; see [mcp-atlassian authentication](https://mcp-atlassian.soomiles.com/docs/authentication).

### Step 2: Choose how to run mcp-atlassian

The server can run **on your machine** and the AI tool connects to it via **stdio** (recommended for local use) or over **HTTP/SSE** if you run it as a long-lived process.

#### Option A: uvx (recommended if you have Python/uv)

```bash
# Install uv (includes uvx) – one-line install
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart shell, then:
uvx mcp-atlassian --help
```

If that works, use the **uvx** config in Step 3. The server is started by Cursor/Claude/VS Code when you use the chat; you don’t start a separate process.

#### Option B: Docker

```bash
docker pull ghcr.io/sooperset/mcp-atlassian:latest
docker run --rm -i \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your.email@company.com \
  -e JIRA_API_TOKEN=your_api_token \
  ghcr.io/sooperset/mcp-atlassian:latest
```

For IDE integration you’ll configure the same env vars in the tool’s MCP config and use `command: "docker"` with the appropriate `args` (see docs and `cursor-mcp-atlassian-config.json` in this repo).

#### Option C: pip

```bash
pip install mcp-atlassian
mcp-atlassian --help
```

Then in MCP config use `command: "mcp-atlassian"` (or full path to the executable).

### Step 3: Connect the MCP server to your “test agent” (Cursor)

1. **Create or edit global MCP config**
   - **macOS:** `~/.cursor/mcp.json`
   - **Windows:** `%USERPROFILE%\.cursor\mcp.json`
   - Or in Cursor: **Settings (Cmd+,)** → **Tools & MCP** → **+ Add new global MCP server**

2. **Add the mcp-atlassian server**

   Use the snippet from **`cursor-mcp-atlassian-config.json`** in this repo. It looks like this (replace placeholders with your real values):

   ```json
   {
     "mcpServers": {
       "mcp-atlassian": {
         "command": "uvx",
         "args": ["mcp-atlassian"],
         "env": {
           "JIRA_URL": "https://your-company.atlassian.net",
           "JIRA_USERNAME": "your.email@company.com",
           "JIRA_API_TOKEN": "your_api_token",
           "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
           "CONFLUENCE_USERNAME": "your.email@company.com",
           "CONFLUENCE_API_TOKEN": "your_confluence_api_token"
         }
       }
     }
   }
   ```

   For **Jira only**, you can omit the `CONFLUENCE_*` variables.

3. **Restart Cursor** (or reload the MCP servers if the UI allows).

4. **Invoke the agent**: open the AI chat and type e.g.:
   - “Find issues assigned to me in project PROJ”
   - “Get details for issue PROJ-123”
   - “Search Confluence for onboarding docs”

The assistant will use the MCP tools when needed; that’s your “test agent” in action.

### Step 4: Optional – Same server in Claude Desktop, VS Code/Copilot, Amazon Q

- **Claude Desktop**  
  Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) and add the same `mcpServers.mcp-atlassian` block (with your real env). Restart Claude.

- **VS Code / GitHub Copilot**  
  Create or edit `~/.vscode/mcp.json` (or `.vscode/mcp.json` in the project) with the same structure. Copilot Chat will then be able to use the Jira/Confluence tools when you type in chat.

- **Amazon Q CLI**  
  After installing and authenticating Q:
  ```bash
  q config set mcp.servers.mcp-atlassian.command "uvx"
  q config set mcp.servers.mcp-atlassian.args "[\"mcp-atlassian\"]"
  # Set env (syntax may vary; see Q docs for MCP env)
  q chat "Use Jira to list my open issues"
  ```

---

## Quick checklist

- [ ] Atlassian API token (and optional Confluence token) created  
- [ ] uvx **or** Docker **or** pip chosen and working (`mcp-atlassian --help` or Docker run succeeds)  
- [ ] `~/.cursor/mcp.json` (or Cursor UI) updated with `mcp-atlassian` and your `env`  
- [ ] Cursor restarted / MCP reloaded  
- [ ] Test in Cursor chat: “Find my Jira issues” or “Get issue PROJ-123”  
- [ ] (Optional) Repeat for Claude Desktop, VS Code, or Amazon Q using the same server config  

---

## References

- [mcp-atlassian GitHub](https://github.com/sooperset/mcp-atlassian)
- [mcp-atlassian docs](https://mcp-atlassian.soomiles.com) (installation, authentication, configuration, tools)
- [Cursor MCP](https://cursor.fan/tutorial/HowTo/how-to-config-mcp-server-with-an-env-parameter-in-cursor) (config with env)
- [VS Code / Copilot MCP](https://code.visualstudio.com/docs/copilot/chat/mcp-servers)
- [Amazon Q CLI MCP](https://www.mcpstack.org/use/render-mcp-server/mcp-server/with/amazon-q-cli)
