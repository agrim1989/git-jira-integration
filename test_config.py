import pytest
import config

@pytest.fixture
def test_config():
    return config.Config()

def test_config_network_settings(test_config):
    assert hasattr(test_config, 'network_settings')

def test_config_security_protocols(test_config):
    assert hasattr(test_config, 'security_protocols')
