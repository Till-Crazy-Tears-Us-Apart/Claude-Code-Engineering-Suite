---
name: update-tree
description: Manually update the project tree snapshot (.claude/project_tree.md).
allowed-tools: Bash
disable-model-invocation: true
---

# Update Project Tree

Use this command to force a refresh of the project structure file.
This is useful if you created many files and want Claude to "see" them immediately.

## Usage
- `/update-tree` : Updates the tree based on `.claude/tree_config`.

## Implementation
1. Run the generation script.
2. Confirm success.

```bash
python -c "import os, subprocess, sys; script = os.path.expanduser('~/.claude/hooks/tree_system/generate_smart_tree.py'); subprocess.run([sys.executable, script], check=True)"
```
