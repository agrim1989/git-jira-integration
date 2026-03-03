---
description: Workflow-server workflow for designing an Amazon-like e-commerce marketplace. Product catalog, search, cart, checkout, orders, user accounts. Uses custom-jira, custom-github, local-llm. Create workflow doc, Jira ticket, code, branch, PR, review, update Jira.
---

# Amazon-like E-commerce Marketplace — Workflow

This workflow is designed to be run by the **workflow-server** (or workflow-agent). It uses **custom-jira**, **custom-github**, and **local-llm** (or editor-agent fallback). Do not skip steps; stop on failure; return JSON after every step.

---

## STEP 1 — Create workflow design (Amazon)

**Tool:** local-llm (prefer) else editor-agent.

Use the content in **`docs/workflow-amazon.md`** (already created) or generate equivalent with:

- **Problem statement:** Design an Amazon-like marketplace (catalog, cart, checkout, orders, user accounts).
- **Functional requirements:** User accounts, product catalog, cart, checkout & orders; optional sellers, inventory, reviews.
- **Non-functional requirements:** REST API (FastAPI), in-memory or SQLite, no secrets in code, tests.
- **Architecture / design:** Module layout (`marketplace/` or `amazon/`), data models, API endpoints, auth.
- **Implementation plan:** Steps 1–8 (auth, products, cart, checkout, orders, tests; optional sellers/reviews).
- **Testing plan:** Unit tests for auth, products, cart, checkout, orders; `pytest tests/test_amazon.py -v`.
- **Deployment plan:** Local run; env for DB/secret; no secrets in repo.
- **Risks & mitigation:** Scope (core first); concurrency (MVP in-memory/SQLite).
- **Rollback strategy:** Feature on branch; no production until PR merged.

Reference doc: **`docs/workflow-amazon.md`**.

---

## STEP 2 — Create Jira ticket

**Tool:** custom-jira.

- **create_issue:** `project_key` = your Jira project (e.g. `KAN`), `summary` = "Design Amazon-like e-commerce marketplace (catalog, cart, checkout, orders)", `issue_type` = "Story", `description` = summary from workflow doc (problem statement + key requirements).
- Store: **JIRA_ID** (e.g. KAN-81), **JIRA_URL**.

Output: `{"step": "STEP_2", "status": "SUCCESS", "artifacts": {"jira_id": "KAN-81", "jira_url": "..."}}`

---

## STEP 3 — Generate production code

**Tool:** local-llm (prefer) else code-editor-agent.

- Generate code per Implementation plan in `docs/workflow-amazon.md`: FastAPI app, `marketplace/` or `amazon/` module (models, store, routes), auth, products (list, get, filter, search), cart (add, list, update, remove), checkout (create order, clear cart), orders (list, get); `requirements.txt`, config, logging, error handling, docstrings, PEP8, no secrets in code.
- Place under repo (e.g. `marketplace/` and `tests/test_amazon.py`).

---

## STEP 4 — Branch naming

**Rule:** Branch name must be `feature/<JIRA-ID>-<short-desc>`: start with `feature/`, include JIRA-ID, lowercase, hyphen-separated, max 50 chars. No spaces.

- Example: `feature/kan-81-amazon-marketplace`
- **Tool:** validate_branch_name (workflow-server). If invalid, regenerate name and do not proceed.

---

## STEP 5 — Push to GitHub

**Tool:** custom-github (or git execute).

- Create branch (from step 4), commit message: `"<JIRA_ID>: Initial implementation"`, push.
- Store: **branch** name, branch URL.

---

## STEP 6 — Create PR

**Tool:** custom-github.

- **github_create_pull_request:** `head_branch` = branch from step 4, `title` = "<JIRA_ID>: Design Amazon-like marketplace (catalog, cart, checkout, orders)", `body` = summary + implementation details + Jira URL; base = `main`.
- Store: **PR_ID**, **PR_URL**.

---

## STEP 7 — Assign PR reviewers

**Tool:** custom-github.

- Use CODEOWNERS or assign reviewers; avoid self-review. (If MCP has no assign tool, assign in GitHub UI.)

---

## STEP 8 — Review PR (optional)

- Ask user: review PR? If **YES:** fetch diff (custom-github), analyze (local-llm or editor-agent), post comments (custom-github). If **NO:** continue.
- Preferred: run tests (`pytest tests/test_amazon.py -v`), then add PR review (e.g. **github_add_pr_review** with body and event COMMENT or REQUEST_CHANGES).

---

## STEP 9 — On PR merged: update Jira

**Tool:** custom-jira.

- Add comment to Jira issue: PR Merged, branch name, summary, PR URL, reviewers, review summary, merge timestamp.
- Transition issue to Done / Closed / Ready for QA as per project workflow.

---

## Workflow completion

Complete only when: workflow design doc (STEP 1), Jira ticket (STEP 2), code and tests (STEP 3), branch pushed (STEP 4–5), PR created and reviewers assigned (STEP 6–7), review handled if requested (STEP 8), Jira updated with PR and merge status (STEP 9).

## How to run

### Run at once (end-to-end)

1. In Cursor, open AI chat; use **GitHub-Jira** or **GitHub & Jira MCP Integration** agent if available.
2. Prompt: *"Run the full workflow from _agent/workflows/amazon-workflow.md from STEP 1 through STEP 9. Do not skip steps; stop on failure."*
3. Or: *"Execute the Amazon marketplace workflow end-to-end using custom-jira and custom-github."*
4. Prerequisites: **user-custom-jira**, **user-custom-github**, **user-workflow-server** (and optionally **user-local-llm**) enabled in Cursor → Settings → Tools & MCP.

### Run step-by-step

- *"Do step 1 of the amazon-workflow"*, then *"Do step 2 with project key KAN"*, etc.
- On failure: `{"step": "STEP_N", "status": "FAILED", "reason": "...", "next_action": "..."}`.
