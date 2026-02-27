# Jira + MCP Solution REST API

FastAPI REST API that:

1. **Fetches tickets** from Jira (list and get by key).
2. Lets **users ask for a solution** related to a ticket.
3. **Passes ticket data to any MCP server** and returns the solution from that server.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/tickets` | List tickets (JQL, max_results, start_at) |
| GET | `/tickets/{ticket_id}` | Get one ticket (e.g. PROJ-123) |
| POST | `/tickets/{ticket_id}/solution` | Ask for a solution for a ticket (Groq or default MCP server) |
| POST | `/tickets/{ticket_id}/solution/post-to-jira` | Generate plan + solution, post as comment; for Story/Epic also create sub-tasks from suggested list |
| POST | `/tickets/{ticket_id}/github-flow` | Branch (name = Jira ID), AI code + tests, push, open PR, post PR link to Jira for review |
| GET | `/tickets/{ticket_id}/pr` | Get PR URL for this ticket's branch (if a PR exists) |
| POST | `/tickets/{ticket_id}/code-review` | Find PR for Jira ID, run AI code review on diff, post review as comment on the PR |
| POST | `/mcp/solution` | Pass ticket to a chosen MCP server and get solution |

## 1. Fetch tickets

- **GET /tickets**  
  Query params: `jql` (default: `order by created DESC`), `max_results` (1–100), `start_at`.  
  Returns a list of ticket summaries (key, summary, status, issue_type, assignee).

- **GET /tickets/{ticket_id}**  
  Returns full ticket details (key, summary, description, status, type, assignee, project, created, updated).

## 2. Generate plan and post solution to Jira (with sub-tasks for Story/Epic)

- **POST /tickets/{ticket_id}/solution/post-to-jira**  
  Body (optional): `{ "question": "How do I fix this?" }`  
  The API generates an **approach plan**, **solution**, and for **Story or Epic** a **Suggested sub-tasks** list (using Groq or MCP). It then **posts the solution as a comment** on the ticket. If the ticket is a **Story or Epic**, it **creates sub-tasks** in Jira from the suggested list.  
  Response: `ticket_id`, `solution`, `comment_id`, `comment_url`, `created_subtask_keys` (e.g. `["PROJ-124", "PROJ-125"]`), `success`.

## 3. GitHub flow (branch, AI code + tests, PR, Jira review link)

- **POST /tickets/{ticket_id}/github-flow**  
  Body: `{ "repo_url": "https://github.com/owner/repo.git", "language": "python", "test_framework": "pytest", "question": "..." }`  
  - `repo_url` (optional): override `GITHUB_DEFAULT_REPO_URL`.  
  - `language` (required): e.g. `python`, `typescript` (code and tests are generated in this language).  
  - `test_framework` (optional): e.g. `pytest`, `jest`; defaults from language if omitted.  
  - `question` (optional): passed to solution generation.  

  The API (1) fetches the ticket and generates a solution (Groq), (2) clones the repo and creates a branch named after the Jira ID (e.g. `PROJ-123`), (3) generates implementation files and applies them, commits and pushes, (4) generates test files, commits and pushes, (5) creates a Pull Request and posts the PR link as a Jira comment for review.  
  Requires `GITHUB_TOKEN` (repo scope) and either `GITHUB_DEFAULT_REPO_URL` or `repo_url` in the body.  
  Response: `ticket_id`, `branch`, `commit_sha`, `test_commit_sha`, `pr_url`, `jira_comment_id`, `jira_comment_url`, `success`, `error` (if partial failure).  
  If the branch already exists on the remote, returns **409** (use a different ticket or delete the branch).

## 3b. Code review for a ticket's PR

- **GET /tickets/{ticket_id}/pr**  
  Returns `{ "pr_url": "..." }` if a GitHub PR exists for the branch named after the ticket (e.g. `PROJ-123`). Otherwise `pr_url` is `null`.

- **POST /tickets/{ticket_id}/code-review**  
  When a code review is requested for a Jira ticket: (1) finds the open PR for that ticket's branch, (2) runs an AI code review on the PR diff (Groq), (3) posts the review as a comment on the PR.  
  Body (optional): `{ "repo_url": "https://github.com/owner/repo.git", "base_branch": "main" }`.  
  Requires `GITHUB_TOKEN`, `GITHUB_DEFAULT_REPO_URL`, and `GROQ_API_KEY`.  
  Returns `ticket_id`, `pr_url`, `review_posted`, `review_url`.  
  If no PR exists for the ticket, returns **404**.

## 4. User asks solution for a ticket (no Jira update)

- **POST /tickets/{ticket_id}/solution**  
  Body (optional): `{ "question": "How do I fix the login bug?" }`  
  The API fetches the ticket, then calls Groq or the **default MCP server** with the ticket data and question. For **Story or Epic**, the solution text includes a **Suggested sub-tasks** section (which tasks to create under it).  
  Response: `ticket_id`, `ticket_summary`, `question`, `solution`, `mcp_server_key`, `tool_name`.

## 5. Pass ticket to any MCP server for solution

- **POST /mcp/solution**  
  Body:
  ```json
  {
    "ticket_id": "PROJ-123",
    "mcp_server_key": "my-server",
    "tool_name": "generate_solution",
    "question": "What are the root cause and fix?",
    "tool_arguments": {}
  }
  ```
  - `mcp_server_key`: key from `MCP_SERVERS_JSON` (optional if default is set).  
  - `tool_name`: tool to call (optional; uses server’s `solution_tool_name`).  
  - `tool_arguments`: extra args merged with `ticket_data` and `question`.  

  The API fetches the ticket, passes its context (and question) to the chosen MCP server’s tool, and returns the tool output as the solution.

## Configuration

- **Jira** (required for fetch and solution):  
  `JIRA_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN` in `.env` (see `.env.example`).

- **Groq** (optional): If `GROQ_API_KEY` is set, POST /tickets/{id}/solution and the GitHub flow use [Groq](https://console.groq.com/keys). Optional `GROQ_MODEL` (default `llama-3.3-70b-versatile`).

- **GitHub flow**: `GITHUB_TOKEN` (Personal Access Token with repo scope) for clone, push, and Create PR API. Optional `GITHUB_DEFAULT_REPO_URL` (HTTPS or SSH); can be overridden per request with `repo_url`.

- **Default MCP server** (for POST /tickets/{id}/solution when Groq is not used):  
  `DEFAULT_MCP_SERVER_KEY` = one of the keys in `MCP_SERVERS_JSON`.

- **MCP servers** (for POST /mcp/solution and default solution):  
  `MCP_SERVERS_JSON` = JSON array of server configs. Each object:
  - `key`: unique id (e.g. `"solution-stub"`).
  - `command`: executable (e.g. `"python"`, `"uvx"`).
  - `args`: list of args (e.g. `["mcp_stub_server.py"]`).
  - `env`: optional env vars for the process.
  - `solution_tool_name`: tool called with `ticket_data` and `question` (default `"generate_solution"`).

### Example .env (stub server in this repo)

```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=your_token

DEFAULT_MCP_SERVER_KEY=solution-stub
MCP_SERVERS_JSON=[{"key":"solution-stub","command":"python","args":["mcp_stub_server.py"],"env":{},"solution_tool_name":"generate_solution"}]
```

Run the stub server from the repo root so `python mcp_stub_server.py` works (or use full path in `args`).

## Run the API

```bash
cd /path/to/jira_mcp_integration
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Jira and MCP settings
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

## PR Manager MCP (validate, review, post comments on GitHub)

`mcp_pr_manager.py` is an MCP server that acts as a **Project Manager / Team Leader**: it validates a PR (optional test run), runs an AI code review, and **posts the review plus inline code comments** on the GitHub PR.

- **Tool**: `validate_review_and_comment_on_pr(repo_url, branch_name, base_branch="main", run_tests=False, test_command="pytest", post_to_github=True, token=None)`
- **Flow**: Resolves the open PR for the branch → optionally runs tests and includes output in the review → runs Groq-based structured review (summary + inline comments per file/line) → submits the review to GitHub with a summary body and inline comments on the relevant lines.
- **Requires**: `GROQ_API_KEY`, and `GITHUB_TOKEN` (when `post_to_github=True`). Add the server to Cursor/IDE MCP config (e.g. `cursor-mcp-config.json`) as `pr-manager`.

## Stub MCP server (testing without an LLM)

`mcp_stub_server.py` is a minimal MCP server that exposes `generate_solution(ticket_data, question)`. It returns a formatted echo of the inputs (no LLM). Use it to test the flow:

```bash
# Terminal 1 – stub (optional; the API spawns it when you call solution endpoints)
python mcp_stub_server.py

# Terminal 2 – API
uvicorn app.main:app --reload --port 8000
```

Configure `MCP_SERVERS_JSON` with `command: "python"`, `args: ["/full/path/to/mcp_stub_server.py"]` so the API can spawn the stub when handling solution requests.

## Custom MCP server for real solutions

Your MCP server should expose a tool that accepts at least:

- `ticket_data` (string): ticket key, summary, description, status, etc.
- `question` (string): user question.

The tool can call an LLM with this context and return the model’s answer. Set that server in `MCP_SERVERS_JSON` and use its key in `DEFAULT_MCP_SERVER_KEY` or in `mcp_server_key` in POST /mcp/solution.
