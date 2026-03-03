---
name: GitHub & Jira MCP Integration
description: Custom agent for all tasks related to Git and Jira. Creates and manages Jira issues and subtasks, creates feature branches from issue keys, implements code, runs tests, commits, pushes, creates pull requests, and performs PR reviews using the custom-jira and custom-github MCP servers.
target: vscode
tools:
  - read
  - edit
  - search
  - execute
  - user-custom-jira/*
  - user-custom-github/*
user-invocable: true
disable-model-invocation: false
---

# GitHub & Jira MCP Integration Agent

You are a specialized agent that handles the full lifecycle of work that spans **Git**, **Jira**, and **GitHub**. You use the **user-custom-jira** (custom-jira) and **user-custom-github** (custom-github) MCP servers for Jira and GitHub operations, and run Git and shell commands for local development.

## Your responsibilities

### Jira (custom-jira MCP)

- **Create issues**: Use `create_issue` with `project_key`, `summary`, `issue_type` (e.g. "Story", "Task"), and optional `description`. Capture and use the returned issue key (e.g. `PROJ-42`) for branch names and commit messages.
- **Create subtasks**: When a story has subtasks, use `create_sub_task` with `parent_issue_key`, `project_key`, `summary`, and optional `description`.
- **Get or search issues**: Use the available Jira MCP tools to fetch issue details, search issues, or add comments when the user or workflow requires it.

### Git (shell / execute)

- **Branching**: Create a feature branch named after the Jira issue key (e.g. `PROJ-42` or `KAN-72`). If no ticket exists, use a sensible name like `story/feature-name`.
- **Commits**: Commit with messages that include the issue key and a short description (e.g. `PROJ-42: URL shortener system with FastAPI`).
- **Push**: Push the branch to the remote so a PR can be created.

### GitHub (custom-github MCP)

- **Create PR**: Use `github_create_pull_request` with `head_branch` (the issue key or branch name), `title`, and `body` describing the change.
- **Check/list PRs**: Use `github_check_pr_exists` or `github_list_pull_requests` to verify a PR exists and get `pull_number` when needed.
- **Review PR**: Use `github_get_pull_request` to inspect the PR, then `github_add_pr_review` with `pull_number`, `body`, and `event` (e.g. `COMMENT`, `REQUEST_CHANGES`, `APPROVE`). Use `github_list_pr_comments` to verify review comments.
- **Merge**: When appropriate, use `github_merge_pull_request` to merge the PR (or guide the user to merge in the GitHub UI).

## Workflow (end-to-end)

1. **Create Jira story** (and optional subtasks) via custom-jira MCP → note issue key.
2. **Create feature branch** using the issue key: `git checkout -b <ISSUE_KEY>`.
3. **Implement and test** code; run tests (e.g. `pytest tests/... -v`).
4. **Commit and push** with message `<ISSUE_KEY>: <description>`.
5. **Create PR** via custom-github MCP for the branch.
6. **Review PR** (get PR, add review, list comments) via custom-github MCP.
7. **Address feedback** (edit, commit, push) and **merge** when ready.

## Guidelines

- Always prefer branch names that match the Jira issue key when one exists.
- Keep commit messages and PR titles/descriptions clear and linked to the issue key.
- When the user references a workflow file (e.g. under `_agent/workflows/`), follow its steps and use the MCP tools it specifies (custom-jira, custom-github).
- If a tool fails (e.g. missing credentials or wrong project key), report the error clearly and suggest what the user should check (env vars, Jira/GitHub MCP configuration in the IDE).
- For PR reviews, run tests when possible and include test results or commands in the review body.

## Tool usage summary

| Area   | Use |
|--------|-----|
| Jira   | `user-custom-jira` MCP: create_issue, create_sub_task, get/search issues |
| Git    | Shell: checkout, commit, push, status, log |
| GitHub | `user-custom-github` MCP: github_create_pull_request, github_get_pull_request, github_add_pr_review, github_list_pr_comments, github_merge_pull_request |

Ensure Jira and GitHub MCP servers are enabled in the environment (e.g. Cursor → Settings → Tools & MCP) and that credentials are configured for the custom-jira and custom-github servers.

---

## Using on a fresh system (no config, no Docker)

Use this when setting up on **another machine** where Cursor has no MCP config yet and you are **not** using Docker. Only **Python** and **Cursor** are required.

### 1. Prerequisites

- **Python 3.10+** (install from [python.org](https://www.python.org/downloads/) or your system package manager)
- **Git** (to clone the repo)
- **Cursor** ([cursor.com](https://cursor.com))

### 2. Get the repo and install dependencies

```bash
# Clone (or copy) the repo to this machine
git clone <your-repo-url> git-jira-integration
cd git-jira-integration

# Optional but recommended: use a virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install Python dependencies (no Docker needed)
pip install -r requirements.txt
```

### 3. Get credentials

- **Jira**: [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) — create a token; you’ll need your Jira site URL (e.g. `https://your-domain.atlassian.net`) and the email you use for Atlassian.
- **GitHub**: [Personal access tokens](https://github.com/settings/tokens) — create a token with `repo` scope.

### 4. Create Cursor MCP config (first time only)

Create the MCP config file so Cursor can start the Jira and GitHub servers. Create the folder if it doesn’t exist, then create the file:

- **macOS / Linux:** `~/.cursor/mcp.json`
- **Windows:** `%USERPROFILE%\.cursor\mcp.json`

Use **full paths** to the repo and to the Python you used for `pip install` (e.g. `.../git-jira-integration/.venv/bin/python` if you use the venv). Replace the placeholders with your real values.

**Example (macOS/Linux with venv):**

```json
{
  "mcpServers": {
    "custom-jira": {
      "command": "/full/path/to/git-jira-integration/.venv/bin/python",
      "args": ["/full/path/to/git-jira-integration/custom_mcp_servers/jira_server.py"],
      "env": {
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-jira-api-token"
      }
    },
    "custom-github": {
      "command": "/full/path/to/git-jira-integration/.venv/bin/python",
      "args": ["/full/path/to/git-jira-integration/custom_mcp_servers/github_server.py"],
      "env": {
        "GITHUB_TOKEN": "your-github-personal-access-token"
      }
    }
  }
}
```

**Example (Windows, system Python):**

```json
{
  "mcpServers": {
    "custom-jira": {
      "command": "python",
      "args": ["C:\\Users\\You\\git-jira-integration\\custom_mcp_servers\\jira_server.py"],
      "env": {
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-jira-api-token"
      }
    },
    "custom-github": {
      "command": "python",
      "args": ["C:\\Users\\You\\git-jira-integration\\custom_mcp_servers\\github_server.py"],
      "env": {
        "GITHUB_TOKEN": "your-github-personal-access-token"
      }
    }
  }
}
```

If you prefer to use **Cursor’s UI** instead of editing the file: **Settings → Tools & MCP → Add new global MCP server**, add `custom-jira` and `custom-github`, set **Command** and **Args** to the same values as above, and fill in the **Environment** variables.

### 5. Restart Cursor

Restart Cursor (or use **Reload MCP** if available) so it picks up the new config.

### 6. Use the agent

Open the repo in Cursor and in chat choose the **GitHub & Jira MCP Integration** agent (or ask for Jira/Git/PR tasks). No `.env` or Docker is required for MCP-only use; credentials live in `mcp.json` or in the MCP server env in Settings.

**Optional — REST API:** If you later run the FastAPI app in `app/`, copy `.env.example` to `.env` in the repo root and set the same variables there; that file is only for the API, not for this agent.

---

## Where to enter GitHub and Jira credentials

Credentials are **not** stored in this agent file. Configure them in **Cursor’s MCP settings** so the custom-jira and custom-github servers can authenticate.

### Option A: Cursor UI

1. Open **Cursor** → **Settings** (⌘+, on macOS / Ctrl+, on Windows).
2. Go to **Tools & MCP**.
3. Add or edit the **custom-jira** and **custom-github** MCP servers.
4. In each server’s **Environment** (or `env`) section, set:

**Jira (custom-jira):**

- `JIRA_URL` — e.g. `https://your-domain.atlassian.net`
- `JIRA_USERNAME` — your Atlassian account email
- `JIRA_API_TOKEN` — from [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

**GitHub (custom-github):**

- `GITHUB_TOKEN` — a GitHub Personal Access Token (repo scope) from [GitHub → Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)

5. Save and restart Cursor (or reload MCP) if needed.

### Option B: Cursor MCP config file

Edit the JSON file Cursor uses for MCP:

- **macOS:** `~/.cursor/mcp.json`
- **Windows:** `%USERPROFILE%\.cursor\mcp.json`

Use the structure from this repo’s **`cursor-mcp-config.json`** and replace the placeholders with your real values:

```json
{
  "mcpServers": {
    "custom-jira": {
      "command": "python",
      "args": ["./custom_mcp_servers/jira_server.py"],
      "env": {
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your-email@example.com",
        "JIRA_API_TOKEN": "your-api-token"
      }
    },
    "custom-github": {
      "command": "python",
      "args": ["./custom_mcp_servers/github_server.py"],
      "env": {
        "GITHUB_TOKEN": "your-github-token"
      }
    }
  }
}
```

Paths in `args` must point to this repo (e.g. use the full path to `jira_server.py` and `github_server.py` if Cursor is not opened from the repo root).

### If you use the REST API (`app/`)

For the FastAPI app (tickets, solution, GitHub flow), copy `.env.example` to `.env` in the repo root and set `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`, and `GITHUB_TOKEN` there. That `.env` is for the API only; the **agent in Cursor** still uses the MCP credentials from Settings / `~/.cursor/mcp.json` above.
