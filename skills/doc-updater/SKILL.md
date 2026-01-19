---
description: Update core documentation based on code changes referenced in CLAUDE.md
---

# Document Updater Protocol

This skill analyzes recent code changes and updates the core documentation referenced in `CLAUDE.md`.

## Workflow

1.  **Extract Core Docs**: Read `CLAUDE.md` to find all `@filename.md` references.
2.  **Analyze Changes**: Check git status/diff to see what code has changed.
3.  **Update Docs**: If code changes impact the documentation, update the relevant markdown files.

## Prompt

```markdown
You are a technical documentation specialist. Your task is to keep the project's core documentation in sync with the code.

### 1. Identify Core Documentation
First, read `CLAUDE.md` in the current directory.
Extract all file paths referenced with the `@` syntax (e.g., `@style.md`, `@docs/arch.md`).
These are the **Core Documents**.

### 2. Analyze Code Changes
Run `git status` and `git diff --cached` (or `git diff HEAD~1` if no staged changes) to see recent code modifications.
Identify which modules or logical components have changed.

### 3. Determine Impact
For each **Core Document**, determine if the code changes require a documentation update.
- Did the API change?
- Did the configuration schema change?
- Did the behavior or logic flow change?
- Did the directory structure change?

### 4. Execute Updates
If updates are needed:
1.  Read the content of the target Core Document.
2.  Propose specific text changes to reflect the new code reality.
3.  Use the `Edit` tool to apply changes (Sequential Operations).

**Constraints**:
- Only update documents that are strictly affected.
- Preserve the existing style and format of the documentation.
- If no documentation update is needed, explicitly state: "Documentation is up-to-date with recent changes."
```
