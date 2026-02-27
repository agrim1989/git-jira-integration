import pytest
import deployment
from unittest.mock import patch

@pytest.fixture
def test_deployment():
    return deployment.Deployment()

def test_deployment_plan(test_deployment):
    assert hasattr(test_deployment, 'plan')

def test_deployment_execute(test_deployment):
    with patch('deployment Deployment.execute') as mock_execute:
        test_deployment.execute()
        mock_execute.assert_called_once()
