import pytest
import setuptools

def test_setup_exists():
    import setup
    assert hasattr(setup, 'setup')