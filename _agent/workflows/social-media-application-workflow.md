---
description: Workflow-server workflow for building a Social Media Application. Follows global workflow rules (custom-jira, custom-github, local-llm). Create workflow.md, Jira ticket, code, branch, PR, review, update Jira.
---

# Social Media Application — Workflow

This workflow is designed to be run by the **workflow-server** (or workflow-agent). It uses **custom-jira**, **custom-github**, and **local-llm** (or editor-agent fallback). Do not skip steps; stop on failure; return JSON after every step.

---

## STEP 1 — Create /docs/workflow.md

**Tool:** local-llm (prefer) else editor-agent.

Generate and save `/docs/workflow.md` with the following sections.

### Problem statement

Build a Social Media Application that allows users to register, maintain profiles, create and view posts, interact via likes and comments, and consume a timeline feed. The system should be implementable as a REST API with optional persistence (in-memory or SQLite).

### Functional requirements

- **Users & profiles:** Register/login (or simple user creation); profile with display name, bio, optional avatar URL; get/update own profile.
- **Posts:** Create post (text, optional media URL); list posts (feed) with pagination; get single post; delete own post.
- **Feed:** Timeline of posts (all users or from followed users); sort by date (newest first); pagination (limit/offset or cursor).
- **Interactions:** Like/unlike a post; add comment to a post; list comments for a post; optional: reply to comment.
- **Optional:** Follow/unfollow users; feed filtered to followed users only; media upload or URL-only.

### Non-functional requirements

- REST API (FastAPI or equivalent); clear API contracts.
- In-memory or SQLite persistence; no hardcoded secrets; config via env.
- Logging, error handling, docstrings; PEP8-compliant code.
- Unit tests with FastAPI TestClient; tests must pass before PR.

### Architecture / design

- **Module layout:** e.g. `social_media/` or `social/` with models, store (in-memory dict or SQLite), and API routes; separate `main.py` or `app.py` for FastAPI app.
- **Data:** User (id, username, display_name, bio, avatar_url, created_at); Post (id, user_id, content, media_url, created_at); Like (user_id, post_id); Comment (id, post_id, user_id, body, created_at, parent_id optional).
- **API:** POST/GET /users, GET/PATCH /users/me; POST/GET /posts, GET /posts/{id}, DELETE /posts/{id}; GET /feed; POST/DELETE /posts/{id}/like; POST/GET /posts/{id}/comments. Auth: simple API key or session for scope; optional JWT later.

### Implementation plan

1. Set up FastAPI app and project structure (`social_media/`, `tests/`).
2. Implement user model and store; registration and get profile endpoints.
3. Implement post model and store; create, list, get, delete post endpoints.
4. Implement feed (timeline) with pagination.
5. Implement likes (like/unlike) and comments (add, list).
6. Add validation, error handling, logging; requirements.txt and config.
7. Write unit tests for all main flows; run pytest and fix until green.

### Testing plan

- Unit tests: user registration and get profile; create post, list feed, get single post, delete post; like/unlike; add comment, list comments; auth/authorization (e.g. cannot delete another user’s post).
- Use FastAPI `TestClient`; target `tests/test_social_media.py` (or equivalent).
- Command: `pytest tests/test_social_media.py -v`. All tests must pass before commit and PR.

### Deployment plan

- Run locally: `uvicorn` with host/port from config; optional Dockerfile later.
- Env: database path or in-memory flag; secret key if auth added; no secrets in repo.

### Risks & mitigation

- Scope creep: stick to core features (profiles, posts, feed, likes, comments) first; follow/unfollow and media upload as optional.
- Persistence: start with in-memory; migrate to SQLite if needed without changing API contract.

### Rollback strategy

- Feature developed on branch; if issues, do not merge PR; fix on same branch or revert commits. No production deployment until PR is merged and verified.

---

## STEP 2 — Create Jira ticket

**Tool:** custom-jira.

- **create_issue:** `project_key` = your Jira project (e.g. `KAN`), `summary` = "Design and implement a Social Media Application", `issue_type` = "Story", `description` = link to or paste summary from workflow.md (problem statement + key requirements).
- Store: **JIRA_ID** (e.g. KAN-72), **JIRA_URL**.

Output: `{"step": "STEP_2", "status": "SUCCESS", "artifacts": {"jira_id": "KAN-72", "jira_url": "..."}}`

---

## STEP 3 — Generate production code

**Tool:** local-llm (prefer) else code-editor-agent.

- Generate code per Implementation plan: FastAPI app, `social_media/` module (models, store, routes), `requirements.txt`, config, logging, error handling, docstrings, PEP8, no secrets in code.
- Place under repo (e.g. `social_media/` and `tests/test_social_media.py`).

---

## STEP 4 — Branch naming

**Rule:** Branch name must be `feature/<JIRA-ID>-<short-desc>`: start with `feature/`, include JIRA-ID, lowercase, hyphen-separated, max 50 chars. No spaces.

- Example: `feature/kan-72-social-media-app`
- **Tool:** validate_branch_name (workflow-server). If invalid, regenerate name and do not proceed.

---

## STEP 5 — Push to GitHub

**Tool:** custom-github.

- Create branch (from step 4), commit message: `"<JIRA_ID>: Initial implementation"`, push.
- Store: **branch** name, branch URL.

Output: `{"step": "STEP_5", "status": "SUCCESS", "artifacts": {"branch": "feature/kan-72-social-media-app", ...}}`

---

## STEP 6 — Create PR

**Tool:** custom-github.

- **github_create_pull_request:** `head_branch` = branch from step 4, `title` = "<JIRA_ID>: Design and implement Social Media Application", `body` = summary + implementation details + Jira URL; base = `main`.
- Store: **PR_ID**, **PR_URL**.

---

## STEP 7 — Assign PR reviewers

**Tool:** custom-github.

- Use CODEOWNERS or assign at least 2 reviewers; avoid self-review. Store reviewers list.

---

## STEP 8 — Review PR (optional)

- Ask user: review PR? If **YES:** fetch diff (custom-github), analyze (local-llm or editor-agent), post comments (custom-github). If **NO:** continue.
- Preferred: run tests (`pytest tests/test_social_media.py -v`), then add PR review (e.g. **github_add_pr_review** with body and event COMMENT or REQUEST_CHANGES).

---

## STEP 9 — On PR merged: update Jira

**Tool:** custom-jira.

- Add comment to Jira issue: PR Merged, branch name, summary, PR URL, reviewers, review summary, merge timestamp.
- Transition issue to Done / Closed / Ready for QA as per project workflow.

Output: `{"step": "STEP_9", "status": "SUCCESS", "artifacts": {"jira_id": "...", "pr_url": "...", "reviewers": [...]}}`

---

## Workflow completion

Workflow is complete only when:

- `/docs/workflow.md` created (STEP 1)
- Jira ticket created (STEP 2)
- Code generated and tests pass (STEP 3, Testing plan)
- Branch created and pushed (STEP 4, 5)
- PR created and reviewers assigned (STEP 6, 7)
- Review handled if requested (STEP 8)
- Jira updated with PR details and merge status (STEP 9)

## How to run

### Run the workflow at once (end-to-end)

1. **In Cursor:** Open AI chat, choose the **GitHub-Jira** or **GitHub & Jira MCP Integration** agent (or leave default).
2. **One-shot prompt:** Paste one of these and send:
   - *"Run the full workflow from _agent/workflows/social-media-application-workflow.md from STEP 1 through STEP 9. Do not skip steps; stop on failure."*
   - *"Execute the entire social-media-application-workflow at once: create workflow.md, Jira ticket, generate code, create branch, push, create PR, assign reviewers, then update Jira when merged."*
   - *"Run the Social Media Application workflow end-to-end using custom-jira and custom-github."*
3. The AI will run STEP 1 → STEP 9 in order, using **custom-jira**, **custom-github**, and (if available) **local-llm** or editor-agent. It will stop and report if any step fails.
4. **Prerequisites:** In Cursor go to **Settings → Tools & MCP** and ensure **user-custom-jira**, **user-custom-github**, and **user-workflow-server** (and optionally **user-local-llm**) are enabled and have valid credentials.

### Run step-by-step

- *"Do step 1 of the social-media-application-workflow"*, then *"Do step 2 with project key KAN"*, etc.
- Or follow STEP 1–9 manually in the doc; use the tools indicated; on failure report: `{"step": "STEP_N", "status": "FAILED", "reason": "...", "next_action": "..."}`.
