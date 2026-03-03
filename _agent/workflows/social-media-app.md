---
description: Workflow for Social Media Application - Design and implement a social media app (profiles, posts, feed, likes, comments)
---

This workflow automates Jira ticket creation, development, testing, PR creation, and PR review for the Social Media Application story. The story may or may not have subtasks.

## How to run this workflow

**Option A – In Cursor (AI / workflow-agent)**  
Open the AI chat and ask it to run the workflow. Example prompts:
- *"Run the social-media-app workflow from _agent/workflows/social-media-app.md"*
- *"Execute all steps of the Social Media Application workflow"*
- Or run step-by-step: *"Do step 1 of the social-media-app workflow"* then *"Do step 2 with issue key KAN-72"*, etc.

The AI will use **custom_jira** and **custom_github** MCP servers for steps 1, 2, 7, 8 and run git/test commands for the rest. Ensure Jira and GitHub MCPs are enabled in Cursor (Settings → Tools & MCP).

**Option B – Manually**  
1. **Step 1:** In Jira create a Story, or in Cursor ask: *"Create a Jira story for Social Media Application using custom-jira"*. Note the issue key (e.g. `KAN-72`).  
2. **Step 2:** Run `git checkout -b <ISSUE_KEY>` (replace with your key).  
3. **Steps 3–4:** Implement the app and tests in your repo (e.g. `social_media/`, `tests/test_social_media.py`).  
4. **Step 5:** Run `pytest tests/test_social_media.py -v`.  
5. **Step 6:** `git add .` → `git commit -m "<ISSUE_KEY>: Social media application (...)"` → `git push origin <ISSUE_KEY>`.  
6. **Step 7:** In Cursor ask *"Create a PR for branch <ISSUE_KEY> using custom-github"* or create the PR on GitHub.  
7. **Step 8:** Check PR exists, run code review (pr-manager or add review via GitHub MCP), verify comments.  
8. **Step 9:** Address feedback and merge when ready.

**Prerequisites:** Jira and GitHub MCP servers configured in Cursor; repo clone with `main` (or default branch) up to date.

---

// turbo
1. Create the Jira story (and optionally subtasks):
- Use the **custom_jira** (or **user-custom-jira**) MCP server:
  - **create_issue**: `project_key` = your Jira project key (e.g. `PROJ`), `summary` = "Design and implement a Social Media Application", `issue_type` = "Story", `description` = optional (e.g. scope below). Capture the returned issue key (e.g. `PROJ-42`).
- **Optional – subtasks**: If the story has subtasks, for each one use **create_sub_task** with `parent_issue_key` = the story key, `project_key`, `summary`, and optional `description`. If the story has no subtasks, skip this.

// turbo
2. Create a feature branch using the Jira issue key:
- Use the issue key from step 1 for the branch name (e.g. `PROJ-42`). If no ticket was created, use `story/social-media-app`.
```bash
git checkout -b <ISSUE_KEY>
```
Example: `git checkout -b PROJ-42`

3. Implement the Social Media Application:
- **Scope (suggested):**
  - **Users & profiles**: Register/login (or simple user with profile); display name, bio, avatar URL (optional).
  - **Posts**: Create post (text, optional media URL); list posts (feed) with pagination; get single post; delete own post.
  - **Feed**: Timeline of posts (e.g. from all users or from followed users); sort by date (newest first).
  - **Interactions**: Like/unlike a post; add comment to a post; list comments for a post; optional: reply to comment.
  - **Optional**: Follow/unfollow users; feed = posts from followed users only; media upload or URL-only.
- **Tech**: FastAPI (or chosen stack); in-memory or SQLite/DB store; REST API; optional WebSocket for real-time feed updates.
- **Structure**: e.g. `social/` or `social_media/` module with models, store, and API routes; keep tests in `tests/test_social_media.py` (or similar).

4. Create unit tests (e.g. `tests/test_social_media.py`) using FastAPI's `TestClient`:
- Test user registration and get profile.
- Test create post, list feed, get single post.
- Test like/unlike, add comment, list comments.
- Test delete post and authorization (e.g. cannot delete another user's post).
- Optionally test follow/unfollow and filtered feed.

// turbo
5. Run tests to ensure everything works:
```bash
pytest tests/test_social_media.py -v
```

6. Once tests pass, commit and push (use the same branch name as in step 2):
```bash
git add .
git commit -m "<ISSUE_KEY>: Social media application (profiles, posts, feed, likes, comments)"
git push origin <ISSUE_KEY>
```
Example: `git commit -m "PROJ-42: Social media application (profiles, posts, feed, likes, comments)"` and `git push origin PROJ-42`.

// turbo
7. Create a Pull Request:
- Use the **custom_github** (or **user-custom-github**) MCP server: **github_create_pull_request** with `head_branch` = `<ISSUE_KEY>`, `title` and `body` describing the change. Note the PR number or URL.

// turbo
8. Check that the PR exists and run PR review:
- **Check PR**: Use **github_check_pr_exists** with `head_branch` = `<ISSUE_KEY>` to confirm the PR exists. If needed, use **github_list_pull_requests** to get the `pull_number` for the branch.
- **Run AI code review and add comments on the PR** (choose one approach):
  - **Preferred (if pr-manager MCP is configured)**: Use the **pr-manager** MCP tool **validate_review_and_comment_on_pr** with `branch_name` = `<ISSUE_KEY>`, `base_branch` = `main`, `run_tests` = `true`, `test_command` = `pytest tests/test_social_media.py -v`, `post_to_github` = `true`. This runs tests, performs an AI code review, and posts the review summary plus inline comments on the PR.
  - **Otherwise**: Use **github_get_pull_request** (with the PR number) to review the PR, then **github_add_pr_review** with `pull_number`, `body` = your review summary, and `event` = `COMMENT` or `REQUEST_CHANGES` to add the review and comments on the PR.
- **Verify**: Use **github_list_pr_comments** to confirm the review/feedback was added to the PR.

9. Review the PR (human or AI):
- Read the PR diff and any review comments.
- Address feedback: fix code or tests if needed, push new commits, and re-run the review step if desired.
- When satisfied, the PR can be merged (via GitHub UI or **github_merge_pull_request** MCP when appropriate).
