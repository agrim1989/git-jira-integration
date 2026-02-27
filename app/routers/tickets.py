"""Tickets API: fetch from Jira."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models import TicketDetail, TicketSummary
from app.services.jira_service import DEFAULT_JQL, fetch_ticket, fetch_tickets

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketSummary])
def list_tickets(
    jql: str = Query(default=DEFAULT_JQL, description="JQL query"),
    max_results: int = Query(default=50, ge=1, le=100),
    start_at: int = Query(default=0, ge=0),
) -> list[TicketSummary]:
    """Fetch tickets from Jira using JQL."""
    try:
        return fetch_tickets(jql=jql, max_results=max_results, start_at=start_at)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Jira request failed: {e}")


@router.get("/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: str) -> TicketDetail:
    """Get a single ticket by key (e.g. PROJ-123)."""
    try:
        return fetch_ticket(ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found or error: {e}")

@router.get("/{ticket_id}/comments")
def get_ticket_comments(ticket_id: str):
    """Get comments for a single ticket."""
    from app.services.jira_service import fetch_ticket_comments
    try:
        comments = fetch_ticket_comments(ticket_id)
        return {"comments": comments}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Comments not found or error: {e}")

@router.get("/{ticket_id}/pr")
def check_ticket_pr(ticket_id: str):
    """Check if a GitHub PR exists for this ticket branch."""
    from app.config import settings
    if not settings.github_token or not settings.github_default_repo_url:
        return {"pr_url": None}
    
    from app.services.git_service import normalize_branch_name
    from app.services.github_service import check_pull_request_exists
    
    branch_name = normalize_branch_name(ticket_id)
    try:
        pr_url = check_pull_request_exists(settings.github_default_repo_url, branch_name, settings.github_token)
        return {"pr_url": pr_url}
    except Exception as e:
        return {"pr_url": None, "error": str(e)}


class CodeReviewRequest(BaseModel):
    """Optional overrides for code review (PR for ticket must already exist)."""
    repo_url: str | None = None
    base_branch: str = "main"


@router.post("/{ticket_id}/code-review")
def run_code_review_and_update_pr(ticket_id: str, payload: CodeReviewRequest | None = None):
    """
    For the given Jira ticket ID: find the open PR for that ticket's branch,
    run an AI code review on the PR diff, and post the review as a comment on the PR.
    Returns PR URL and review comment URL.
    """
    from app.config import settings
    if not settings.github_token or not settings.github_default_repo_url:
        raise HTTPException(
            status_code=503,
            detail="GitHub not configured. Set GITHUB_TOKEN and GITHUB_DEFAULT_REPO_URL.",
        )
    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is required for AI code review.",
        )

    opts = payload or CodeReviewRequest()
    repo_url = (opts.repo_url or "").strip() or (settings.github_default_repo_url or "").strip()
    if not repo_url:
        raise HTTPException(status_code=400, detail="No repo URL configured or provided.")
    base_branch = (opts.base_branch or "main").strip() or "main"

    from app.services.git_service import normalize_branch_name
    from app.services.github_service import get_pull_request_by_branch, add_pull_request_review
    from mcp_code_reviewer import review_pr_code

    branch_name = normalize_branch_name(ticket_id)
    pr_info = get_pull_request_by_branch(repo_url, branch_name, settings.github_token)
    if not pr_info or not pr_info.get("html_url") or pr_info.get("number") is None:
        raise HTTPException(
            status_code=404,
            detail=f"No open PR found for ticket {ticket_id} (branch: {branch_name}). Create a PR first.",
        )

    review_body = review_pr_code(repo_url=repo_url, branch_name=branch_name, base_branch=base_branch)
    if not review_body or review_body.startswith("Error:") or review_body.startswith("Failed"):
        raise HTTPException(status_code=502, detail=f"Code review failed: {review_body or 'empty response'}")

    review_url = add_pull_request_review(
        repo_url=repo_url,
        pull_number=pr_info["number"],
        body=review_body,
        token=settings.github_token,
        event="COMMENT",
    )
    if not review_url:
        raise HTTPException(status_code=502, detail="Failed to post review comment on the PR.")

    return {
        "ticket_id": ticket_id,
        "pr_url": pr_info["html_url"],
        "review_posted": True,
        "review_url": review_url,
    }

class CommentRequest(BaseModel):
    body: str

@router.post("/{ticket_id}/comments")
def post_ticket_comment(ticket_id: str, payload: CommentRequest):
    """Post a simple quick comment to a single ticket."""
    from app.services.jira_service import add_comment_to_ticket
    try:
        comment = add_comment_to_ticket(ticket_id, payload.body)
        return {"id": comment.get("id"), "message": "Comment added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to add comment: {e}")

class TicketDraftRequest(BaseModel):
    prompt: str
    existing_ticket_id: str | None = None

@router.post("/draft")
def draft_ticket(payload: TicketDraftRequest):
    from app.services.groq_service import generate_ticket_draft
    from app.services.jira_service import fetch_ticket
    
    existing_context = None
    if payload.existing_ticket_id:
        try:
            ticket = fetch_ticket(payload.existing_ticket_id)
            existing_context = f"Summary: {ticket.summary}\nDescription: {ticket.description or ''}"
        except Exception:
            pass # Continue without context if not found
            
    try:
        import json
        result = generate_ticket_draft(payload.prompt, existing_context)
        return json.loads(result)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to draft ticket: {e}")

class TicketCreateRequest(BaseModel):
    project_key: str
    summary: str
    description: str | None = None
    issue_type: str = "Task"

@router.post("")
def create_new_ticket(payload: TicketCreateRequest):
    from app.services.jira_service import create_ticket
    try:
        res = create_ticket(
            project_key=payload.project_key,
            summary=payload.summary,
            description=payload.description,
            issue_type=payload.issue_type
        )
        return {"key": res.get("key"), "message": "Ticket created"}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to create ticket: {e}")

class TicketUpdateRequest(BaseModel):
    summary: str | None = None
    description: str | None = None

@router.put("/{ticket_id}")
def update_existing_ticket(ticket_id: str, payload: TicketUpdateRequest):
    from app.services.jira_service import update_ticket
    try:
        return update_ticket(
            ticket_id=ticket_id,
            summary=payload.summary,
            description=payload.description
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to update ticket: {e}")
