import pytest
from jira_api import JiraAPI

@pytest.fixture
def jira_api():
    return JiraAPI()

def test_jira_api(jira_api):
    assert jira_api is not None

def test_create_issue(jira_api):
    issue = jira_api.create_issue('Test Issue', 'This is a test issue')
    assert issue is not None

def test_get_issue(jira_api):
    issue = jira_api.get_issue(1)
    assert issue is not None