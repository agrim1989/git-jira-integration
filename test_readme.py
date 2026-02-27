import pytest
from unittest.mock import patch
from io import StringIO
import sys
import os

@pytest.fixture
def test_readme():
    with open('README.md', 'r') as f:
        yield f.read()

def test_readme_contents(test_readme):
    assert 'MCP server' in test_readme
