"""Pydantic models for API request/response."""
from typing import Any

from pydantic import BaseModel, Field


# --- Jira / Ticket ---
class SubtaskItem(BaseModel):
    """One suggested sub-task: summary (title) and optional description."""
    summary: str
    description: str | None = None


class TicketSummary(BaseModel):
    """Minimal ticket for list."""
    key: str
    summary: str
    status: str | None = None
    issue_type: str | None = None
    assignee: str | None = None


class TicketDetail(BaseModel):
    """Full ticket details (for get one / solution context)."""
    key: str
    summary: str
    description: str | None = None
    status: str | None = None
    issue_type: str | None = None
    assignee: str | None = None
    project: str | None = None
    created: str | None = None
    updated: str | None = None
    subtasks: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw Jira issue payload")


# --- Solution ---
class SolutionRequest(BaseModel):
    """Request body for asking a solution for a ticket."""
    question: str | None = Field(default=None, description="Optional user question about the ticket")


class McpSolutionRequest(BaseModel):
    """Request body for getting solution from an MCP server."""
    ticket_id: str = Field(..., description="Jira issue key, e.g. PROJ-123")
    mcp_server_key: str | None = Field(default=None, description="Key of MCP server in config; omit for default")
    tool_name: str | None = Field(default=None, description="Tool to call; omit to use server's solution_tool_name")
    question: str | None = Field(default=None, description="Optional user question")
    tool_arguments: dict[str, Any] = Field(default_factory=dict, description="Extra args merged with ticket_data/question")


class SolutionResponse(BaseModel):
    """Response for solution endpoints."""
    ticket_id: str
    ticket_summary: str | None = None
    question: str | None = None
    solution: str
    mcp_server_key: str | None = None
    tool_name: str | None = None


class SubtaskDefaults(BaseModel):
    """Optional defaults for sub-tasks created under a Story/Epic. Overrides env defaults when set."""
    assignee_account_id: str | None = Field(default=None, description="Jira Cloud accountId for assignee")
    priority: str | None = Field(default=None, description="Priority name, e.g. High, Medium, Low")
    labels: list[str] = Field(default_factory=list, description="Labels to add to each sub-task")
    due_days: int | None = Field(default=None, description="Due date = today + due_days (e.g. 7 for one week)")
    components: list[str] = Field(default_factory=list, description="Component names to add (project must have these)")
    fix_version: str | None = Field(default=None, description="Fix version name (e.g. release 1.0)")


class PostSolutionToJiraRequest(BaseModel):
    """Request for generating a solution and posting it to the ticket as a comment."""
    question: str | None = Field(
        default=None,
        description="Optional question (e.g. 'How do I fix this?'). Default: ask for approach plan + solution.",
    )
    subtask_defaults: SubtaskDefaults | None = Field(
        default=None,
        description="Optional defaults for created sub-tasks (assignee, priority, labels, due_days).",
    )


class PublishSolutionRequest(BaseModel):
    """Request for directly publishing an already-generated (and reviewed) solution string to Jira."""
    solution: str = Field(..., description="The reviewed/edited solution string to post")
    subtask_defaults: SubtaskDefaults | None = Field(
        default=None,
        description="Optional defaults for created sub-tasks.",
    )


class PostSolutionToJiraResponse(BaseModel):
    """Response after posting solution to Jira."""
    ticket_id: str
    solution: str
    comment_id: str | None = Field(default=None, description="Jira comment ID")
    comment_url: str | None = Field(default=None, description="Link to the comment in Jira if available")
    created_subtask_keys: list[str] = Field(
        default_factory=list,
        description="Keys of sub-tasks created under the Story/Epic (e.g. PROJ-124, PROJ-125)",
    )
    subtask_errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered while creating sub-tasks (e.g. permission or issuetype).",
    )
    description_updated: bool = Field(
        default=False,
        description="True if the issue description was empty and was updated with the solution.",
    )
    success: bool = True


# --- GitHub flow ---
class GitHubFlowRequest(BaseModel):
    """Request for Jira–GitHub flow: branch, AI code + tests, push, PR, Jira comment."""
    repo_url: str | None = Field(default=None, description="Override default repo (optional)")
    base_branch: str | None = Field(default=None, description="Optional base branch (e.g. main/develop). If omitted, uses repository default branch.")
    language: str = Field(..., description="e.g. python, typescript (required)")
    test_framework: str | None = Field(default=None, description="e.g. pytest, jest (optional; default from language)")
    question: str | None = Field(default=None, description="Optional; passed to solution generation")


class GitHubFlowResponse(BaseModel):
    """Response after GitHub flow: branch, commits, PR, Jira comment."""
    ticket_id: str
    branch: str
    commit_sha: str | None = Field(default=None, description="Implementation commit SHA")
    test_commit_sha: str | None = Field(default=None, description="Tests commit SHA")
    pr_url: str | None = Field(default=None, description="Pull request URL")
    jira_comment_id: str | None = None
    jira_comment_url: str | None = None
    success: bool = True
    error: str | None = Field(default=None, description="Partial failure message if any")


# --- Settings ---
class SettingsRequest(BaseModel):
    """Request for saving credentials to .env"""
    jira_url: str | None = None
    jira_username: str | None = None
    jira_api_token: str | None = None
    github_token: str | None = None


class SettingsResponse(BaseModel):
    """Response after saving settings"""
    success: bool
    message: str
