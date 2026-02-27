import pytest
import os

def test_requirements_exists():
    assert os.path.exists('requirements.txt')

def test_requirements_content():
    with open('requirements.txt', 'r') as f:
        content = f.read()
    assert 'jira' in content