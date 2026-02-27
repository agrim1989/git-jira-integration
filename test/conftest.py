import pytest
from mcp_server import MCPServer

def test_mcp_server_setup_teardown():
    mcp_server = MCPServer()
    mcp_server.setup()
    yield
    mcp_server.teardown()