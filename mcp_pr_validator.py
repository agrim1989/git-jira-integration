"""
MCP server that validates a PR by running test cases and sharing results.
"""
from mcp.server.fastmcp import FastMCP
import subprocess
import tempfile
import pathlib
import os

mcp = FastMCP("pr-validator-mcp")

@mcp.tool()
def run_pr_tests(repo_url: str, branch_name: str, test_command: str) -> str:
    """
    Validates a PR by cloning the repo, checking out the given branch,
    and running the test command. Returns the test execution output.
    
    Args:
        repo_url: The full HTTPS URL of the git repository.
        branch_name: The branch name of the PR.
        test_command: The command to run the tests (e.g., "pytest", "npm test").
    """
    with tempfile.TemporaryDirectory() as tempd:
        try:
            # 1. Clone the repo
            subprocess.run(["git", "clone", repo_url, tempd], check=True, capture_output=True)
            
            # 2. Checkout the branch
            subprocess.run(["git", "checkout", branch_name], cwd=tempd, check=True, capture_output=True)
            
            # 3. Run the tests
            result = subprocess.run(
                test_command, 
                shell=True, 
                cwd=tempd, 
                capture_output=True, 
                text=True
            )
            
            # 4. Share result
            output = f"Command: {test_command}\nExit Code: {result.returncode}\n\n"
            output += f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            return output
            
        except subprocess.CalledProcessError as e:
            return f"Failed during git operation. Return code: {e.returncode}\nStderr: {e.stderr.decode('utf-8') if e.stderr else str(e)}"
        except Exception as e:
            return f"Error executing tests: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
