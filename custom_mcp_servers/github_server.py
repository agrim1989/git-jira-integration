import sys
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to sys.path so we can import app modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from app.services.github_service import (
    create_pull_request,
    check_pull_request_exists,
)
from app.services.git_service import (
    clone_repo,
    ensure_branch,
    apply_changes,
    commit_and_push,
    get_default_branch
)

mcp = FastMCP("Custom GitHub Server")

@mcp.tool()
def github_create_pull_request(repo_url: str, head_branch: str, title: str, body: str, base_branch: str = "main", token: Optional[str] = None) -> str:
    """Create a pull request on GitHub."""
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        return "Error: GITHUB_TOKEN environment variable or token parameter is required."
        
    try:
        pr_url = create_pull_request(
            repo_url=repo_url,
            head_branch=head_branch,
            base_branch=base_branch,
            title=title,
            body=body,
            token=gh_token
        )
        if pr_url:
            return f"Successfully created PR: {pr_url}"
        return "Failed to create PR."
    except Exception as e:
        return f"Error creating PR: {e}"

@mcp.tool()
def github_check_pr_exists(repo_url: str, head_branch: str, token: Optional[str] = None) -> str:
    """Check if a pull request exists for a specific branch."""
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        return "Error: GITHUB_TOKEN environment variable or token parameter is required."
        
    try:
        pr_url = check_pull_request_exists(
            repo_url=repo_url,
            head_branch=head_branch,
            token=gh_token
        )
        if pr_url:
            return f"PR exists: {pr_url}"
        return "No PR exists for this branch."
    except Exception as e:
        return f"Error checking PR: {e}"

@mcp.tool()
def git_commit_and_push_changes(repo_url: str, branch_name: str, message: str, files: List[Dict[str, str]], token: Optional[str] = None) -> str:
    """
    Clone a repo, checkout/create a branch, apply file changes, commit, and push.
    files should be a list of dicts with 'path' and 'content' keys.
    """
    gh_token = token or os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        return "Error: GITHUB_TOKEN environment variable or token parameter is required."
        
    try:
        # 1. Clone
        repo_path = clone_repo(repo_url, gh_token)
        
        # 2. Get base branch
        default_branch = get_default_branch(repo_path)
        
        # 3. Checkout branch
        ensure_branch(repo_path, branch_name, from_branch=default_branch)
        
        # 4. Apply changes
        apply_changes(repo_path, files)
        
        # 5. Commit and push
        sha = commit_and_push(
            repo_path=repo_path,
            message=message,
            branch=branch_name,
            repo_url=repo_url,
            token=gh_token
        )
        
        return f"Successfully committed and pushed. Commit SHA: {sha}"
    except Exception as e:
        return f"Error in git workflow: {e}"

if __name__ == "__main__":
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        
    mcp.run(transport="stdio")
