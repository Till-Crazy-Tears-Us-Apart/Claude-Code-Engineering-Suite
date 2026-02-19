# Technical Execution Reference

**Strictly adhere to the protocols defined in the specialized Skills.** Do not rely on defaults.

*   **File Operations**: See `skills/file-ops`. **Mandatory**: PVE Workflow, Streaming Bulk Read, Robust Read-Modify-Read.
*   **Git Workflow**: See `skills/git-workflow`. **Mandatory**: Conventional Commits, Dangerous Ops Confirmation.
*   **Debugging**: See `skills/systematic-debugging`. **Mandatory**: Root Cause Analysis -> Hypothesis -> Fix.
*   **TDD**: See `skills/test-driven-development`. **Mandatory**: RED -> GREEN -> REFACTOR.
*   **Tool Guide**: See `skills/tool-guide`. **Reference**: MCP Tool Selection Strategy.
*   **Doc Updater**: See `skills/doc-updater`. **Mandatory**: Keep `CLAUDE.md` core docs in sync with code changes.
*   **Update Tree**: See `skills/update-tree`. **Mandatory**: Keep `.claude/project_tree.md` fresh after batch ops.
*   **Update Logic Index**: See `skills/update-logic-index`. **Mandatory**: Update `.claude/logic_tree.md` after major refactors.
*   **Hooks System**:
    *   `pre_tool_guard.py`: Enforces Path Security, Code Hygiene, and Environment Safety.
    *   `context_manager.py`: Manages Session Persistence and State Snapshots.
    *   `enforcer_hook.py`: Enforces persona constraints and UserPromptSubmit protocols.
    *   `lifecycle_hook.py`: Manages SessionStart tree injection and update reminders.
*   **GitHub CLI Integration**: Verified `gh` installation. **Mandatory**: Use `gh` for repository management, issue tracking, and PR operations. **Safety Constraint**: Only use `gh` for **Read-Only** metadata retrieval unless **explicit confirmation** is provided for **Destructive Actions**.
