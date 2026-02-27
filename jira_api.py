import requests
from typing import Dict

class JiraAPI:
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token

    def create_issue(self, issue_data: Dict[str, str]) -> Dict[str, str]:
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(self.base_url + '/issue', headers=headers, json=issue_data)
        return response.json()

    def get_project(self, project_id: str) -> Dict[str, str]:
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get(self.base_url + f'/project/{project_id}', headers=headers)
        return response.json()

    def update_issue(self, issue_id: str, issue_data: Dict[str, str]) -> Dict[str, str]:
        headers = {
            'Authorization': f'Bearer {self.auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.put(self.base_url + f'/issue/{issue_id}', headers=headers, json=issue_data)
        return response.json()