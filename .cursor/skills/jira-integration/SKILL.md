---
name: jira-integration
description: Use the Jira MCP to search issues, create/update tickets, add comments, and transition status. Apply when the user asks about Jira, tickets, or issue management.
---

# Jira Integration Agent (MCP)

Use the **custom Jira MCP** for all Jira operations. Do not call the app's REST endpoints directly from agent flows; use MCP tools so behavior stays consistent and auditable.

## When to Use This Skill

- User asks to search, list, or find Jira issues
- User asks to create or update a ticket, add a comment, or change status
- User references a ticket key (e.g. KAN-57) and you need details or want to take action
- Any workflow that involves "Jira integration" or "issue management"

## MCP Tools to Use

| Tool | Purpose |
|------|--------|
| `get_issue` | Fetch full details of one issue by key (e.g. `KAN-57`) |
| `search_issues` | List/search with JQL; use `jql` and optional `max_results` (default 50) |
| `create_issue` | Create issue: `project_key`, `summary`, optional `description`, `issue_type` (default Task) |
| `update_issue` | Update summary and/or description for an issue |
| `add_comment` | Add a comment to an issue (`issue_key`, `comment` text) |
| `transition_issue` | Move issue to another status: `issue_key`, `transition_id` (e.g. 41 for Done) |

## Instructions

1. **Searching**: Prefer `search_issues` with specific JQL (e.g. `project = KAN AND status = "To Do"`) for relevant results. Default JQL is `project is not empty ORDER BY created DESC`.
2. **Single issue**: Use `get_issue(issue_key)` to get Key, Summary, Type, Status, Assignee, Project, Description, Created/Updated.
3. **Creating**: Use `create_issue(project_key, summary, description=None, issue_type="Task")`. Ensure project key and summary are non-empty.
4. **Updating**: Use `update_issue(issue_key, summary=None, description=None)` with only the fields you want to change.
5. **Comments**: Use `add_comment(issue_key, comment)` for plain text; keep content clear and professional.
6. **Transitions**: Use `transition_issue(issue_key, transition_id)`. Transition IDs are numeric and workflow-dependent (e.g. 21 = In Progress, 31/41 = Done). If unknown, suggest the user check Jira workflow or use the API to list transitions.

## Error Handling and Security

- Do not log or echo Jira credentials or tokens.
- If an MCP call returns an error string, surface it to the user and suggest checking Jira URL, credentials, and permissions.
- For "not configured" or auth errors, direct the user to set `JIRA_URL`, `JIRA_USERNAME`, and `JIRA_API_TOKEN` (e.g. in `.env` or app settings).

## Alignment with Project

- This skill aligns with `.cursor/rules/jira-integration.mdc` for consistent Jira usage.
- The backend implements these operations in `app/services/jira_service.py` and exposes them via `custom_mcp_servers/jira_server.py`; the agent should use the MCP, not duplicate logic.
