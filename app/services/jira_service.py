"""Jira client for fetching tickets and creating sub-tasks."""
import logging
import re
from typing import Any

import httpx
from jira import JIRA

from app.config import settings
from app.models import SubtaskItem, TicketDetail, TicketSummary

logger = logging.getLogger(__name__)


def is_story_or_epic(ticket: TicketDetail) -> bool:
    """True if the ticket is a Story or Epic (can have sub-tasks in Jira)."""
    it = (ticket.issue_type or "").strip().lower()
    return it in ("story", "epic")


# Default JQL for listing issues (project is not empty avoids empty-JQL 400 on some instances).
DEFAULT_JQL = "project is not empty ORDER BY created DESC"
SEARCH_FIELDS = "summary,status,issuetype,assignee"


def _get_jira_client() -> JIRA:
    """Build JIRA client for Cloud (get_server_info=True enables enhanced_search_issues)."""
    return JIRA(
        server=settings.jira_url.rstrip("/"),
        basic_auth=(settings.jira_username, settings.jira_api_token),
        get_server_info=True,
    )


def _issue_to_dict(issue) -> dict[str, Any]:
    """Turn jira.Issue into the dict shape our extractors expect."""
    return getattr(issue, "raw", issue) if not isinstance(issue, dict) else issue


def _extract_summary(issue: dict[str, Any]) -> TicketSummary:
    fields = issue.get("fields") or {}
    status = (fields.get("status") or {}).get("name")
    itype = (fields.get("issuetype") or {}).get("name")
    assignee = (fields.get("assignee") or {}).get("displayName") or (fields.get("assignee") or {}).get("emailAddress")
    return TicketSummary(
        key=issue.get("key", ""),
        summary=(fields.get("summary") or ""),
        status=status,
        issue_type=itype,
        assignee=assignee,
    )


def _adf_to_markdown(node: dict[str, Any], list_index: int = None) -> str:
    """Recursively convert Jira ADF to Markdown."""
    if not isinstance(node, dict):
        return ""
    
    node_type = node.get("type")
    
    if node_type == "text":
        text = node.get("text", "")
        # Handle marks (bold, italic, code, link)
        marks = node.get("marks", [])
        for mark in marks:
            t = mark.get("type")
            if t == "strong":
                text = f"**{text}**"
            elif t == "em":
                text = f"*{text}*"
            elif t == "code":
                text = f"`{text}`"
            elif t == "link":
                url = mark.get("attrs", {}).get("href", "")
                text = f"[{text}]({url})"
        return text

    content = node.get("content", [])
    parts = []
    
    for i, child in enumerate(content):
        if node_type == "orderedList":
            parts.append(_adf_to_markdown(child, list_index=i+1))
        elif node_type == "bulletList":
            parts.append(_adf_to_markdown(child, list_index=0))
        else:
            parts.append(_adf_to_markdown(child))
            
    if node_type == "paragraph":
        return "".join(parts) + "\n\n"
    elif node_type == "heading":
        level = node.get("attrs", {}).get("level", 1)
        return f"{'#' * level} " + "".join(parts) + "\n\n"
    elif node_type in ("bulletList", "orderedList"):
        return "".join(parts) + "\n"
    elif node_type == "listItem":
        prefix = f"{list_index}. " if list_index else "* "
        # list items usually contain paragraphs, so we strip trailing newlines
        item_text = "".join(parts).strip()
        # Handle multi-line list items by indenting subsequent lines
        indented_text = item_text.replace("\n", "\n  ")
        return f"{prefix}{indented_text}\n"
    elif node_type == "codeBlock":
        lang = node.get("attrs", {}).get("language", "")
        return f"```{lang}\n" + "".join(parts).strip() + "\n```\n\n"
    elif node_type in ("doc", "blockquote", "panel"):
        return "".join(parts)
    elif node_type == "rule":
        return "---\n\n"

    return "".join(parts)


def _extract_detail(issue: dict[str, Any]) -> TicketDetail:
    fields = issue.get("fields") or {}
    desc = fields.get("description")
    if isinstance(desc, dict):
        description = _adf_to_markdown(desc).strip()
    else:
        description = str(desc) if desc is not None else None

    status = (fields.get("status") or {}).get("name")
    itype = (fields.get("issuetype") or {}).get("name")
    assignee = (fields.get("assignee") or {}).get("displayName") or (fields.get("assignee") or {}).get("emailAddress")
    project = (fields.get("project") or {}).get("key")
    subtasks = fields.get("subtasks", [])

    return TicketDetail(
        key=issue.get("key", ""),
        summary=(fields.get("summary") or ""),
        description=description,
        status=status,
        issue_type=itype,
        assignee=assignee,
        project=project,
        created=fields.get("created"),
        updated=fields.get("updated"),
        subtasks=subtasks,
        raw=issue,
    )


def _fetch_tickets_via_rest(
    jql: str,
    max_results: int,
) -> list[TicketSummary]:
    """Fallback: fetch tickets via direct REST. Prefer GET search/jql (recommended by Atlassian)."""
    base = settings.jira_url.rstrip("/")
    auth = (settings.jira_username, settings.jira_api_token)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    # Use comma-separated string for fields; some Jira versions reject array in query string
    fields_str = SEARCH_FIELDS.strip() or "summary,status,issuetype,assignee"
    jql_str = jql or DEFAULT_JQL

    def parse_issues(data: dict) -> list[TicketSummary]:
        issues = data.get("issues") or data.get("values") or []
        return [_extract_summary(i if isinstance(i, dict) else getattr(i, "raw", i)) for i in issues]

    with httpx.Client(timeout=30.0) as client:
        url_jql = f"{base}/rest/api/3/search/jql"
        # 1) GET /rest/api/3/search/jql – recommended; params only (no body)
        logger.info("Jira fetch_tickets: trying GET %s with jql=%s", url_jql, jql_str[:80])
        r = client.get(
            url_jql,
            auth=auth,
            params={"jql": jql_str, "maxResults": max_results, "fields": fields_str},
        )
        logger.info("Jira GET search/jql response: status=%s body=%s", r.status_code, r.text[:500] if r.text else "")
        if r.status_code == 200:
            return parse_issues(r.json())
        # 2) GET without fields (minimal params)
        if r.status_code == 400:
            logger.info("Jira fetch_tickets: trying GET search/jql without fields")
            r2 = client.get(url_jql, auth=auth, params={"jql": jql_str, "maxResults": max_results})
            logger.info("Jira GET search/jql (no fields) response: status=%s body=%s", r2.status_code, r2.text[:500] if r2.text else "")
            if r2.status_code == 200:
                return parse_issues(r2.json())
        # 3) POST /rest/api/3/search/jql – body with jql, maxResults, fields (array ok in JSON body)
        if r.status_code in (400, 404, 410):
            logger.info("Jira fetch_tickets: trying POST %s", url_jql)
            body = {
                "jql": jql_str,
                "maxResults": max_results,
                "fields": [f.strip() for f in fields_str.split(",")],
            }
            r3 = client.post(url_jql, auth=auth, headers=headers, json=body)
            logger.info("Jira POST search/jql response: status=%s body=%s", r3.status_code, r3.text[:500] if r3.text else "")
            if r3.status_code == 200:
                return parse_issues(r3.json())
        # 4) POST /rest/api/3/search (legacy)
        if r.status_code in (400, 404, 410):
            url_legacy = f"{base}/rest/api/3/search"
            logger.info("Jira fetch_tickets: trying POST legacy %s", url_legacy)
            r4 = client.post(
                url_legacy,
                auth=auth,
                headers=headers,
                json={
                    "jql": jql_str,
                    "startAt": 0,
                    "maxResults": max_results,
                    "fields": [f.strip() for f in fields_str.split(",")],
                },
            )
            logger.info("Jira POST legacy search response: status=%s body=%s", r4.status_code, r4.text[:500] if r4.text else "")
            if r4.status_code == 200:
                return parse_issues(r4.json())
        logger.error("Jira fetch_tickets: all REST attempts failed. Last response: status=%s url=%s body=%s", r.status_code, r.url, r.text)
        r.raise_for_status()
        return []


def fetch_tickets(
    jql: str = DEFAULT_JQL,
    max_results: int = 50,
    start_at: int = 0,
) -> list[TicketSummary]:
    """Fetch tickets using jira.enhanced_search_issues(); fallback to direct REST if needed."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured (JIRA_URL, JIRA_USERNAME, JIRA_API_TOKEN)")
    max_results = min(max(1, max_results), 100)
    jql_str = jql or DEFAULT_JQL
    last_error = None
    for use_post in (False, True):
        try:
            method = "POST" if use_post else "GET"
            logger.info("Jira fetch_tickets: trying jira library enhanced_search_issues (use_post=%s)", use_post)
            jira_client = _get_jira_client()
            result = jira_client.enhanced_search_issues(
                jql_str=jql_str,
                maxResults=max_results,
                fields=SEARCH_FIELDS,
                nextPageToken=None,
                use_post=use_post,
            )
            if isinstance(result, dict):
                issues = result.get("issues") or result.get("values") or []
            else:
                issues = list(result) if result is not None else []
            out = []
            for issue in issues or []:
                out.append(_extract_summary(_issue_to_dict(issue)))
            if out:
                logger.info("Jira fetch_tickets: got %d tickets via jira library (%s)", len(out), method)
                return out
            logger.warning("Jira fetch_tickets: jira library (%s) returned 0 issues", method)
        except Exception as e:
            last_error = e
            logger.warning("Jira fetch_tickets: jira library (use_post=%s) failed: %s", use_post, e, exc_info=True)
            continue
    logger.info("Jira fetch_tickets: falling back to direct REST (jira library failed: %s)", last_error)
    try:
        out = _fetch_tickets_via_rest(jql_str, max_results)
        logger.info("Jira fetch_tickets: REST fallback returned %d tickets", len(out))
        return out
    except Exception as e:
        logger.error("Jira fetch_tickets: REST fallback also failed: %s", e, exc_info=True)
        raise


def fetch_ticket(ticket_id: str) -> TicketDetail:
    """Fetch a single ticket by key (GET /rest/api/3/issue/{id})."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    # Use httpx for single-issue GET to avoid pulling in full jira.issue() if needed
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{ticket_id}"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            params={"fields": "summary,description,status,issuetype,assignee,project,created,updated,subtasks"},
        )
        r.raise_for_status()
        issue = r.json()
    return _extract_detail(issue)

def fetch_ticket_comments(ticket_id: str) -> list[dict]:
    """Fetch comments for a single ticket by key."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{ticket_id}/comment"
    with httpx.Client(timeout=30.0) as client:
        r = client.get(
            url,
            auth=(settings.jira_username, settings.jira_api_token)
        )
        r.raise_for_status()
        data = r.json()
    return data.get("comments", [])


def ticket_to_context_string(ticket: TicketDetail) -> str:
    """Serialize ticket for MCP tool context."""
    lines = [
        f"Key: {ticket.key}",
        f"Summary: {ticket.summary}",
        f"Type: {ticket.issue_type or 'N/A'}",
        f"Status: {ticket.status or 'N/A'}",
        f"Assignee: {ticket.assignee or 'Unassigned'}",
        f"Project: {ticket.project or 'N/A'}",
    ]
    if ticket.description:
        lines.append(f"Description: {ticket.description}")
    if ticket.created:
        lines.append(f"Created: {ticket.created}")
    if ticket.updated:
        lines.append(f"Updated: {ticket.updated}")
    return "\n".join(lines)


def _text_to_adf_body(text: str) -> dict:
    """Convert Markdown text to Jira Cloud ADF (Atlassian Document Format)."""
    import re
    blocks = []
    lines = text.split("\n")
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        raw_line = lines[i]
        
        if not line:
            i += 1
            continue
            
        # Code block
        if line.startswith("```"):
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            blocks.append({
                "type": "codeBlock",
                "attrs": {"language": lang or "plain"},
                "content": [{"type": "text", "text": "\n".join(code_lines) if code_lines else " "}]
            })
            i += 1
            continue
            
        # Heading
        m_heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if m_heading:
            level = len(m_heading.group(1))
            blocks.append({
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": m_heading.group(2)}]
            })
            i += 1
            continue
            
        # Bullet List
        if line.startswith("- ") or line.startswith("* "):
            items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                item_text = re.sub(r"^[-*]\s+", "", lines[i].strip())
                
                # bold parsing inside list
                text_nodes = []
                parts = re.split(r'(\*\*.*?\*\*)', item_text)
                for part in parts:
                    if part.startswith("**") and part.endswith("**") and len(part) > 4:
                        text_nodes.append({"type": "text", "text": part[2:-2], "marks": [{"type": "strong"}]})
                    elif part:
                        text_nodes.append({"type": "text", "text": part})
                        
                items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": text_nodes if text_nodes else [{"type": "text", "text": " "}]
                    }]
                })
                i += 1
            blocks.append({
                "type": "bulletList",
                "content": items
            })
            continue

        # Numbered List
        m_ordered = re.match(r"^(\d+)\.\s+(.*)", line)
        if m_ordered:
            items = []
            while i < len(lines):
                m_ord = re.match(r"^(\d+)\.\s+(.*)", lines[i].strip())
                if not m_ord:
                    break
                item_text = m_ord.group(2)
                
                text_nodes = []
                parts = re.split(r'(\*\*.*?\*\*)', item_text)
                for part in parts:
                    if part.startswith("**") and part.endswith("**") and len(part) > 4:
                        text_nodes.append({"type": "text", "text": part[2:-2], "marks": [{"type": "strong"}]})
                    elif part:
                        text_nodes.append({"type": "text", "text": part})
                        
                items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": text_nodes if text_nodes else [{"type": "text", "text": " "}]
                    }]
                })
                i += 1
            blocks.append({
                "type": "orderedList",
                "content": items
            })
            continue
            
        # Paragraph with bold parsing
        text_nodes = []
        parts = re.split(r'(\*\*.*?\*\*)', line)
        for part in parts:
            if part.startswith("**") and part.endswith("**") and len(part) > 4:
                text_nodes.append({"type": "text", "text": part[2:-2], "marks": [{"type": "strong"}]})
            elif part:
                text_nodes.append({"type": "text", "text": part})
        
        blocks.append({
            "type": "paragraph",
            "content": text_nodes if text_nodes else [{"type": "text", "text": line}]
        })
        i += 1
        
    if not blocks:
        blocks = [{"type": "paragraph", "content": [{"type": "text", "text": "(No content)"}]}]
    return {"type": "doc", "version": 1, "content": blocks}


def add_comment_to_ticket(ticket_id: str, body_text: str) -> dict:
    """Add a comment to a Jira issue. Returns the created comment payload."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{ticket_id}/comment"
    body_adf = _text_to_adf_body(body_text)
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            json={"body": body_adf},
        )
        r.raise_for_status()
        return r.json()


def update_issue_description(issue_key: str, description_text: str) -> None:
    """Update the issue's description field (Jira Cloud expects ADF). Fails if Jira is not configured."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{issue_key}"
    description_adf = _text_to_adf_body(description_text or "")
    with httpx.Client(timeout=30.0) as client:
        r = client.put(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            json={"fields": {"description": description_adf}},
        )
        r.raise_for_status()


def parse_suggested_subtasks(solution_text: str) -> list[SubtaskItem]:
    """
    Extract sub-task items (summary + description) from solution text.
    Supports: (1) "Summary | Description" per line, (2) multi-line blocks (summary then indented description),
    (3) fallback APPROACH PLAN lines as summaries (no description).
    """
    text = solution_text or ""
    patterns = [
        r"(?:Suggested\s+sub-tasks|Sub-tasks\s+to\s+create|SUGGESTED\s+SUB-TASKS|Tasks\s+to\s+create|Recommended\s+(?:sub-?)?tasks):\s*\n",
        r"\n3\)\s*SUGGESTED\s+SUB-TASKS:\s*\n",
        r"\n3\.\s*SUGGESTED\s+SUB-TASKS:\s*\n",
    ]
    start = -1
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            start = m.end()
            break
    if start >= 0:
        section = text[start:]
        tasks: list[SubtaskItem] = []
        # Try single-line "Summary | Description" first (only count lines that have a pipe)
        for line in section.split("\n"):
            line_stripped = line.strip()
            if not line_stripped:
                break
            if re.match(r"^(?:Solution|Approach|SOLUTION|APPROACH)\s*:?\s*$", line_stripped, re.IGNORECASE):
                break
            raw = line_stripped
            raw = re.sub(r"^\s*[-*]\s+", "", raw)
            raw = re.sub(r"^\s*\d+[.)]\s+", "", raw)
            if not raw:
                continue
            if "|" in raw:
                parts = raw.split("|", 1)
                summary = (parts[0] or "").strip()[:255]
                description = (parts[1].strip() if len(parts) > 1 and parts[1] else "").strip() or None
                if summary:
                    tasks.append(SubtaskItem(summary=summary, description=description))
        if tasks:
            return tasks

        # Multi-line block: "1. Summary\n   Description\n2. Next\n   Desc" (no pipe on any line)
        lines = section.split("\n")
        current_summary: str | None = None
        current_desc: list[str] = []
        for line in lines:
            stripped = line.strip()
            is_bullet = bool(re.match(r"^\s*(\d+[.)]|[-*])\s+", line))
            if is_bullet and stripped:
                bullet_removed = re.sub(r"^\s*\d+[.)]\s+", "", stripped)
                bullet_removed = re.sub(r"^\s*[-*]\s+", "", bullet_removed)
                if bullet_removed and len(bullet_removed) <= 255:
                    if current_summary:
                        desc_text = "\n".join(current_desc).strip() or None
                        tasks.append(SubtaskItem(summary=current_summary, description=desc_text))
                    current_summary = bullet_removed[:255]
                    current_desc = []
            elif current_summary and stripped:
                current_desc.append(stripped)
        if current_summary:
            desc_text = "\n".join(current_desc).strip() or None
            tasks.append(SubtaskItem(summary=current_summary, description=desc_text))
        if tasks:
            return tasks
    # Fallback: APPROACH PLAN numbered lines as summaries (no description)
    approach = re.search(r"(?:APPROACH\s+PLAN|1\)\s*APPROACH)\s*:?\s*\n(.*?)(?=\n\s*(?:2\)|2\.|SOLUTION|Suggested)|$)", text, re.IGNORECASE | re.DOTALL)
    if approach:
        block = approach.group(1).strip()
        tasks = []
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue
            cleaned = re.sub(r"^\s*\d+[.)]\s+", "", line)
            cleaned = re.sub(r"^\s*[-*]\s+", "", cleaned)
            if cleaned and len(cleaned) <= 255:
                tasks.append(SubtaskItem(summary=cleaned, description=None))
        if tasks:
            return tasks
    return []


def create_subtask(
    parent_issue_key: str,
    project_key: str,
    summary: str,
    *,
    description: str | None = None,
    assignee_account_id: str | None = None,
    priority_name: str | None = None,
    labels: list[str] | None = None,
    duedate: str | None = None,
    components: list[str] | None = None,
    fix_version: str | None = None,
) -> dict:
    """
    Create a sub-task under a Story/Epic. Returns the created issue payload (includes 'key').
    Tries 'Sub-task' then 'Subtask' if the first fails.
    Optional: description (ADF), assignee, priority, labels, duedate (YYYY-MM-DD), components, fix version.
    """
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue"
    summary_trimmed = (summary or "Task").strip()[:255]
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "parent": {"key": parent_issue_key},
        "summary": summary_trimmed,
        "issuetype": {"name": ""},  # set per attempt
    }
    if description and description.strip():
        fields["description"] = _text_to_adf_body(description.strip())
    if assignee_account_id and assignee_account_id.strip():
        fields["assignee"] = {"accountId": assignee_account_id.strip()}
    if priority_name and priority_name.strip():
        fields["priority"] = {"name": priority_name.strip()}
    if labels:
        fields["labels"] = [str(l).strip() for l in labels if str(l).strip()]
    if duedate and str(duedate).strip():
        fields["duedate"] = str(duedate).strip()
    if components:
        fields["components"] = [{"name": str(c).strip()} for c in components if str(c).strip()]
    if fix_version and str(fix_version).strip():
        fields["fixVersions"] = [{"name": str(fix_version).strip()}]

    types_to_try: list[str] = []
    if settings.jira_subtask_issuetype and settings.jira_subtask_issuetype not in types_to_try:
        types_to_try.append(settings.jira_subtask_issuetype)
    for name in ("Sub-task", "Subtask"):
        if name not in types_to_try:
            types_to_try.append(name)
    for subtask_type in types_to_try:
        fields["issuetype"] = {"name": subtask_type}
        payload = {"fields": fields}
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                url,
                auth=(settings.jira_username, settings.jira_api_token),
                json=payload,
            )
            if r.status_code == 200:
                return r.json()
            if r.status_code != 400:
                r.raise_for_status()
            if "Subtask" in subtask_type or "Sub-task" in subtask_type:
                continue
    raise RuntimeError("Jira create sub-task failed: try setting JIRA_SUBTASK_ISSUETYPE in .env to your project's sub-task type name")


def create_ticket(
    project_key: str,
    summary: str,
    description: str | None = None,
    issue_type: str = "Task",
) -> dict:
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue"
    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": (summary or "Task").strip()[:255],
        "issuetype": {"name": issue_type},
    }
    if description and description.strip():
        fields["description"] = _text_to_adf_body(description.strip())
    
    payload = {"fields": fields}
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            json=payload,
        )
        if r.status_code == 201:
            return r.json()
        raise RuntimeError(f"Jira create ticket failed: {r.text}")


def update_ticket(
    ticket_id: str,
    summary: str | None = None,
    description: str | None = None,
) -> dict:
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{ticket_id}"
    fields: dict[str, Any] = {}
    if summary is not None:
        fields["summary"] = summary.strip()[:255]
    if description is not None:
        fields["description"] = _text_to_adf_body(description.strip())
    
    if not fields:
        return {}
        
    payload = {"fields": fields}
    with httpx.Client(timeout=30.0) as client:
        r = client.put(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            json=payload,
        )
        if r.status_code == 204:
            return {"id": ticket_id, "message": "updated"}
        raise RuntimeError(f"Jira update ticket failed: {r.text}")


def transition_issue(issue_key: str, transition_id: str) -> None:
    """Transition a Jira issue to a new status (e.g. '41' for Done)."""
    if not settings.jira_configured:
        raise ValueError("Jira is not configured")
    base = settings.jira_url.rstrip("/")
    url = f"{base}/rest/api/3/issue/{issue_key}/transitions"
    tid = str(transition_id).strip()
    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            url,
            auth=(settings.jira_username, settings.jira_api_token),
            json={"transition": {"id": tid}},
        )
        r.raise_for_status()

