# Update Tree (Project Tree Snapshot)

Update Tree generates a text snapshot of the project directory structure and saves it to `.claude/project_tree.md`. This snapshot is then injected into `CLAUDE.md` as a structural navigation map for the AI.

## Core Functions

1. **Smart Filtering**: Supports `.gitignore`-style exclusion rules.
2. **Depth Control**: Supports per-directory traversal depth configuration.
3. **File Visibility**: Controls whether leaf-node files are listed, or only directory structure.
4. **Auto-Injection**: Automatically triggers `hooks/doc_manager/injector.py` to update `CLAUDE.md` after generation.

## Configuration (`.claude/tree_config`)

This skill reads `.claude/tree_config` for rules. If the file does not exist, a default template is created on first run.

### Syntax

- **Exclusion rules**: Prefixed with `!`.
    - `!node_modules` (exclude directories/files named node_modules)
    - `!*.log` (exclude files ending in .log)
- **Inclusion rules**: `[path] [arguments]`
    - `-depth N`: Traversal depth (N=0 for current level only, N=-1 for unlimited recursion).
    - `-if_file true/false`: Whether to display individual files.

### Example

```text
# Exclusions
!__pycache__
!.git
!dist

# Root rule: depth 2, show files
. -depth 2 -if_file true

# Specific directory: depth 1, directories only
src/assets -depth 1 -if_file false

# Source directory: unlimited depth, show files
src/core -depth -1 -if_file true
```

## Proactive Usage Policy

You should run `/update-tree` in the following scenarios:

1. **After file operations**: Batch creation (`touch`), move (`mv`), or deletion (`rm`) of files.
2. **After refactoring**: Module structure changes or directory renames.
3. **After destructive actions**: Any operation that alters the directory layout.
4. **Context drift**: The AI begins referencing non-existent file paths.

## Lifecycle Integration

The tree is automatically updated on three lifecycle events via `hooks/tree_system/lifecycle_hook.py`:

| Event | Trigger |
| :--- | :--- |
| `SessionStart` | Session begins |
| `PreCompact` | Before context compaction |
| `SessionEnd` | Session ends |

## Related Files

| File | Purpose |
| :--- | :--- |
| `SKILL.md` | Protocol definition (loaded by Claude Code) |
| `hooks/tree_system/generate_smart_tree.py` | Core generation script |
| `hooks/tree_system/lifecycle_hook.py` | Lifecycle event handler |
| `hooks/tree_system/default_tree_config.template` | Default configuration template |
