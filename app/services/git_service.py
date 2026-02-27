"""Git operations for GitHub flow: clone, branch, apply files, commit, push."""
import re
import subprocess
import tempfile
from pathlib import Path


class GitCommandError(Exception):
    """Raised when a git command fails; message includes stderr for diagnosis."""

    def __init__(self, message: str, stdout: str = "", stderr: str = "", returncode: int = -1):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode
        detail = message
        if stderr:
            detail = f"{detail} stderr: {stderr.strip()!r}"
        if stdout and not stderr:
            detail = f"{detail} stdout: {stdout.strip()!r}"
        super().__init__(detail)


def normalize_branch_name(ticket_id: str) -> str:
    """Normalize Jira ticket ID to a valid Git ref (e.g. PROJ-123, replace spaces/slashes with -)."""
    s = (ticket_id or "").strip()
    s = re.sub(r"[\s/]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "branch"


def _run(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git"] + list(args),
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        timeout=120,
    )


def _auth_url(repo_url: str, token: str) -> str:
    """Inject token into HTTPS URL for clone/push."""
    if not token or not repo_url.strip():
        return repo_url
    url = repo_url.strip()
    if url.startswith("https://"):
        if "@" in url.split("//")[1]:
            url = "https://" + url.split("//", 1)[1].split("@", 1)[1]
        return f"https://{token}@{url[8:]}"
    if url.startswith("http://"):
        if "@" in url.split("//")[1]:
            url = "http://" + url.split("//", 1)[1].split("@", 1)[1]
        return f"http://{token}@{url[7:]}"
    return repo_url


def clone_repo(repo_url: str, token: str | None) -> Path:
    """Clone repo into a temp dir; return path. Uses token in URL for HTTPS auth."""
    auth = _auth_url(repo_url, token or "")
    tmp = tempfile.mkdtemp(prefix="jira_github_")
    path = Path(tmp)
    _run(path, "clone", "--depth", "1", auth, str(path / "repo"))
    return path / "repo"


def branch_exists_remote(repo_path: Path, branch: str) -> bool:
    """Return True if origin/branch exists."""
    r = _run(repo_path, "ls-remote", "origin", f"refs/heads/{branch}", check=False)
    return bool((r.stdout or "").strip())


def get_default_branch(repo_path: Path) -> str:
    """Return default branch (main or master)."""
    try:
        r = _run(repo_path, "symbolic-ref", "refs/remotes/origin/HEAD")
        ref = (r.stdout or "").strip()
        if ref:
            return ref.replace("refs/remotes/origin/", "")
    except subprocess.CalledProcessError:
        pass
    try:
        _run(repo_path, "branch", "-r")
        r = _run(repo_path, "branch", "-r", "--format", "%(refname:short)", check=False)
        for line in (r.stdout or "").strip().splitlines():
            name = line.strip().replace("origin/", "")
            if name in ("main", "master") and not name.startswith("HEAD"):
                return name
        for line in (r.stdout or "").strip().splitlines():
            name = line.strip().replace("origin/", "")
            if name and name != "HEAD":
                return name
    except Exception:
        pass
    return "main"


def ensure_branch(repo_path: Path, branch_name: str, from_branch: str = "main") -> str:
    """
    Checkout from_branch, create branch_name if it doesn't exist, checkout it.
    If repo has no commits, create orphan branch branch_name.
    Returns the branch name in use.
    """
    try:
        _run(repo_path, "fetch", "origin", from_branch, check=False)
    except Exception:
        pass
    try:
        _run(repo_path, "checkout", "-b", branch_name, f"origin/{from_branch}")
        return branch_name
    except subprocess.CalledProcessError:
        pass
    try:
        _run(repo_path, "checkout", from_branch, check=False)
    except subprocess.CalledProcessError:
        pass
    try:
        r = _run(repo_path, "rev-parse", "--verify", "HEAD", check=False)
        if r.returncode != 0 or not (r.stdout or "").strip():
            _run(repo_path, "checkout", "--orphan", branch_name)
            return branch_name
    except Exception:
        _run(repo_path, "checkout", "--orphan", branch_name)
        return branch_name
    _run(repo_path, "checkout", "-b", branch_name)
    return branch_name


def list_repo_files(repo_path: Path, max_files: int = 100) -> list[str]:
    """Return relative paths of tracked files (for code-gen context)."""
    r = _run(repo_path, "ls-files", check=False)
    lines = [p for p in (r.stdout or "").strip().splitlines() if p.strip()][:max_files]
    return lines


def apply_changes(repo_path: Path, files: list[dict]) -> None:
    """Write each {path, content} into repo_path (path relative to repo root). Creates dirs as needed."""
    for item in files:
        path = (item.get("path") or "").strip()
        if not path or ".." in path or path.startswith("/"):
            continue
        content = item.get("content")
        if content is None:
            continue
        full = repo_path / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content if isinstance(content, str) else str(content), encoding="utf-8")


def commit_and_push(
    repo_path: Path,
    message: str,
    branch: str,
    repo_url: str,
    token: str,
) -> str:
    """Add all, commit, push origin branch. Returns commit SHA."""
    _run(repo_path, "add", "-A")
    _run(repo_path, "config", "user.email", "jira-flow@local", check=False)
    _run(repo_path, "config", "user.name", "Jira GitHub Flow", check=False)
    _run(repo_path, "commit", "-m", message, "--allow-empty")
    r = _run(repo_path, "rev-parse", "HEAD")
    sha = (r.stdout or "").strip()
    push_with_token(repo_path, branch, repo_url, token)
    return sha


def push_with_token(repo_path: Path, branch: str, repo_url: str, token: str) -> None:
    """Push branch to origin using token in URL; restore original URL after."""
    original_url = repo_url.strip()
    auth = _auth_url(original_url, token)
    remote = "origin"
    _run(repo_path, "remote", "set-url", remote, auth, check=False)
    proc = subprocess.run(
        ["git", "push", remote, branch],
        cwd=repo_path,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    _run(repo_path, "remote", "set-url", remote, original_url, check=False)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        raise GitCommandError(
            f"git push origin {branch} failed (exit {proc.returncode}). "
            "Check GITHUB_TOKEN has repo scope and push access to the repository.",
            stdout=stdout,
            stderr=stderr,
            returncode=proc.returncode,
        )
