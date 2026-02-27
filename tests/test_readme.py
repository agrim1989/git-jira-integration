import pytest
import os

def test_readme_exists():
    assert os.path.exists('README.md')

def test_readme_content():
    with open('README.md', 'r') as f:
        content = f.read()
    assert 'Jira API' in content