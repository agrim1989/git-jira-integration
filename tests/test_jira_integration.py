"""Tests for Jira integration (KAN-57): transition_issue and MCP alignment."""
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import unittest
from unittest.mock import patch, MagicMock

# Import module under test so patch targets resolve
import app.services.jira_service as jira_service_module


class TestJiraTransition(unittest.TestCase):
    """Test transition_issue in jira_service (mocked HTTP)."""

    @patch.object(jira_service_module, "settings")
    @patch.object(jira_service_module, "httpx")
    def test_transition_issue_success(self, mock_httpx, mock_settings):
        mock_settings.jira_configured = True
        mock_settings.jira_url = "https://example.atlassian.net"
        mock_settings.jira_username = "user"
        mock_settings.jira_api_token = "token"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_httpx.Client.return_value.__enter__.return_value = mock_client

        from app.services.jira_service import transition_issue

        transition_issue("KAN-57", "41")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        self.assertIn("/rest/api/3/issue/KAN-57/transitions", call_args[0][0])
        self.assertEqual(call_args[1]["json"], {"transition": {"id": "41"}})

    @patch.object(jira_service_module, "settings")
    def test_transition_issue_not_configured(self, mock_settings):
        mock_settings.jira_configured = False
        from app.services.jira_service import transition_issue
        with self.assertRaises(ValueError) as ctx:
            transition_issue("KAN-57", "41")
        self.assertIn("not configured", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
