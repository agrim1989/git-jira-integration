import unittest
from unittest.mock import patch
from readme import get_readme_content

class TestReadme(unittest.TestCase):
    @patch('readme.get_readme_content')
    def test_get_readme_content(self, mock_get_readme_content):
        get_readme_content()
        mock_get_readme_content.assert_called_once()