"""Generate code and test files from Jira ticket + solution using Groq."""
import json
import re

import httpx

from app.config import settings
from app.models import TicketDetail
from app.services.jira_service import ticket_to_context_string

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(system: str, user: str) -> str:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set")
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key.strip()}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"Groq API error {r.status_code}: {r.text}")
        data = r.json()
    choices = data.get("choices") or []
    if not choices:
        return ""
    return (choices[0].get("message") or {}).get("content") or ""


def _parse_files_json(raw: str) -> list[dict]:
    """Extract JSON with 'files' array from model output; strip markdown code fences."""
    text = (raw or "").strip()
    # Remove markdown code block
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        data = {}
    files = data.get("files") if isinstance(data, dict) else None
    if isinstance(files, list):
        return [f for f in files if isinstance(f, dict) and f.get("path")]
    return []


def generate_code_changes(
    ticket: TicketDetail,
    solution: str,
    language: str,
    repo_file_list: list[str] | None = None,
) -> list[dict]:
    """
    Ask Groq for concrete code changes. Returns list of {path, content}.
    Paths are relative to repo root. Validates: no '..', no absolute.
    """
    ctx = ticket_to_context_string(ticket)
    file_hint = ""
    if repo_file_list:
        file_hint = f"\nExisting files in repo (prefer editing these): {', '.join(repo_file_list[:50])}"
    lang_lower = language.strip().lower()
    practices = {
        "python": "Follow PEP 8 and use type hints where appropriate.",
        "typescript": "Use strict types and common project style.",
        "javascript": "Use ES modules and consistent style.",
        "go": "Follow Go conventions and effective Go style.",
    }
    practice = practices.get(lang_lower, f"Follow best practices for {language}.")

    system = (
        "You are an Expert Software Engineer and Code Generator. Given a Jira ticket and a solution description, output concrete file changes as JSON only. "
        "Output exactly one JSON object with a key 'files' whose value is an array of objects, each with 'path' (relative path from repo root) and 'content' (full file content as string). "
        "No markdown, no explanation outside the JSON. Create or modify only the files needed for the solution. "
        "CRITICAL: Take all the details from the Jira description box, which can have any content like Technical Specifications, Execution Plan, Scope, Objective, etc. You must strongly align your code output with these exact specifications.\n"
        "CRITICAL: Act as a professional developer. Strictly adhere to SOLID principles, design patterns, DRY methodology, extensive error handling, and language-specific coding standards.\n"
        f"{practice}"
    )
    user = (
        f"Ticket context:\n{ctx}\n\nSolution:\n{solution}\n\n"
        f"Language: {language}{file_hint}\n\n"
        "Output the JSON with 'files' array (path and content for each file)."
    )
    raw = _call_groq(system, user)
    files = _parse_files_json(raw)
    out = []
    for f in files:
        path = (f.get("path") or "").strip()
        if ".." in path or path.startswith("/"):
            continue
        content = f.get("content")
        if content is None:
            content = ""
        out.append({"path": path, "content": content if isinstance(content, str) else str(content)})
    return out


def generate_tests(
    ticket: TicketDetail,
    solution: str,
    language: str,
    test_framework: str | None,
    changed_file_paths: list[str] | None = None,
) -> list[dict]:
    """
    Ask Groq for test files. Returns list of {path, content}.
    """
    ctx = ticket_to_context_string(ticket)
    lang_lower = language.strip().lower()
    framework = (test_framework or "").strip() or {"python": "pytest", "typescript": "jest", "javascript": "jest"}.get(lang_lower, "standard")
    changed_hint = ""
    if changed_file_paths:
        changed_hint = f"\nImplementations to test: {', '.join(changed_file_paths[:30])}"

    system = (
        "You are a test generator. Given a Jira ticket and solution, output test files as JSON only. "
        "Output exactly one JSON object with key 'files' = array of objects with 'path' and 'content'. "
        "No markdown, no explanation outside the JSON. Write unit/integration tests that validate the implementation. "
        "CRITICAL: Take all the details from the Jira description box, which can have any content like Test Cases, Acceptance Criteria, Scope, Technical Specifications, etc. You must strongly align your test output with these exact specifications. "
        f"Use {framework} style for {language}."
    )
    user = (
        f"Ticket context:\n{ctx}\n\nSolution:\n{solution}\n\n"
        f"Language: {language}, test framework: {framework}{changed_hint}\n\n"
        "Output the JSON with 'files' array (path and content for each test file)."
    )
    raw = _call_groq(system, user)
    files = _parse_files_json(raw)
    out = []
    for f in files:
        path = (f.get("path") or "").strip()
        if ".." in path or path.startswith("/"):
            continue
        content = f.get("content")
        if content is None:
            content = ""
        out.append({"path": path, "content": content if isinstance(content, str) else str(content)})
    return out
