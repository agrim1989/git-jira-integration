import pytest
from pathlib import Path

def test_docs_setup_exists():
    assert Path('docs/setup.md').exists()