---
description: Manually update the project tree snapshot (.claude/project_tree.md).
allowed-tools: Bash
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
python hooks/tree_system/generate_smart_tree.py
```
