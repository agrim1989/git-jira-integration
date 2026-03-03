---
description: Workflow-server workflow for designing a Dropbox-like system. File upload, download, storage, folders, sharing, optional versioning. Uses custom-jira, custom-github, local-llm. Create workflow doc, Jira ticket, code, branch, PR, review, update Jira.
---

# Dropbox-like System — Workflow

This workflow is designed to be run by the **workflow-server** (or workflow-agent). It uses **custom-jira**, **custom-github**, and **local-llm** (or editor-agent fallback). Do not skip steps; stop on failure; return JSON after every step.

---

## STEP 1 — Create /docs/workflow.md (Dropbox design)

**Tool:** local-llm (prefer) else editor-agent.

Generate and save workflow design for the Dropbox system. Use the content in **`docs/workflow-dropbox.md`** (already created) or generate equivalent with these sections:

- **Problem statement:** Design a Dropbox-like system (upload, download, storage, sync, sharing, optional versioning).
- **Functional requirements:** File upload/download, folders & hierarchy, sharing (links), optional versioning, auth.
- **Non-functional requirements:** REST API (FastAPI), configurable storage (local/S3), no secrets in code, tests.
- **Architecture / design:** Module layout (`dropbox/` or `file_storage/`), metadata store, storage backend, API endpoints, auth.
- **Implementation plan:** Steps 1–8 (auth, metadata, upload/download, list, folders, sharing, optional versioning, tests).
- **Testing plan:** Unit tests for auth, upload, download, list, share; `pytest tests/test_dropbox.py -v`.
- **Deployment plan:** Local run with config; env for storage path/S3, DB, secret key.
- **Risks & mitigation:** Large files (streaming, max size); scope (core first, versioning optional).
- **Rollback strategy:** Feature on branch; no production until PR merged and verified.

Reference doc: **`docs/workflow-dropbox.md`**.

---

## STEP 2 — Create Jira ticket

**Tool:** custom-jira.

- **create_issue:** `project_key` = your Jira project (e.g. `KAN`), `summary` = "Design a Dropbox-like system (file upload, download, storage, sharing)", `issue_type` = "Story", `description` = summary from workflow doc (problem statement + key requirements).
- Store: **JIRA_ID** (e.g. KAN-80), **JIRA_URL**.

Output: `{"step": "STEP_2", "status": "SUCCESS", "artifacts": {"jira_id": "KAN-80", "jira_url": "..."}}`

---

## STEP 3 — Generate production code

**Tool:** local-llm (prefer) else code-editor-agent.

- Generate code per Implementation plan in `docs/workflow-dropbox.md`: FastAPI app, `dropbox/` or `file_storage/` module (models, storage backend, metadata store, routes), auth, upload/download (streaming), list, folders, sharing; `requirements.txt`, config, logging, error handling, docstrings, PEP8, no secrets in code.
- Place under repo (e.g. `dropbox/` and `tests/test_dropbox.py`).

---

## STEP 4 — Branch naming

**Rule:** Branch name must be `feature/<JIRA-ID>-<short-desc>`: start with `feature/`, include JIRA-ID, lowercase, hyphen-separated, max 50 chars. No spaces.

- Example: `feature/kan-80-dropbox-system`
- **Tool:** validate_branch_name (workflow-server). If invalid, regenerate name and do not proceed.

---

## STEP 5 — Push to GitHub

**Tool:** custom-github (or git execute).

- Create branch (from step 4), commit message: `"<JIRA_ID>: Initial implementation"`, push.
- Store: **branch** name, branch URL.

Output: `{"step": "STEP_5", "status": "SUCCESS", "artifacts": {"branch": "feature/kan-80-dropbox-system", ...}}`

---

## STEP 6 — Create PR

**Tool:** custom-github.

- **github_create_pull_request:** `head_branch` = branch from step 4, `title` = "<JIRA_ID>: Design Dropbox-like system (upload, download, storage, sharing)", `body` = summary + implementation details + Jira URL; base = `main`.
- Store: **PR_ID**, **PR_URL**.

---

## STEP 7 — Assign PR reviewers

**Tool:** custom-github.

- Use CODEOWNERS or assign at least 2 reviewers; avoid self-review. Store reviewers list. (If MCP has no assign tool, assign in GitHub UI.)

---

## STEP 8 — Review PR (optional)

- Ask user: review PR? If **YES:** fetch diff (custom-github), analyze (local-llm or editor-agent), post comments (custom-github). If **NO:** continue.
- Preferred: run tests (`pytest tests/test_dropbox.py -v`), then add PR review (e.g. **github_add_pr_review** with body and event COMMENT or REQUEST_CHANGES).

---

## STEP 9 — On PR merged: update Jira

**Tool:** custom-jira.

- Add comment to Jira issue: PR Merged, branch name, summary, PR URL, reviewers, review summary, merge timestamp.
- Transition issue to Done / Closed / Ready for QA as per project workflow.

Output: `{"step": "STEP_9", "status": "SUCCESS", "artifacts": {"jira_id": "...", "pr_url": "...", "reviewers": [...]}}`

---

## Workflow completion

Workflow is complete only when:

- Workflow design doc created (STEP 1; ref: `docs/workflow-dropbox.md`)
- Jira ticket created (STEP 2)
- Code generated and tests pass (STEP 3)
- Branch created and pushed (STEP 4, 5)
- PR created and reviewers assigned (STEP 6, 7)
- Review handled if requested (STEP 8)
- Jira updated with PR details and merge status (STEP 9)

## How to run

### Run at once (end-to-end)

1. In Cursor, open AI chat; use **GitHub-Jira** or **GitHub & Jira MCP Integration** agent if available.
2. Prompt: *"Run the full workflow from _agent/workflows/dropbox-system-workflow.md from STEP 1 through STEP 9. Do not skip steps; stop on failure."*
3. Or: *"Execute the Dropbox system workflow end-to-end using custom-jira and custom-github."*
4. Prerequisites: **user-custom-jira**, **user-custom-github**, **user-workflow-server** (and optionally **user-local-llm**) enabled in Cursor → Settings → Tools & MCP.

### Run step-by-step

- *"Do step 1 of the dropbox-system-workflow"*, then *"Do step 2 with project key KAN"*, etc.
- On failure: `{"step": "STEP_N", "status": "FAILED", "reason": "...", "next_action": "..."}`.
