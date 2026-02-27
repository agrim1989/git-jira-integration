import unittest
from unittest.mock import patch, MagicMock
import httpx
from jira_api_client import JiraAPIClient

class TestJiraAPIClient(unittest.TestCase):
    def setUp(self):
        self.client = JiraAPIClient("https://example.atlassian.net", "user@example.com", "fake_token")

    @patch("jira_api_client.httpx.get")
    def test_get_issue_success(self, mock_get):
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "10097", "key": "KAN-23", "fields": {"summary": "Test Title"}}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Execute
        result = self.client.get_issue("KAN-23")

        # Assert
        self.assertEqual(result["key"], "KAN-23")
        self.assertEqual(result["fields"]["summary"], "Test Title")
        mock_get.assert_called_once_with(
            "https://example.atlassian.net/rest/api/3/issue/KAN-23", 
            headers=self.client.headers, 
            auth=self.client.auth
        )

    @patch("jira_api_client.httpx.get")
    def test_get_issue_failure(self, mock_get):
        # Configure the mock to simulate HTTP Error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())
        mock_get.return_value = mock_response

        # Execute & Assert
        with self.assertRaises(httpx.HTTPStatusError):
            self.client.get_issue("INVALID-123")

    @patch("jira_api_client.httpx.post")
    def test_create_issue_success(self, mock_post):
        # Configure the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "10098", "key": "KAN-24"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Execute
        result = self.client.create_issue("KAN", "Create API to connect to Jira")

        # Assert
        self.assertEqual(result["key"], "KAN-24")
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "https://example.atlassian.net/rest/api/3/issue")
        self.assertEqual(kwargs["json"]["fields"]["summary"], "Create API to connect to Jira")

if __name__ == "__main__":
    unittest.main()
