"""GitHub API: create pull request."""
import re

import httpx


def parse_repo_owner_name(repo_url: str) -> tuple[str, str] | None:
    """Extract owner and repo name from HTTPS or SSH URL. Returns (owner, name) or None."""
    url = (repo_url or "").strip()
    if not url:
        return None
    # https://github.com/owner/repo.git or .../owner/repo
    m = re.match(r"https?://[^/]+/([^/]+)/([^/#?]+?)(?:\.git)?/?$", url, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2).removesuffix(".git")
    # git@github.com:owner/repo.git
    m = re.match(r"git@[^:]+:([^/]+)/([^/#?]+?)(?:\.git)?/?$", url)
    if m:
        return m.group(1), m.group(2).removesuffix(".git")
    return None


def create_pull_request(
    repo_url: str,
    head_branch: str,
    base_branch: str,
    title: str,
    body: str,
    token: str,
) -> str | None:
    """Create a PR via GitHub API. Returns html_url of the PR or None on failure."""
    parsed = parse_repo_owner_name(repo_url)
    if not parsed:
        return None
    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = {
        "title": title[:256],
        "body": body,
        "head": head_branch,
        "base": base_branch,
    }
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json=payload,
        )
        if r.status_code != 201:
            return None
        data = r.json()
        return data.get("html_url")

def check_pull_request_exists(
    repo_url: str,
    head_branch: str,
    token: str,
) -> str | None:
    """Check if a PR exists via GitHub API. Returns html_url of the PR or None."""
    info = get_pull_request_by_branch(repo_url, head_branch, token)
    return info.get("html_url") if info else None


def get_pull_request_by_branch(
    repo_url: str,
    head_branch: str,
    token: str,
) -> dict | None:
    """
    Get PR info by head branch. Returns dict with html_url and number, or None.
    """
    parsed = parse_repo_owner_name(repo_url)
    if not parsed:
        return None
    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    with httpx.Client(timeout=10.0) as client:
        r = client.get(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            params={"head": f"{owner}:{head_branch}"},
        )
        if r.status_code != 200:
            return None
        prs = r.json()
        if not prs:
            return None
        pr = prs[0]
        head = pr.get("head") or {}
        return {
            "html_url": pr.get("html_url"),
            "number": pr.get("number"),
            "head_sha": head.get("sha"),
        }


def add_pull_request_review(
    repo_url: str,
    pull_number: int,
    body: str,
    token: str,
    event: str = "COMMENT",
) -> str | None:
    """
    Post a review comment on a pull request. body is markdown.
    event: COMMENT (default), APPROVE, or REQUEST_CHANGES.
    Returns the review HTML URL or None on failure.
    """
    return submit_pr_review(
        repo_url=repo_url,
        pull_number=pull_number,
        body=body,
        token=token,
        event=event,
    )


def submit_pr_review(
    repo_url: str,
    pull_number: int,
    body: str,
    token: str,
    event: str = "COMMENT",
    commit_id: str | None = None,
    inline_comments: list[dict] | None = None,
) -> str | None:
    """
    Submit a pull request review with optional inline comments.
    body: overall review summary (markdown).
    event: COMMENT, APPROVE, or REQUEST_CHANGES.
    commit_id: SHA of the commit to comment on (required if inline_comments given).
    inline_comments: list of {"path": str, "line": int, "body": str, "side": "LEFT"|"RIGHT"}.
      side defaults to "RIGHT" (line in the new version).
    Returns the review HTML URL or None on failure.
    """
    parsed = parse_repo_owner_name(repo_url)
    if not parsed:
        return None
    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
    payload = {"body": (body or "Code review completed.")[:65535], "event": event}
    if commit_id:
        payload["commit_id"] = commit_id
    if inline_comments:
        payload["comments"] = []
        for c in inline_comments[:50]:  # cap to avoid rate limits
            path = (c.get("path") or "").strip()
            line = c.get("line")
            comment_body = (c.get("body") or "")[:65535]
            if not path or line is None or not comment_body:
                continue
            payload["comments"].append({
                "path": path,
                "line": int(line),
                "side": c.get("side") or "RIGHT",
                "body": comment_body,
            })
        if not payload["comments"]:
            del payload["comments"]
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            api_url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json=payload,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        return data.get("html_url")
