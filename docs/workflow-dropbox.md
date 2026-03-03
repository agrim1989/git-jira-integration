# Dropbox-like System — Workflow Design

Generated for workflow-server. Use with `_agent/workflows/dropbox-system-workflow.md` for full step-by-step execution.

---

## Problem statement

Design a Dropbox-like system that enables file upload, download, storage management, synchronization across devices or platforms, sharing capabilities, and optional versioning. The service should use FastAPI as the backend, support local disk or S3-compatible storage and a metadata store (DB or SQLite), and include user authentication.

## Functional requirements

- **File upload:** Users can upload files up to a configurable max size; auth required for uploads to their space.
- **File download:** Users can download or stream their files and shared files they have access to.
- **Storage & metadata:** Store files on local disk or S3-compatible storage; metadata (path, owner, size, mime type, created/updated) in DB or SQLite.
- **Folders & hierarchy:** Create folders; list directory contents; navigate path-based hierarchy (e.g. `/me/docs`, `/me/photos`).
- **Sharing:** Share a file or folder via link (public or token-based); optional expiry; list shared items.
- **Optional versioning:** Keep previous versions of a file; list versions; restore a version.
- **Auth:** User registration/login; per-request auth (API key or JWT); scope access by user and shared links.

## Non-functional requirements

- REST API (FastAPI); clear contracts; streaming for large file upload/download.
- Configurable storage backend (local path or S3); no hardcoded secrets; config via env.
- Logging, error handling, docstrings; PEP8-compliant code.
- Unit tests with FastAPI TestClient; tests must pass before PR.

## Architecture / design

- **Module layout:** e.g. `dropbox/` or `file_storage/` with models, storage backend (local/S3), metadata store, and API routes; `main.py` for FastAPI app.
- **Data:** User (id, username, created_at); FileMetadata (id, path, owner_id, size, content_type, version, created_at, updated_at); Share (id, resource_path, token, expires_at, created_at). Optional: Version (file_id, version_number, stored_path, created_at).
- **Storage:** Files on disk under `storage/<owner_id>/<path>` or in S3 bucket with key prefix; metadata in SQLite or DB.
- **API:** POST /files/upload (multipart), GET /files/download/{path}, GET /files/list?path=, POST /files/folder, DELETE /files/{path}; POST /share (create link), GET /share/{token} (resolve); optional GET /files/{path}/versions, POST /files/{path}/restore?version=.
- **Auth:** API key or JWT in header; middleware to resolve user and enforce path ownership or share access.

## Implementation plan

1. Set up FastAPI app and project structure (`dropbox/` or `file_storage/`, `tests/`).
2. Implement user model and auth (register, login, API key or JWT); middleware for current user.
3. Implement metadata store (SQLite) and storage backend interface (local disk first).
4. Implement file upload (multipart), download (streaming), list directory, create folder, delete file/folder.
5. Implement sharing: generate token, store share record, resolve token to file path and allow read/download.
6. Optional: versioning on overwrite; list versions; restore.
7. Add validation, size limits, error handling, logging; requirements.txt and config.
8. Write unit tests for upload, download, list, share, auth; run pytest until green.

## Testing plan

- Unit tests: auth (missing/invalid token returns 401); upload file and verify metadata; download file; list directory; create folder; delete file; create share link and access via token; optional version list/restore.
- Use FastAPI TestClient; target `tests/test_dropbox.py` (or equivalent). Mock or use temp directory for storage.
- Command: `pytest tests/test_dropbox.py -v`. All tests must pass before commit and PR.

## Deployment plan

- Run locally: `uvicorn` with host/port from config; storage path or S3 credentials in env; optional Dockerfile.
- Env: storage path or S3 bucket/region, DB path, secret key for JWT, max file size; no secrets in repo.

## Risks & mitigation

- Large files: enforce max size and streaming to avoid memory exhaustion.
- Scope creep: deliver core (upload, download, list, folders, sharing) first; versioning and sync as optional.
- Storage: start with local disk; abstract interface so S3 can be swapped in later.

## Rollback strategy

- Feature on branch; if issues, do not merge PR; fix on branch or revert. No production deployment until PR is merged and verified.
