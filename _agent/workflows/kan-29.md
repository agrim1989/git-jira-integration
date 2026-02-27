---
description: Workflow for KAN-29 - Calculator Application
---

This workflow automates the development, testing, and PR creation for KAN-29.

// turbo
1. Create a new feature branch for KAN-29:
```bash
git checkout -b KAN-29
```

2. Implement the calculator logic in `calculator.py`. 

3. Create unit tests in `tests/test_calculator.py`.

// turbo
4. Run tests to ensure everything is working correctly:
```bash
python3 -m unittest tests/test_calculator.py
```

5. Once tests pass, commit and push the changes:
```bash
git add .
git commit -m "KAN-29: Implement basic calculator application"
git push origin KAN-29
```

6. Create a Pull Request using the MCP.
