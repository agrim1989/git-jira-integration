# Social Media Application — Workflow Design

Generated for workflow-server. Use with `_agent/workflows/social-media-application-workflow.md` for full step-by-step execution.

---

## Problem statement

Build a Social Media Application that allows users to register, maintain profiles, create and view posts, interact via likes and comments, and consume a timeline feed. The system should be implementable as a REST API with optional persistence (in-memory or SQLite).

## Functional requirements

- **Users & profiles:** Register/login (or simple user creation); profile with display name, bio, optional avatar URL; get/update own profile.
- **Posts:** Create post (text, optional media URL); list posts (feed) with pagination; get single post; delete own post.
- **Feed:** Timeline of posts (all users or from followed users); sort by date (newest first); pagination (limit/offset or cursor).
- **Interactions:** Like/unlike a post; add comment to a post; list comments for a post; optional: reply to comment.
- **Optional:** Follow/unfollow users; feed filtered to followed users only; media upload or URL-only.

## Non-functional requirements

- REST API (FastAPI or equivalent); clear API contracts.
- In-memory or SQLite persistence; no hardcoded secrets; config via env.
- Logging, error handling, docstrings; PEP8-compliant code.
- Unit tests with FastAPI TestClient; tests must pass before PR.

## Architecture / design

- **Module layout:** e.g. `social_media/` or `social/` with models, store (in-memory dict or SQLite), and API routes; separate `main.py` or `app.py` for FastAPI app.
- **Data:** User (id, username, display_name, bio, avatar_url, created_at); Post (id, user_id, content, media_url, created_at); Like (user_id, post_id); Comment (id, post_id, user_id, body, created_at, parent_id optional).
- **API:** POST/GET /users, GET/PATCH /users/me; POST/GET /posts, GET /posts/{id}, DELETE /posts/{id}; GET /feed; POST/DELETE /posts/{id}/like; POST/GET /posts/{id}/comments. Auth: simple API key or session for scope; optional JWT later.

## Implementation plan

1. Set up FastAPI app and project structure (`social_media/`, `tests/`).
2. Implement user model and store; registration and get profile endpoints.
3. Implement post model and store; create, list, get, delete post endpoints.
4. Implement feed (timeline) with pagination.
5. Implement likes (like/unlike) and comments (add, list).
6. Add validation, error handling, logging; requirements.txt and config.
7. Write unit tests for all main flows; run pytest and fix until green.

## Testing plan

- Unit tests: user registration and get profile; create post, list feed, get single post, delete post; like/unlike; add comment, list comments; auth/authorization (e.g. cannot delete another user’s post).
- Use FastAPI `TestClient`; target `tests/test_social_media.py` (or equivalent).
- Command: `pytest tests/test_social_media.py -v`. All tests must pass before commit and PR.

## Deployment plan

- Run locally: `uvicorn` with host/port from config; optional Dockerfile later.
- Env: database path or in-memory flag; secret key if auth added; no secrets in repo.

## Risks & mitigation

- Scope creep: stick to core features (profiles, posts, feed, likes, comments) first; follow/unfollow and media upload as optional.
- Persistence: start with in-memory; migrate to SQLite if needed without changing API contract.

## Rollback strategy

- Feature developed on branch; if issues, do not merge PR; fix on same branch or revert commits. No production deployment until PR is merged and verified.
