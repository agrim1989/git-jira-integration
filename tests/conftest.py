import pytest

@pytest.fixture
def jira_api():
    # Mock Jira API for testing
    class MockJiraAPI:
        def create_issue(self, summary, description):
            return {'id': 1, 'summary': summary, 'description': description}
        def get_issue(self, id):
            return {'id': id, 'summary': 'Test Issue', 'description': 'This is a test issue'}
    return MockJiraAPI()