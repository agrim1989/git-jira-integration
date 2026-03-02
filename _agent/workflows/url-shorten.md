---
description: Workflow for URL Shortener - Design a URL shorten system using FastAPI
---

This workflow automates the development, testing, and PR creation for the URL shortener story (design a URL shorten system using Fast API).

// turbo
1. Create a new feature branch for the URL shortener story:
```bash
git checkout -b story/url-shorten
```

2. Implement the URL shortener system using FastAPI:
- Create a FastAPI application (e.g. `app/main.py` or `url_shortener/main.py`) with:
  - **POST /shorten** – accept a long URL, generate a short code, store the mapping, return the short URL.
  - **GET /{short_code}** – redirect to the original URL (302) or return 404 if not found.
  - Optional: **GET /urls** – list stored mappings (for demo/admin); **DELETE /{short_code}** – remove a mapping.
- Use in-memory storage (e.g. dict) or a simple persistence (SQLite/JSON file) for the short_code → long_url mapping.
- Generate short codes (e.g. base62 or random string of fixed length); ensure uniqueness.
- Add basic validation (valid URL format, optional length limits).

3. Create unit tests (e.g. `tests/test_url_shortener.py`) using `httpx.ASGITransport` and FastAPI's `TestClient` or `pytest-asyncio`:
- Test POST /shorten returns 200 and a short URL.
- Test GET /{short_code} redirects to the original URL.
- Test GET for unknown code returns 404.
- Optionally test duplicate long URL handling and invalid input (400).

// turbo
4. Run tests to ensure everything works:
```bash
pytest tests/test_url_shortener.py -v
```

5. Once tests pass, commit and push the changes:
```bash
git add .
git commit -m "story: URL shortener system with FastAPI (shorten, redirect, tests)"
git push origin story/url-shorten
```

6. Create a Pull Request using the MCP (e.g. `custom_github` or configured GitHub MCP server).

7. Optional: Run an automated AI code review via the `pr-manager` MCP server using the tool with `branch_name="story/url-shorten"` to validate the implementation and post feedback.
