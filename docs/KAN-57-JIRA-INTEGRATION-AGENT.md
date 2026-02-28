# KAN-57: Jira Integration Agent — Implementation & Usage

## Objective

Design and implement a Jira Integration agent that uses Cursor rules and skills with the **custom Jira MCP**, for seamless interaction: search issues, create/update tickets, add comments, and transition status.

## Deliverables Implemented

### 1. Jira Integration Agent (cursor skill + rule)

- **Skill**: `.cursor/skills/jira-integration/SKILL.md`  
  - When to use: Jira searches, create/update tickets, comments, status transitions.  
  - Documents all MCP tools: `get_issue`, `search_issues`, `create_issue`, `update_issue`, `add_comment`, `transition_issue`.  
  - Instructions for JQL, single-issue fetch, create/update, comments, transitions.  
  - Error handling and security (no logging of credentials).

- **Rule**: `.cursor/rules/jira-integration.mdc`  
  - Applies to Jira-related code and the jira-integration skill.  
  - Prefer MCP for agent flows; single source of truth in `app/services/jira_service.py`; safe errors; transition IDs documented/configurable where possible.

### 2. Backend and MCP

- **Transition support**:  
  - `app/services/jira_service.py`: added `transition_issue(issue_key, transition_id)` (POST `/rest/api/3/issue/{key}/transitions`).  
  - `custom_mcp_servers/jira_server.py`: new MCP tool `transition_issue(issue_key, transition_id)` delegating to the service.

- **Existing MCP tools** (unchanged): `get_issue`, `search_issues`, `create_issue`, `update_issue`, `add_comment`.

### 3. Configuration and Usage

- **Jira**: Set `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` (e.g. in `.env`).  
- **MCP**: Ensure the Jira MCP server is enabled and points at this project (so it uses `app.services.jira_service`).  
- **Agent**: In Cursor, when working on Jira or ticket management, the agent will use the skill and rule to call the Jira MCP tools instead of ad-hoc REST.

### 4. Testing

- **Unit test**: `tests/test_jira_integration.py` — tests `transition_issue` with a mocked HTTP client to avoid real Jira calls.  
- Run (from project root, with dependencies installed, e.g. in a venv):  
  `python3 -m unittest tests.test_jira_integration -v`

## Requirements Coverage

| Requirement | Status |
|-------------|--------|
| Align with .cursor/skills/jira-integration and .cursor/rules | Done (skill + rule created) |
| Robust framework for searching issues | Done (JQL via `search_issues`; documented in skill) |
| Create/update tickets, comments, status transitions | Done (service + MCP) |
| Error handling, logging, security | Done (service raises; no credentials in logs; skill guidance) |
| Testing for integration | Done (unit test for transition; doc for manual/MCP testing) |

## Transition IDs

Transition IDs are workflow-specific. Common examples (may vary by project):

- **21** — In Progress  
- **31** / **41** — Done  

To discover IDs for your project: use Jira’s “View workflow” or the REST endpoint `GET /rest/api/3/issue/{key}/transitions` (optional future enhancement).
