"""App configuration from environment."""
import json
import os
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class McpServerConfig(BaseModel):
    """Configuration for one MCP server (for solution generation)."""
    key: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    cwd: str | None = Field(default=None, description="Working directory for the process (default: project root)")
    solution_tool_name: str = Field(default="generate_solution", description="Tool to call with ticket data")


class Settings(BaseSettings):
    """Application settings from env."""
    # Jira
    jira_url: str = Field(default="", alias="JIRA_URL")
    jira_username: str = Field(default="", alias="JIRA_USERNAME")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    jira_subtask_issuetype: str = Field(default="Sub-task", alias="JIRA_SUBTASK_ISSUETYPE")
    # Optional defaults for created sub-tasks (leave empty to not set)
    jira_default_assignee_account_id: str = Field(default="", alias="JIRA_DEFAULT_ASSIGNEE_ACCOUNT_ID")
    jira_default_priority: str = Field(default="", alias="JIRA_DEFAULT_PRIORITY")
    jira_default_subtask_labels: str = Field(default="", alias="JIRA_DEFAULT_SUBTASK_LABELS")  # Comma-separated
    jira_default_due_days: int = Field(default=0, alias="JIRA_DEFAULT_DUE_DAYS")  # 0 = don't set due date
    jira_default_components: str = Field(default="", alias="JIRA_DEFAULT_COMPONENTS")  # Comma-separated component names
    jira_default_fix_version: str = Field(default="", alias="JIRA_DEFAULT_FIX_VERSION")  # Single version name

    # Optional: Groq API key – if set, solution endpoints use Groq instead of MCP. Get key: https://console.groq.com/keys
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")

    # Optional: default MCP server key for /tickets/{id}/solution (used when GROQ_API_KEY is not set)
    default_mcp_server_key: str = Field(default="", alias="DEFAULT_MCP_SERVER_KEY")

    # MCP servers JSON: list of {"key": "...", "command": "...", "args": [...], "env": {...}, "solution_tool_name": "..."}
    mcp_servers_json: str = Field(default="[]", alias="MCP_SERVERS_JSON")

    # GitHub flow: repo to clone/push; token for HTTPS and Create PR API (needs repo scope)
    github_default_repo_url: str = Field(default="", alias="GITHUB_DEFAULT_REPO_URL")
    github_token: str = Field(default="", alias="GITHUB_TOKEN")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def jira_configured(self) -> bool:
        return bool(self.jira_url and self.jira_username and self.jira_api_token)

    @property
    def github_flow_configured(self) -> bool:
        return bool(self.github_token and (self.github_default_repo_url or True))  # repo can come from request

    def get_mcp_servers(self) -> list[McpServerConfig]:
        try:
            data = json.loads(self.mcp_servers_json)
        except json.JSONDecodeError:
            return []
        out: list[McpServerConfig] = []
        for item in data if isinstance(data, list) else []:
            if isinstance(item, dict) and item.get("key") and item.get("command"):
                out.append(McpServerConfig(
                    key=item["key"],
                    command=item["command"],
                    args=item.get("args") or [],
                    env=item.get("env") or {},
                    cwd=item.get("cwd"),
                    solution_tool_name=item.get("solution_tool_name") or "generate_solution",
                ))
        return out


settings = Settings()
