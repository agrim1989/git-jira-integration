"""FastAPI app: fetch Jira tickets, ask solution for a ticket, pass ticket to MCP for solution."""
import logging
from contextlib import asynccontextmanager

import dotenv
dotenv.load_dotenv()

# So Jira ticket fetch logging (INFO/WARNING/ERROR) is visible in the console
logging.getLogger("app").setLevel(logging.INFO)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
import logging

from app.config import settings
from app.routers import github_flow, solution, tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Jira + MCP Solution API",
    description="Fetch Jira tickets, ask for solutions, and pass ticket data to any MCP server for solutions.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(solution.router)
app.include_router(github_flow.router)

# Mount static files
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")

@app.get("/", include_in_schema=False)
def index_redirect():
    if os.path.exists(static_dir):
        return RedirectResponse(url="/ui/")
    return RedirectResponse(url="/api")


# Import inline to avoid circular import issues
from app.models import SettingsRequest, SettingsResponse
import httpx

@app.get("/settings", response_model=SettingsRequest)
def get_settings():
    """Get current configured credentials."""
    return SettingsRequest(
        jira_url=settings.jira_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token,
        github_token=settings.github_token,
    )

@app.post("/settings", response_model=SettingsResponse)
def update_settings(body: SettingsRequest):
    """Validate and save credentials to local .env and update in-memory settings."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    updates = 0
    
    # Validate Jira Credentials if provided
    url = body.jira_url.rstrip('/') if body.jira_url else settings.jira_url
    username = body.jira_username if body.jira_username else settings.jira_username
    token = body.jira_api_token if body.jira_api_token else settings.jira_api_token

    if url and username and token:
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(
                    f"{url}/rest/api/3/myself",
                    auth=(username, token)
                )
                if r.status_code != 200:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=400, detail=f"Jira authentication failed. Please check your URL, Email, and API Token. (Status: {r.status_code})")
        except httpx.RequestError as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Could not connect to Jira URL: {e}")

    if body.jira_url is not None:
        dotenv.set_key(env_file, "JIRA_URL", body.jira_url.rstrip('/'))
        settings.jira_url = body.jira_url.rstrip('/')
        updates += 1
        
    if body.jira_username is not None:
        dotenv.set_key(env_file, "JIRA_USERNAME", body.jira_username)
        settings.jira_username = body.jira_username
        updates += 1
        
    if body.jira_api_token is not None:
        dotenv.set_key(env_file, "JIRA_API_TOKEN", body.jira_api_token)
        settings.jira_api_token = body.jira_api_token
        updates += 1
        
    if body.github_token is not None:
        dotenv.set_key(env_file, "GITHUB_TOKEN", body.github_token)
        settings.github_token = body.github_token
        updates += 1
        
    if updates > 0:
        # Re-initialize the internal clients if necessary.
        logging.getLogger("app").info(f"Updated {updates} settings in .env")
        
    return SettingsResponse(success=True, message=f"Successfully updated {updates} settings.")


@app.get("/api")
def root():
    return {
        "message": "Jira + MCP Solution API",
        "docs": "/docs",
        "endpoints": {
            "tickets": "GET /tickets (list), GET /tickets/{ticket_id} (one)",
            "solution": "POST /tickets/{ticket_id}/solution (ask solution for a ticket)",
            "solution_post_to_jira": "POST /tickets/{ticket_id}/solution/post-to-jira (generate plan+solution, post as Jira comment)",
            "github_flow": "POST /tickets/{ticket_id}/github-flow (branch=Jira ID, AI code+tests, push, PR, Jira comment for review)",
            "code_review": "POST /tickets/{ticket_id}/code-review (find PR for Jira ID, run AI review, post comment on PR)",
            "mcp_solution": "POST /mcp/solution (pass ticket to any MCP server for solution)",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "jira_configured": settings.jira_configured}
