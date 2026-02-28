import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path so we can import app modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from mcp.server.fastmcp import FastMCP
from app.services.jira_service import (
    fetch_ticket,
    fetch_tickets,
    create_ticket,
    update_ticket,
    add_comment_to_ticket,
    transition_issue as jira_transition_issue,
    ticket_to_context_string,
)

mcp = FastMCP("Custom Jira Server")

@mcp.tool()
def get_issue(issue_key: str) -> str:
    """Fetch details of a single Jira issue."""
    try:
        ticket = fetch_ticket(issue_key)
        return ticket_to_context_string(ticket)
    except Exception as e:
        return f"Error fetching issue {issue_key}: {e}"

@mcp.tool()
def search_issues(jql: str = "project is not empty ORDER BY created DESC", max_results: int = 50) -> str:
    """List or search tickets using JQL."""
    try:
        tickets = fetch_tickets(jql, max_results)
        if not tickets:
            return "No issues found matching the JQL."
        return "\n".join([f"{t.key}: {t.summary} ({t.status})" for t in tickets])
    except Exception as e:
        return f"Error searching issues: {e}"

@mcp.tool()
def add_comment(issue_key: str, comment: str) -> str:
    """Add a comment to a Jira issue."""
    try:
        add_comment_to_ticket(issue_key, comment)
        return f"Comment added to {issue_key}"
    except Exception as e:
        return f"Error adding comment to {issue_key}: {e}"

@mcp.tool()
def create_issue(project_key: str, summary: str, description: Optional[str] = None, issue_type: str = "Task") -> str:
    """Create a new Jira issue."""
    try:
        res = create_ticket(project_key, summary, description, issue_type)
        return f"Created issue: {res.get('key')}"
    except Exception as e:
        return f"Error creating issue: {e}"

@mcp.tool()
def update_issue(issue_key: str, summary: Optional[str] = None, description: Optional[str] = None) -> str:
    """Update a Jira issue."""
    try:
        res = update_ticket(issue_key, summary, description)
        return f"Updated issue: {issue_key}"
    except Exception as e:
        return f"Error updating issue {issue_key}: {e}"


@mcp.tool()
def transition_issue(issue_key: str, transition_id: str) -> str:
    """Transition a Jira issue to a new status (e.g. 41 for Done)."""
    try:
        jira_transition_issue(issue_key, transition_id)
        return f"Issue {issue_key} transitioned to status (transition_id={transition_id})"
    except Exception as e:
        return f"Error transitioning issue {issue_key}: {e}"


if __name__ == "__main__":
    import os
    # Ensure env is loaded from project root if not already set
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    
    mcp.run(transport="stdio")
