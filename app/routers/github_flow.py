"""GitHub flow: branch (Jira ID), AI code + tests, push, PR, Jira comment for review."""
import shutil

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import GitHubFlowRequest, GitHubFlowResponse
from app.services.code_gen_service import generate_code_changes, generate_tests
from app.services.github_service import create_pull_request
from app.services.git_service import (
    apply_changes,
    branch_exists_remote,
    clone_repo,
    commit_and_push,
    ensure_branch,
    get_default_branch,
    list_repo_files,
    normalize_branch_name,
)
from app.services.groq_service import get_solution_from_groq
from app.services.jira_service import add_comment_to_ticket, fetch_ticket

router = APIRouter(tags=["github-flow"])


@router.post("/tickets/{ticket_id}/github-flow", response_model=GitHubFlowResponse)
async def ticket_github_flow(ticket_id: str, body: GitHubFlowRequest) -> GitHubFlowResponse:
    """
    For a Jira ticket: create branch (name = ticket ID), generate code and tests with AI,
    commit and push, open a PR, and post the PR link to Jira for review.
    Client should send the preferred language (e.g. python, typescript) in the request.
    """
    if not settings.github_token:
        raise HTTPException(
            status_code=503,
            detail="GitHub flow is not configured. Set GITHUB_TOKEN in .env (repo scope).",
        )
    repo_url = (body.repo_url or "").strip() or (settings.github_default_repo_url or "").strip()
    if not repo_url:
        raise HTTPException(
            status_code=400,
            detail="No repo URL. Set GITHUB_DEFAULT_REPO_URL or pass repo_url in the request.",
        )

    try:
        ticket = fetch_ticket(ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")

    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is required for GitHub flow (solution and code generation).",
        )

    question = (body.question or "").strip() or "Provide an approach plan and implementation solution."
    try:
        solution = get_solution_from_groq(ticket, question, as_plan_and_solution=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solution generation failed: {e}")

    branch_name = normalize_branch_name(ticket_id)
    repo_path = None
    commit_sha = None
    test_commit_sha = None
    pr_url = None
    jira_comment_id = None
    jira_comment_url = None
    err_msg = None

    try:
        repo_path = clone_repo(repo_url, settings.github_token)
        if branch_exists_remote(repo_path, branch_name):
            raise HTTPException(
                status_code=409,
                detail=f"Branch {branch_name} already exists on remote. Use a different ticket or delete the branch.",
            )
        default_branch = body.base_branch or get_default_branch(repo_path)
        ensure_branch(repo_path, branch_name, default_branch)

        repo_files = list_repo_files(repo_path)
        code_files = generate_code_changes(ticket, solution, body.language, repo_files)
        if code_files:
            apply_changes(repo_path, code_files)
            commit_sha = commit_and_push(
                repo_path,
                f"Implement {ticket_id}: {ticket.summary[:80]}",
                branch_name,
                repo_url,
                settings.github_token,
            )
        else:
            commit_sha = commit_and_push(
                repo_path,
                f"Implement {ticket_id}: {ticket.summary[:80]}",
                branch_name,
                repo_url,
                settings.github_token,
            )

        # changed_paths = [f["path"] for f in code_files]
        # test_files = generate_tests(
        #     ticket,
        #     solution,
        #     body.language,
        #     body.test_framework,
        #     changed_paths or None,
        # )
        # if test_files:
        #     apply_changes(repo_path, test_files)
        #     test_commit_sha = commit_and_push(
        #         repo_path,
        #         f"Add tests for {ticket_id}",
        #         branch_name,
        #         repo_url,
        #         settings.github_token,
        #     )

        jira_link = f"{settings.jira_url.rstrip('/')}/browse/{ticket_id}"
        pr_title = f"[{ticket_id}] {ticket.summary[:100]}"
        pr_body = f"Jira: {jira_link}\n\nImplementation for this ticket."
        pr_url = create_pull_request(
            repo_url,
            branch_name,
            default_branch,
            pr_title,
            pr_body,
            settings.github_token,
        )
        if not pr_url:
            err_msg = "PR creation failed; branch was pushed. Please open a PR manually."

        comment_body = (
            f"Code changes have been pushed to branch `{branch_name}`. "
            f"Please review: {pr_url or '(open PR manually: ' + repo_url + ')'}"
        )
        try:
            comment = add_comment_to_ticket(ticket_id, comment_body)
            jira_comment_id = comment.get("id")
            if jira_comment_id:
                jira_comment_url = f"{settings.jira_url.rstrip('/')}/browse/{ticket_id}?focusedCommentId={jira_comment_id}"
        except Exception:
            pass

    except HTTPException:
        raise
    except Exception as e:
        err_msg = str(e)
        if not commit_sha and not pr_url:
            raise HTTPException(status_code=502, detail=f"GitHub flow failed: {e}")
    finally:
        if repo_path and hasattr(repo_path, "parent"):
            shutil.rmtree(repo_path.parent, ignore_errors=True)

    return GitHubFlowResponse(
        ticket_id=ticket_id,
        branch=branch_name,
        commit_sha=commit_sha,
        test_commit_sha=test_commit_sha,
        pr_url=pr_url,
        jira_comment_id=jira_comment_id,
        jira_comment_url=jira_comment_url,
        success=bool(commit_sha),
        error=err_msg,
    )
