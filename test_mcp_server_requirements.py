import unittest
from unittest.mock import patch
from mcp_server_requirements import research_mcp_server_requirements

class TestMCPserverRequirements(unittest.TestCase):
    @patch('mcp_server_requirements.research_mcp_server_requirements')
    def test_research_mcp_server_requirements(self, mock_research_mcp_server_requirements):
        research_mcp_server_requirements()
        mock_research_mcp_server_requirements.assert_called_once()