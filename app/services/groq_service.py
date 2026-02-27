"""Groq API client for generating solutions from ticket context. Get key: https://console.groq.com/keys"""
import httpx

from app.config import settings
from app.models import TicketDetail
from app.services.jira_service import is_story_or_epic, ticket_to_context_string

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

# Supported models: llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768, etc.
# See https://console.groq.com/docs/models


PLAN_AND_SOLUTION_SYSTEM = (
    "You are a Senior Technical Leader helping structure solutions for Jira tickets. "
    "Always structure your response in two parts: "
    "1) APPROACH PLAN: A brief numbered list of steps (how to approach the fix). "
    "2) SOLUTION: The detailed solution or recommendations. "
    "Use the ticket context (key, summary, description, status) to give comprehensive, actionable advice.\n"
    "CRITICAL: You must extract and address all the explicit details from the Jira description box, which can contain any content like Technical Specifications, Execution Plan, Scope, Objective, and many more. Ensure your solution fully satisfies all these detailed criteria.\n"
    "CRITICAL: Output must be written in a highly professional, expert developer tone. Use proper technical terminology, structural formatting, and avoid casual or conversational language."
)

PLAN_SOLUTION_SUBTASKS_SYSTEM = (
    "You are a Senior Technical Leader helping structure solutions for Jira tickets. "
    "When the ticket is a Story or Epic, you MUST also suggest sub-tasks with descriptions. "
    "Structure your response in three parts: "
    "1) APPROACH PLAN: A brief numbered list of steps (how to approach the fix). "
    "2) SOLUTION: The detailed solution or recommendations. "
    "3) SUGGESTED SUB-TASKS: Use exactly the heading 'Suggested sub-tasks:' then list each sub-task. "
    "For each sub-task you MUST provide both a title and a description (the description is written into Jira). "
    "Use this format on one line per sub-task: Summary title | Description (1-3 sentences explaining what to do). "
    "Example: 'Add login API | Implement POST /auth/login with JWT validation and rate limiting. Return 401 on invalid credentials.' "
    "Every sub-task line must contain the pipe character | between title and description. "
    "Use the ticket context (key, summary, description, status) to give comprehensive, actionable advice.\n"
    "CRITICAL: You must extract and address all the explicit details from the Jira description box, which can contain any content like Technical Specifications, Execution Plan, Scope, Objective, and many more. Ensure your solution fully satisfies all these detailed criteria.\n"
    "CRITICAL: Output must be written in a highly professional, expert developer tone. Use proper technical terminology, structural formatting, and avoid casual or conversational language."
)


def get_solution_from_groq(
    ticket: TicketDetail,
    question: str,
    *,
    as_plan_and_solution: bool = False,
    include_subtasks_for_story_epic: bool = False,
) -> str:
    """Call Groq API with ticket context and question; return the model response."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set. Get a key at https://console.groq.com/keys")
    ticket_context = ticket_to_context_string(ticket)
    use_subtasks = include_subtasks_for_story_epic and is_story_or_epic(ticket)
    if as_plan_and_solution and use_subtasks:
        system_content = PLAN_SOLUTION_SUBTASKS_SYSTEM
    elif as_plan_and_solution:
        system_content = PLAN_AND_SOLUTION_SYSTEM
    else:
        system_content = (
            "You are a helpful assistant that suggests solutions and recommendations for Jira tickets. "
            "Use the ticket context (key, summary, description, status, etc.) to give concise, actionable advice."
        )
    user_content = f"Ticket context:\n{ticket_context}\n\nUser question: {question}"
    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "stream": False,
    }
    with httpx.Client(timeout=120.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key.strip()}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if r.status_code != 200:
            err_body = r.text
            try:
                err_json = r.json()
                err_body = err_json.get("error", {}).get("message", err_body) or err_json.get("message", err_body)
            except Exception:
                pass
            raise RuntimeError(f"Groq API error {r.status_code}: {err_body}")
        data = r.json()
    choices = data.get("choices") or []
    if not choices:
        return "No response from Groq."
    msg = choices[0].get("message") or {}
    return msg.get("content") or "Empty response from Groq."

def generate_ticket_draft(prompt: str, existing_context: str = None) -> str:
    """Call Groq API to draft a Jira ticket from a one-liner prompt. Returns JSON string."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not set. Get a key at https://console.groq.com/keys")
    
    system_content = (
        "You are an expert Agile Product Manager and Technical Lead. Your job is to take a short one-liner prompt from a user "
        "and draft a comprehensive Jira ticket in highly professional language with structured formatting.\n"
        "Ensure your response uses professional developer terminology, avoids casual language, and defines clear, actionable objectives.\n"
        "Return the response EXACTLY in valid JSON format with keys: 'summary' and 'description'."
    )
    user_content = f"User prompt: {prompt}"
    if existing_context:
        user_content += f"\n\nExisting Ticket Context for Update:\n{existing_context}"
        
    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "stream": False,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key.strip()}", "Content-Type": "application/json"},
            json=payload,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Groq API error {r.status_code}: {r.text}")
        data = r.json()
    
    choices = data.get("choices") or []
    if not choices:
        return "{}"
    msg = choices[0].get("message") or {}
    return msg.get("content") or "{}"
