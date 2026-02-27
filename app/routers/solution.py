"""Solution API: ask solution for a ticket (Groq or MCP), and optionally post to Jira."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import (
    McpSolutionRequest,
    PostSolutionToJiraRequest,
    PublishSolutionRequest,
    PostSolutionToJiraResponse,
    SolutionRequest,
    SolutionResponse,
    SubtaskDefaults,
    SubtaskItem,
)
from app.services.groq_service import get_solution_from_groq
from app.services.jira_service import (
    add_comment_to_ticket,
    create_subtask,
    fetch_ticket,
    is_story_or_epic,
    parse_suggested_subtasks,
    update_issue_description,
)
from app.services.mcp_service import call_mcp_solution

router = APIRouter(tags=["solution"])


@router.post("/tickets/{ticket_id}/solution", response_model=SolutionResponse)
async def ticket_solution(ticket_id: str, body: SolutionRequest | None = None) -> SolutionResponse:
    """
    Fetch the ticket and return a solution. Uses Groq if GROQ_API_KEY is set, else the default MCP server.
    User can pass an optional question about the ticket.
    """
    try:
        ticket = fetch_ticket(ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")

    question = (body.question if body else None) or "Provide a solution or recommendations for this ticket."
    try:
        if settings.groq_api_key:
            solution = get_solution_from_groq(
                ticket, question, include_subtasks_for_story_epic=is_story_or_epic(ticket)
            )
            mcp_key, tool_name = None, None
        else:
            solution = await call_mcp_solution(
                ticket, mcp_server_key=None, tool_name=None, question=question
            )
            mcp_key, tool_name = None, None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solution call failed: {e}")

    return SolutionResponse(
        ticket_id=ticket_id,
        ticket_summary=ticket.summary,
        question=question,
        solution=solution,
        mcp_server_key=mcp_key,
        tool_name=tool_name,
    )


@router.post("/mcp/solution", response_model=SolutionResponse)
async def mcp_solution(body: McpSolutionRequest) -> SolutionResponse:
    """
    Pass the given ticket data to the specified MCP server and return the solution.
    You can specify which MCP server (by key) and which tool to call.
    """
    try:
        ticket = fetch_ticket(body.ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")

    try:
        solution = await call_mcp_solution(
            ticket,
            mcp_server_key=body.mcp_server_key,
            tool_name=body.tool_name,
            question=body.question,
            extra_tool_args=body.tool_arguments or None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"MCP call failed: {e}")

    cfg = None
    if body.mcp_server_key:
        from app.config import settings
        servers = {s.key: s for s in settings.get_mcp_servers()}
        cfg = servers.get(body.mcp_server_key)

    return SolutionResponse(
        ticket_id=body.ticket_id,
        ticket_summary=ticket.summary,
        question=body.question,
        solution=solution,
        mcp_server_key=body.mcp_server_key,
        tool_name=body.tool_name or (cfg.solution_tool_name if cfg else None),
    )


@router.post("/tickets/{ticket_id}/solution/post-to-jira", response_model=PostSolutionToJiraResponse)
async def solution_post_to_jira(ticket_id: str, body: PostSolutionToJiraRequest | None = None) -> PostSolutionToJiraResponse:
    """
    Generate an approach plan and solution for the ticket, post it as a comment, and if the ticket
    is a Story or Epic, create sub-tasks under it from the 'Suggested sub-tasks:' section.
    """
    question = (
        (body.question if body else None)
        or "Provide an approach plan (numbered steps), the detailed solution, and if this is a Story/Epic a 'Suggested sub-tasks:' list."
    )
    try:
        ticket = fetch_ticket(ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")

    try:
        if settings.groq_api_key:
            solution = get_solution_from_groq(
                ticket, question, as_plan_and_solution=True, include_subtasks_for_story_epic=True
            )
        else:
            solution = await call_mcp_solution(
                ticket, mcp_server_key=None, tool_name=None, question=question
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Solution call failed: {e}")

    created_subtask_keys: list[str] = []
    subtask_errors: list[str] = []
    defaults: SubtaskDefaults | None = body.subtask_defaults if body else None
    assignee_id = (defaults.assignee_account_id if defaults else None) or (settings.jira_default_assignee_account_id or None)
    priority_name = (defaults.priority if defaults else None) or (settings.jira_default_priority or None)
    labels_list: list[str] = []
    if defaults and defaults.labels:
        labels_list = list(defaults.labels)
    elif settings.jira_default_subtask_labels:
        labels_list = [x.strip() for x in settings.jira_default_subtask_labels.split(",") if x.strip()]
    due_days = (defaults.due_days if defaults is not None and defaults.due_days is not None else None) or settings.jira_default_due_days
    duedate_str: str | None = None
    if due_days and due_days > 0:
        duedate_str = (datetime.now(timezone.utc) + timedelta(days=due_days)).strftime("%Y-%m-%d")
    components_list: list[str] = []
    if defaults and defaults.components:
        components_list = list(defaults.components)
    elif settings.jira_default_components:
        components_list = [x.strip() for x in settings.jira_default_components.split(",") if x.strip()]
    fix_version_str = (defaults.fix_version if defaults else None) or (settings.jira_default_fix_version or None) or None

    if is_story_or_epic(ticket) and ticket.project:
        subtask_items: list[SubtaskItem] = parse_suggested_subtasks(solution)
        if not subtask_items:
            first_line = (solution.split("\n")[0] or "Implement solution").strip()[:255]
            subtask_items = [SubtaskItem(summary=first_line or "Implement solution", description=solution[:2000] or None)]
        # Ensure every sub-task gets a description (parsed description, or full solution, or placeholder)
        solution_fallback = (solution or "").strip()[:5000] or "See parent story and solution comment for context."
        for item in subtask_items:
            desc = (item.description or "").strip() or solution_fallback
            try:
                created = create_subtask(
                    ticket_id,
                    ticket.project,
                    item.summary,
                    description=desc,
                    assignee_account_id=assignee_id,
                    priority_name=priority_name,
                    labels=labels_list or None,
                    duedate=duedate_str,
                    components=components_list or None,
                    fix_version=fix_version_str,
                )
                if created.get("key"):
                    created_subtask_keys.append(created["key"])
            except Exception as e:
                subtask_errors.append(f"{item.summary!r}: {e}")

    # Update issue description if it was empty
    description_updated = False
    if not (ticket.description and str(ticket.description).strip()):
        try:
            update_issue_description(ticket_id, solution)
            description_updated = True
        except Exception:
            pass  # Non-fatal; comment will still contain the solution

    comment_prefix = "Suggested approach and solution\n\n"
    if created_subtask_keys:
        comment_prefix += f"Created sub-tasks: {', '.join(created_subtask_keys)}\n\n"
    comment_body = comment_prefix + solution
    try:
        comment = add_comment_to_ticket(ticket_id, comment_body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to add comment to Jira: {e}")

    comment_id = comment.get("id")
    base_url = settings.jira_url.rstrip("/")
    comment_url = f"{base_url}/browse/{ticket_id}?focusedCommentId={comment_id}" if comment_id else None

    return PostSolutionToJiraResponse(
        ticket_id=ticket_id,
        solution=solution,
        comment_id=comment_id,
        comment_url=comment_url,
        created_subtask_keys=created_subtask_keys,
        subtask_errors=subtask_errors,
        description_updated=description_updated,
        success=True,
    )


@router.post("/tickets/{ticket_id}/solution/publish", response_model=PostSolutionToJiraResponse)
async def solution_publish_to_jira(ticket_id: str, body: PublishSolutionRequest) -> PostSolutionToJiraResponse:
    """
    Publish a pre-generated/reviewed solution string to the ticket directly, without making an LLM call.
    """
    try:
        ticket = fetch_ticket(ticket_id)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ticket not found: {e}")

    solution = body.solution
    created_subtask_keys: list[str] = []
    subtask_errors: list[str] = []
    defaults: SubtaskDefaults | None = body.subtask_defaults
    assignee_id = (defaults.assignee_account_id if defaults else None) or (settings.jira_default_assignee_account_id or None)
    priority_name = (defaults.priority if defaults else None) or (settings.jira_default_priority or None)
    labels_list: list[str] = []
    if defaults and defaults.labels:
        labels_list = list(defaults.labels)
    elif settings.jira_default_subtask_labels:
        labels_list = [x.strip() for x in settings.jira_default_subtask_labels.split(",") if x.strip()]
    due_days = (defaults.due_days if defaults is not None and defaults.due_days is not None else None) or settings.jira_default_due_days
    duedate_str: str | None = None
    if due_days and due_days > 0:
        duedate_str = (datetime.now(timezone.utc) + timedelta(days=due_days)).strftime("%Y-%m-%d")
    components_list: list[str] = []
    if defaults and defaults.components:
        components_list = list(defaults.components)
    elif settings.jira_default_components:
        components_list = [x.strip() for x in settings.jira_default_components.split(",") if x.strip()]
    fix_version_str = (defaults.fix_version if defaults else None) or (settings.jira_default_fix_version or None) or None

    if is_story_or_epic(ticket) and ticket.project:
        subtask_items: list[SubtaskItem] = parse_suggested_subtasks(solution)
        if not subtask_items:
            first_line = (solution.split("\n")[0] or "Implement solution").strip()[:255]
            subtask_items = [SubtaskItem(summary=first_line or "Implement solution", description=solution[:2000] or None)]
        solution_fallback = (solution or "").strip()[:5000] or "See parent story and solution comment for context."
        for item in subtask_items:
            desc = (item.description or "").strip() or solution_fallback
            try:
                created = create_subtask(
                    ticket_id,
                    ticket.project,
                    item.summary,
                    description=desc,
                    assignee_account_id=assignee_id,
                    priority_name=priority_name,
                    labels=labels_list or None,
                    duedate=duedate_str,
                    components=components_list or None,
                    fix_version=fix_version_str,
                )
                if created.get("key"):
                    created_subtask_keys.append(created["key"])
            except Exception as e:
                subtask_errors.append(f"{item.summary!r}: {e}")

    description_updated = False
    if not (ticket.description and str(ticket.description).strip()):
        try:
            update_issue_description(ticket_id, solution)
            description_updated = True
        except Exception:
            pass

    comment_prefix = "Suggested approach and solution\n\n"
    if created_subtask_keys:
        comment_prefix += f"Created sub-tasks: {', '.join(created_subtask_keys)}\n\n"
    comment_body = comment_prefix + solution
    try:
        comment = add_comment_to_ticket(ticket_id, comment_body)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to add comment to Jira: {e}")

    comment_id = comment.get("id")
    base_url = settings.jira_url.rstrip("/")
    comment_url = f"{base_url}/browse/{ticket_id}?focusedCommentId={comment_id}" if comment_id else None

    return PostSolutionToJiraResponse(
        ticket_id=ticket_id,
        solution=solution,
        comment_id=comment_id,
        comment_url=comment_url,
        created_subtask_keys=created_subtask_keys,
        subtask_errors=subtask_errors,
        description_updated=description_updated,
        success=True,
    )
