import pytest
from pathlib import Path

def test_requirements_exists():
    assert Path('requirements.txt').exists()