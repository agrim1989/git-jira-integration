import httpx

class JiraAPIClient:
    """
    A simple client to connect to Jira via its REST API.
    """
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def get_issue(self, issue_key: str) -> dict:
        """Fetch details of a single Jira issue."""
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        response = httpx.get(url, headers=self.headers, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Task") -> dict:
        """Create a new Jira issue."""
        url = f"{self.base_url}/rest/api/3/issue"
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": issue_type}
            }
        }
        response = httpx.post(url, json=payload, headers=self.headers, auth=self.auth)
        response.raise_for_status()
        return response.json()
