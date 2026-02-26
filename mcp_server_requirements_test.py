import unittest
from mcp_server_requirements import get_mcp_server_requirements

class TestMCPserverRequirements(unittest.TestCase):
    def test_get_mcp_server_requirements(self):
        requirements = get_mcp_server_requirements()
        self.assertIsNotNone(requirements)