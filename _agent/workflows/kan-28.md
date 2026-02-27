---
description: Workflow for KAN-28 - File Downloader and Merger
---

This workflow automates the development, testing, and PR creation for KAN-28.

// turbo
1. Create a new feature branch for KAN-28:
```bash
git checkout -b KAN-28
```

2. Implement the file merger logic in `file_merger.py`. The script should support downloading a list of URLs and merging them into a single file.

3. Create unit tests in `tests/test_file_merger.py` to verify both the downloading and merging functionality.

// turbo
4. Run the newly created tests to ensure everything is working correctly:
```bash
pytest tests/test_file_merger.py
```

5. Once tests pass, commit and push the changes:
```bash
git add .
git commit -m "KAN-28: Implement file downloader and merger with tests"
git push origin KAN-28
```

6. Create a Pull Request using the `custom_github` MCP server.

7. Perform an automated AI code review using the `pr-manager` MCP server:
- Use the `pm_code_review_and_comment` tool with `branch_name="KAN-28"`.
- This will act as a Team Lead/PM to validate the implementation and post feedback.
