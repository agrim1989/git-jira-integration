---
description: Workflow for URL Shortener - Design a URL shorten system using FastAPI
---

This workflow automates Jira ticket creation, development, testing, PR creation, and PR review for the URL shortener story (design a URL shorten system using Fast API). The story may or may not have subtasks.

## How to run this workflow

**Option A – In Cursor (AI / workflow-agent)**  
Open the AI chat and ask it to run the workflow. Example prompts:
- *"Run the url-shorten workflow from _agent/workflows/url-shorten.md"*
- *"Execute all steps of the URL shortener workflow"*
- Or step-by-step: *"Do step 1 of the url-shorten workflow"* then *"Do step 2 with issue key KAN-70"*, etc.

The AI will use **custom_jira** and **custom_github** MCP servers for steps 1, 2, 7, 8 and run git/test commands for the rest. Ensure Jira and GitHub MCPs are enabled in Cursor (Settings → Tools & MCP).

**Option B – Manually**  
1. **Step 1:** Create a Jira Story (in Jira or via Cursor: *"Create a Jira story for URL shortener using custom-jira"*). Note the issue key.  
2. **Step 2:** Run `git checkout -b <ISSUE_KEY>`.  
3. **Steps 3–4:** Implement URL shortener and tests (`url_shortener/`, `tests/test_url_shortener.py`).  
4. **Step 5:** Run `pytest tests/test_url_shortener.py -v`.  
5. **Step 6:** Commit and push with message `<ISSUE_KEY>: URL shortener system with FastAPI (...)`.  
6. **Step 7:** Create PR via Cursor (*"Create a PR for branch <ISSUE_KEY> using custom-github"*) or on GitHub.  
7. **Step 8:** Check PR, run review (pr-manager or github_add_pr_review), verify comments.  
8. **Step 9:** Address feedback and merge.

**Prerequisites:** Jira and GitHub MCP servers configured in Cursor; repo clone with `main` up to date.

---

// turbo
1. Create the Jira story (and optionally subtasks):
- Use the **custom_jira** (or **user-custom-jira**) MCP server:
  - **create_issue**: `project_key` = your Jira project key (e.g. `PROJ`), `summary` = "Design a URL shorten system using Fast API", `issue_type` = "Story", `description` = optional (e.g. scope, acceptance criteria). Capture the returned issue key (e.g. `PROJ-42`).
- **Optional – subtasks**: If the story has subtasks, for each one use **create_sub_task** with `parent_issue_key` = the story key, `project_key`, `summary`, and optional `description`. If the story has no subtasks, skip this.

// turbo
2. Create a feature branch using the Jira issue key:
- Use the issue key from step 1 for the branch name (e.g. `PROJ-42`). If no ticket was created, use `story/url-shorten`.
```bash
git checkout -b <ISSUE_KEY>
```
Example: `git checkout -b PROJ-42`

3. Implement the URL shortener system using FastAPI:
- Create a FastAPI application (e.g. `url_shortener/main.py`) with:
  - **POST /shorten** – accept a long URL, generate a short code, store the mapping, return the short URL.
  - **GET /{short_code}** – redirect to the original URL (302) or return 404 if not found.
  - Optional: **GET /urls** – list stored mappings (for demo/admin); **DELETE /{short_code}** – remove a mapping.
- Use in-memory storage (e.g. dict) or a simple persistence (SQLite/JSON file) for the short_code → long_url mapping.
- Generate short codes (e.g. base62 or random string of fixed length); ensure uniqueness.
- Add basic validation (valid URL format, optional length limits).

4. Create unit tests (e.g. `tests/test_url_shortener.py`) using FastAPI's `TestClient`:
- Test POST /shorten returns 200 and a short URL.
- Test GET /{short_code} redirects to the original URL.
- Test GET for unknown code returns 404.
- Optionally test duplicate long URL handling and invalid input (422).

// turbo
5. Run tests to ensure everything works:
```bash
pytest tests/test_url_shortener.py -v
```

6. Once tests pass, commit and push (use the same branch name as in step 2):
```bash
git add .
git commit -m "<ISSUE_KEY>: URL shortener system with FastAPI (shorten, redirect, tests)"
git push origin <ISSUE_KEY>
```
Example: `git commit -m "PROJ-42: URL shortener system with FastAPI (shorten, redirect, tests)"` and `git push origin PROJ-42`.

// turbo
7. Create a Pull Request:
- Use the **custom_github** (or **user-custom-github**) MCP server: **github_create_pull_request** with `head_branch` = `<ISSUE_KEY>`, `title` and `body` describing the change. Note the PR number or URL.

// turbo
8. Check that the PR exists and run PR review:
- **Check PR**: Use **github_check_pr_exists** with `head_branch` = `<ISSUE_KEY>` to confirm the PR exists. If needed, use **github_list_pull_requests** to get the `pull_number` for the branch.
- **Run AI code review and add comments on the PR** (choose one approach):
  - **Preferred (if pr-manager MCP is configured)**: Use the **pr-manager** MCP tool **validate_review_and_comment_on_pr** with `branch_name` = `<ISSUE_KEY>`, `base_branch` = `main`, `run_tests` = `true`, `test_command` = `pytest tests/test_url_shortener.py -v`, `post_to_github` = `true`. This runs tests, performs an AI code review, and posts the review summary plus inline comments on the PR.
  - **Otherwise**: Use **github_get_pull_request** (with the PR number) to review the PR, then **github_add_pr_review** with `pull_number`, `body` = your review summary (and optionally inline comments), and `event` = `COMMENT` or `REQUEST_CHANGES` to add the review and comments on the PR.
- **Verify**: Use **github_list_pr_comments** (or list review comments) to confirm the review/feedback was added to the PR.

9. Review the PR (human or AI):
- Read the PR diff and any review comments.
- Address feedback: fix code or tests if needed, push new commits, and re-run the review step if desired.
- When satisfied, the PR can be merged (via GitHub UI or **github_merge_pull_request** MCP when appropriate).
