"""
MCP server that acts as a Project Manager / Team Leader: validates a PR (optional tests),
performs AI code review, and posts the review plus inline code comments on GitHub.
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Add project root for app imports
project_root = Path(__file__).resolve().parent
import sys
sys.path.insert(0, str(project_root))

from app.config import settings

mcp = FastMCP("pr-manager-mcp")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def _run(cmd_list, cwd, check=True):
    return subprocess.run(cmd_list, cwd=cwd, check=check, capture_output=True, text=True, timeout=120)


def _get_diff(repo_url: str, branch_name: str, base_branch: str, max_chars: int = 25000) -> tuple[str, str]:
    """Clone repo, get diff. Returns (diff_text, error). error is non-empty on failure."""
    diff_text = ""
    with tempfile.TemporaryDirectory() as tempd:
        try:
            _run(["git", "clone", "--depth", "50", repo_url, tempd], cwd=None)
            _run(["git", "fetch", "origin", f"{base_branch}:{base_branch}"], cwd=tempd, check=False)
            _run(["git", "fetch", "origin", f"{branch_name}:{branch_name}"], cwd=tempd, check=False)
            _run(["git", "checkout", branch_name], cwd=tempd)
            res = _run(["git", "diff", f"{base_branch}...{branch_name}"], cwd=tempd)
            diff_text = res.stdout or ""
        except subprocess.CalledProcessError as e:
            return "", f"Git failed: {e.stderr or str(e)}"
        except Exception as e:
            return "", str(e)
    if not diff_text.strip():
        return "", f"No diff between {base_branch} and {branch_name}."
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars] + "\n\n... [DIFF TRUNCATED] ..."
    return diff_text, ""


def _run_tests(repo_url: str, branch_name: str, test_command: str) -> str:
    """Clone, checkout branch, run test command. Returns output string."""
    with tempfile.TemporaryDirectory() as tempd:
        try:
            _run(["git", "clone", "--depth", "50", repo_url, tempd], cwd=None)
            _run(["git", "checkout", branch_name], cwd=tempd)
            result = subprocess.run(
                test_command, shell=True, cwd=tempd, capture_output=True, text=True, timeout=300
            )
            out = f"**Tests** (`{test_command}`)\nExit code: {result.returncode}\n\n"
            if result.stdout:
                out += f"STDOUT:\n```\n{result.stdout[:8000]}\n```\n\n"
            if result.stderr:
                out += f"STDERR:\n```\n{result.stderr[:4000]}\n```\n"
            return out
        except subprocess.TimeoutExpired:
            return "**Tests** – Command timed out.\n"
        except Exception as e:
            return f"**Tests** – Error: {e}\n"


def _structured_review(diff_text: str, base_branch: str, branch_name: str, test_summary: str = "") -> tuple[str, list]:
    """
    Call Groq to get structured review: summary (markdown) + inline_comments list.
    Returns (summary, inline_comments). inline_comments are dicts: path, line, body, side (optional).
    """
    system_prompt = """You are a Project Manager and Team Leader performing a code review.
Your goal is to ensure work is high-quality, bug-free, and aligned with project goals.
You will receive a Git diff. Respond with a valid JSON object only:
{
  "summary": "PM Oversight: Highlight architectural wins, risks, and alignment with the team roadmap. Mention if PR description matches the changes.",
  "inline_comments": [
    { "path": "filename.py", "line": 10, "body": "TL Feedback: 'Consider moving this to a utility class' or 'Missing check here'." }
  ]
}
Rules:
- Give professional, constructive, and firm feedback.
- Max 15 inline comments.
- JSON response only."""

    user_content = f"Review this diff (base: {base_branch}, branch: {branch_name})."
    if test_summary:
        user_content += f"\n\nTest run result:\n{test_summary}"
    user_content += f"\n\n```diff\n{diff_text}\n```"

    payload = {
        "model": getattr(settings, "groq_model", "llama-3.3-70b-versatile"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.2,
        "stream": False,
    }

    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key.strip()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        r.raise_for_status()
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return "Review failed: no response.", []
        content = (choices[0].get("message") or {}).get("content", "").strip()

    # Parse JSON (allow wrapped in ```json ... ```)
    content_clean = content
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", content):
        content_clean = match.group(1).strip()
        break
    try:
        obj = json.loads(content_clean)
    except json.JSONDecodeError:
        return content[:6000] if content else "Review generated but could not parse structured output.", []

    summary = obj.get("summary") or "Code review completed."
    raw_comments = obj.get("inline_comments")
    if not isinstance(raw_comments, list):
        return summary, []
    inline_comments = []
    for c in raw_comments[:20]:
        if isinstance(c, dict) and c.get("path") and c.get("body") and c.get("line") is not None:
            try:
                line = int(c.get("line"))
                if line < 1:
                    continue
                inline_comments.append({
                    "path": str(c.get("path", "")).strip(),
                    "line": line,
                    "body": (c.get("body") or "")[:2000],
                    "side": "RIGHT",
                })
            except (TypeError, ValueError):
                continue
    return summary, inline_comments


@mcp.tool()
def pm_code_review_and_comment(
    repo_url: str,
    branch_name: str,
    base_branch: str = "main",
    run_tests: bool = False,
    test_command: str = "pytest",
) -> str:
    """
    Perform a Project Manager/Team Leader review of a PR.
    - Validates the PR against the linked Jira ticket (if any).
    - Runs optional tests.
    - Performs an AI code review focused on best practices and tech leadership.
    - Posts the result as a GitHub PR review with inline comments.
    """
    return validate_review_and_comment_on_pr(
        repo_url=repo_url,
        branch_name=branch_name,
        base_branch=base_branch,
        run_tests=run_tests,
        test_command=test_command,
        post_to_github=True,
    )


@mcp.tool()
def deep_branch_code_review(
    repo_url: str,
    branch_name: str,
    base_branch: str = "main",
    ticket_id: Optional[str] = None
) -> str:
    """
    Performs a deep AI code review by analyzing the full contents of changed files
    in BOTH branches (Before and After).
    
    1. Identifies files that differ between branches.
    2. Collects the full content of these files from each branch.
    3. Sends file pairs to the LLM for a deep comparative analysis.
    4. Posts the findings as a PR review.
    """
    if not settings.groq_api_key:
        return "Error: GROQ_API_KEY is missing."

    gh_token = os.environ.get("GITHUB_TOKEN")
    from app.services.github_service import get_pull_request_by_branch, submit_pr_review
    from app.services.jira_service import fetch_ticket

    pr_info = get_pull_request_by_branch(repo_url, branch_name, gh_token)
    if not pr_info:
        return f"No open PR found for branch '{branch_name}'."

    ticket_context = ""
    if ticket_id:
        try:
            t = fetch_ticket(ticket_id)
            ticket_context = f"Jira Ticket Context:\n{t.summary}\n{t.description}\n\n"
        except:
            pass

    changed_files_contents = [] # items: {path, old_content, new_content}
    
    with tempfile.TemporaryDirectory() as tempd:
        try:
            _run(["git", "clone", "--depth", "50", repo_url, tempd], cwd=None)
            _run(["git", "fetch", "origin", f"{base_branch}:{base_branch}"], cwd=tempd, check=False)
            _run(["git", "fetch", "origin", f"{branch_name}:{branch_name}"], cwd=tempd, check=False)

            # Get list of changed files
            res = _run(["git", "diff", "--name-only", f"{base_branch}...{branch_name}"], cwd=tempd)
            files = [f.strip() for f in res.stdout.splitlines() if f.strip()][:10] # limit to 10 for tokens

            for f in files:
                # Get old content
                try:
                    old_c = _run(["git", "show", f"{base_branch}:{f}"], cwd=tempd).stdout
                except:
                    old_c = "[FILE DID NOT EXIST]"
                
                # Get new content
                try:
                    new_c = _run(["git", "show", f"{branch_name}:{f}"], cwd=tempd).stdout
                except:
                    new_c = "[FILE DELETED]"
                
                changed_files_contents.append({
                    "path": f,
                    "old": old_c[:10000], # truncation
                    "new": new_c[:10000]
                })
        except Exception as e:
            return f"Git error in deep review: {str(e)}"

    if not changed_files_contents:
        return "No changed files detected for deep review."

    # Build prompt
    review_prompt = f"{ticket_context}I am providing the full contents for changed files in both branches.\n"
    review_prompt += f"Base Branch: {base_branch}\nFeature Branch: {branch_name}\n\n"
    for item in changed_files_contents:
        review_prompt += f"--- FILE: {item['path']} ---\n"
        review_prompt += f"OLD VERSION (from {base_branch}):\n```\n{item['old']}\n```\n"
        review_prompt += f"NEW VERSION (from {branch_name}):\n```\n{item['new']}\n```\n\n"

    system_prompt = """You are a meticulous Project Manager and Tech Lead. 
Analyze the Before/After states provided. Evaluate:
- If the changes fulfill the project requirements.
- Maintainability and future technical debt.
- Compliance with senior development standards.
Respond with a clear Markdown summary for the PR body and a list of structured inline comments in JSON format:
{
  "summary": "...",
  "inline_comments": [ {"path": "...", "line": 123, "body": "..."} ]
}"""

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": review_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }

    try:
        with httpx.Client(timeout=180.0) as client:
            r = client.post(
                GROQ_CHAT_URL,
                headers={"Authorization": f"Bearer {settings.groq_api_key.strip()}", "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            content = r.json().get("choices")[0]["message"]["content"]
            # Parse result
            data = json.loads(content)
            summary = data.get("summary", "Deep review completed.")
            comments = data.get("inline_comments", [])

            # Post to GitHub
            review_url = submit_pr_review(
                repo_url=repo_url,
                pull_number=pr_info["number"],
                body=f"## 🕵️ Deep Branch Review\n\n{summary}",
                token=gh_token,
                event="COMMENT",
                commit_id=pr_info.get("head_sha"),
                inline_comments=comments if comments else None
            )
            return f"Deep review posted: {review_url or 'Failed to post review body'}"
    except Exception as e:
        return f"Deep review LLM error: {str(e)}"


@mcp.tool()
def validate_review_and_comment_on_pr(
    repo_url: str,
    branch_name: str,
    base_branch: str = "main",
    run_tests: bool = False,
    test_command: str = "pytest",
    post_to_github: bool = True,
    token: Optional[str] = None,
) -> str:
    """
    Act as a Project Manager / Team Leader: validate the PR, run AI code review,
    and post the review plus inline code comments on GitHub.

    1. Resolves the open PR for the given branch.
    2. Optionally runs tests (run_tests=True) and includes results in the review.
    3. Runs an AI code review on the PR diff and gets a summary + inline comments.
    4. If post_to_github is True, submits the review to GitHub with the summary as the review body
       and each suggestion as an inline comment on the relevant line.

    Args:
        repo_url: Full HTTPS URL of the git repository.
        branch_name: Branch name of the PR (e.g. PROJ-123 or feature/xyz).
        base_branch: Target branch (e.g. main).
        run_tests: If True, run test_command on the branch and include output in the review.
        test_command: Command to run tests (e.g. "pytest", "npm test").
        post_to_github: If True, post the review and comments on the GitHub PR.
        token: GitHub token (or set GITHUB_TOKEN in env).
    """
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not settings.groq_api_key:
        return "Error: GROQ_API_KEY is required for AI code review. Set it in .env."
    if post_to_github and not gh_token:
        return "Error: GITHUB_TOKEN is required to post review to GitHub. Set it in .env or pass token."

    from app.services.github_service import get_pull_request_by_branch, submit_pr_review

    pr_info = get_pull_request_by_branch(repo_url, branch_name, gh_token) if post_to_github else None
    if post_to_github and (not pr_info or not pr_info.get("html_url")):
        return f"No open PR found for branch '{branch_name}'. Create a PR first, then run this tool."
    if post_to_github and not pr_info.get("head_sha"):
        return "Could not get PR head commit SHA. Cannot post inline comments."

    # 1. Optional: run tests
    test_summary = ""
    if run_tests:
        test_summary = _run_tests(repo_url, branch_name, test_command)

    # 2. Get diff and structured review
    diff_text, err = _get_diff(repo_url, branch_name, base_branch)
    if err:
        return f"Failed to get diff: {err}"
    summary, inline_comments = _structured_review(diff_text, base_branch, branch_name, test_summary)

    # Build final review body
    review_body = f"## Code review (`{base_branch}` → `{branch_name}`)\n\n{summary}"
    if test_summary:
        review_body = f"{test_summary}\n---\n\n{review_body}"

    # 3. Post to GitHub
    if post_to_github and pr_info:
        event = "REQUEST_CHANGES" if inline_comments else "COMMENT"
        review_url = submit_pr_review(
            repo_url=repo_url,
            pull_number=pr_info["number"],
            body=review_body,
            token=gh_token,
            event=event,
            commit_id=pr_info.get("head_sha"),
            inline_comments=inline_comments if inline_comments else None,
        )
        inline_posted = bool(review_url and inline_comments)
        if not review_url and inline_comments:
            # GitHub may return 422 for invalid line/path; retry with summary only
            review_url = submit_pr_review(
                repo_url=repo_url,
                pull_number=pr_info["number"],
                body=review_body + f"\n\n---\n*({len(inline_comments)} inline suggestion(s) could not be attached.)*",
                token=gh_token,
                event="COMMENT",
                commit_id=None,
                inline_comments=None,
            )
        if not review_url:
            return (
                f"Review generated but failed to post to GitHub. Summary:\n\n{review_body}\n\n"
                f"Inline comments count: {len(inline_comments)}"
            )
        msg = f"Posted review on the PR.\nPR: {pr_info['html_url']}\nReview: {review_url}"
        if inline_posted:
            msg = f"Posted review and {len(inline_comments)} inline comment(s) on the PR.\nPR: {pr_info['html_url']}\nReview: {review_url}"
        elif inline_comments:
            msg = f"Posted review (summary only; inline comments could not be attached).\nPR: {pr_info['html_url']}\nReview: {review_url}"
        return msg

    return f"Review (not posted):\n\n{review_body}\n\nInline comments: {len(inline_comments)}"


if __name__ == "__main__":
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    mcp.run(transport="stdio")
