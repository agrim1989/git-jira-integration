"""
MCP server that extracts the git diff of a given branch against a base branch 
and uses Groq LLM to automatically review the code.
"""
import subprocess
import tempfile
import httpx
from mcp.server.fastmcp import FastMCP
from app.config import settings

mcp = FastMCP("pr-code-reviewer-mcp")

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

def _run(cmd_list, cwd, check=True):
    return subprocess.run(cmd_list, cwd=cwd, check=check, capture_output=True, text=True)

@mcp.tool()
def review_pr_code(repo_url: str, branch_name: str, base_branch: str = "main") -> str:
    """
    Validates a PR by cloning the repo, extracting the git diff between 
    a given base_branch and branch_name, and executing an AI code review.
    
    Args:
        repo_url: The full HTTPS URL of the git repository.
        branch_name: The branch name of the PR.
        base_branch: The target branch it seeks to merge into (e.g., "main").
    """
    if not settings.groq_api_key:
        return "Error: GROQ_API_KEY is missing from environment variables."

    diff_text = ""
    with tempfile.TemporaryDirectory() as tempd:
        try:
            # 1. Clone the repo
            _run(["git", "clone", repo_url, tempd], cwd=None)
            
            # 2. Fetch the base branch and PR branch natively
            _run(["git", "fetch", "origin", f"{base_branch}:{base_branch}"], cwd=tempd, check=False)
            _run(["git", "fetch", "origin", f"{branch_name}:{branch_name}"], cwd=tempd, check=False)
            
            # 3. Check out the PR branch
            _run(["git", "checkout", branch_name], cwd=tempd)
            
            # 4. Generate the diff between base_branch and branch_name
            res = _run(["git", "diff", f"{base_branch}...{branch_name}"], cwd=tempd)
            diff_text = res.stdout
            
        except subprocess.CalledProcessError as e:
            return f"Failed during git operation. Return code: {e.returncode}\nStderr: {e.stderr}"
        except Exception as e:
            return f"Error executing git diff: {str(e)}"

    if not diff_text.strip():
        return f"No code differences found between {base_branch} and {branch_name}."

    # Prevent extremely massive diffs from overflowing the context window
    max_chars = 25000 
    if len(diff_text) > max_chars:
        diff_text = diff_text[:max_chars] + "\n\n... [DIFF TRUNCATED TO AVOID TOKEN OVERFLOW] ..."

    # Request review from Groq AI
    system_prompt = (
        "You are an expert Senior Software Engineer performing a rigorous Code Review.\n"
        "You will be given a Git Diff representing proposed changes to a codebase.\n"
        "Please deeply analyze the code for:\n"
        "1. Bugs, logical errors, or edge cases.\n"
        "2. Adherence to Clean Code, SOLID principles, and DRY methodology.\n"
        "3. Security vulnerabilities.\n"
        "4. Performance bottlenecks.\n\n"
        "Format your response professionally in Markdown. Highlight specific lines or files if necessary. "
        "If the code looks perfect, briefly explain why."
    )

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please review the following git diff:\n\n```diff\n{diff_text}\n```"}
        ],
        "temperature": 0.2,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(
                GROQ_CHAT_URL,
                headers={"Authorization": f"Bearer {settings.groq_api_key.strip()}", "Content-Type": "application/json"},
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            
            choices = data.get("choices") or []
            if not choices:
                return "Failed to generate AI code review. No choices returned."
            msg = choices[0].get("message") or {}
            
            review_content = msg.get("content", "Empty review returned.")
            
            final_output = f"## AI Code Review (`{base_branch}` ➔ `{branch_name}`)\n\n"
            final_output += review_content
            return final_output

    except Exception as e:
        return f"Failed to execute AI code review via Groq: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
