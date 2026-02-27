import pytest
with open('README.md') as file:
    README_CONTENT = file.read()

def test_readme_contains_mcp_server_setup():
    assert 'MCP Server Setup' in README_CONTENT

def test_readme_contains_jira_integration():
    assert 'Jira Integration' in README_CONTENT

def test_readme_contains_configuration_and_deployment():
    assert 'Configuration and Deployment' in README_CONTENT