---
name: file-ops
description: Use this skill for any file system operations, including reading, writing, editing, moving, or deleting files. Enforces strict safety protocols.
user-invocable: false
---

# File Operation Protocols

## 1. Core Safety Protocols

### 1.1 Path Handling Standards
*   **Quoting**: Always use double quotes for file paths (e.g., `cd "C:/My Docs"`).
*   **Separators**: Prefer forward slashes `/`. If backslashes are needed, ensure they are escaped or quoted properly.
*   **Forbidden**: Do not use Windows-native `dir`, `del`, `copy`, `move`. Use POSIX `ls`, `rm`, `cp`, `mv`.

### 1.2 Plan-Verify-Execute (PVE) Workflow
**Mandatory for all filesystem interactions:**
1.  **Plan**: Propose a clear action plan with specific file paths.
2.  **Verify**: Use read-only tools (`Glob`, `Read`) to verify preconditions (file existence, current content) *before* any side-effect operation.
3.  **Execute**: Execute the operation only after verification.

### 1.3 Recursive Context Retrieval Protocol (Auggie-Inspired)
**Trigger**: When analyzing code dependencies or fixing bugs.

1.  **Semantic Query Construction**:
    *   Do NOT just grep for exact matches.
    *   Use NL to formulate 3-point queries: *Where* (location), *What* (definition), *How* (usage).

2.  **Definition-Chain Verification**:
    *   Found `funcA()` call? -> Find `funcA` definition.
    *   `funcA` uses `InterfaceB`? -> Find `InterfaceB` definition.
    *   `InterfaceB` extends `BaseC`? -> Find `BaseC` definition.
    *   *Stop Condition*: When you hold the **Full Type Signature** of all interacting components.

3.  **Completeness Check**:
    *   If context is partial, explicitly list missing parts using `TodoWrite` (in `CHINESE/简体中文` only).
    *   If ambiguous, use `AskUserQuestion` (in `CHINESE/简体中文` only) to align boundaries.

### 1.4 Execution Protocol (Type 1)
*   **Silence**: Execute tools silently. Do not chat between tool calls unless necessary.
*   **Concurrency**: Default to serial. Parallel permitted for independent, non-conflicting read operations.
*   **Parameter Integrity**: STRICTLY check `file_path` and `old_string`/`new_string` before calling.

---

## 2. Advanced Reading Protocols

### 2.1 Streaming Bulk Read Protocol
**Trigger**: When reading 2 or more files.
1.  **Manifest**: List target files using `Glob` or `ls`.
2.  **Instruction**: Generate a series of `Read` calls serially.
3.  **Execution**: Execute one by one without intermediate dialogue.
4.  **Fallback**: If `file_path` errors occur, switch to interactive one-by-one mode.

---

## 3. Robust File Editing Protocol

### 3.1 Read-Modify-Read Cycle (Mandatory)
1.  **Pre-Read**: Read the file to confirm context (silently).
2.  **Modify**: Execute `Edit` or `MultiEdit`.
3.  **Post-Read**: Read the file again to verify the change (silently).

### 3.2 Escalation Path for Edit Failures
If `Edit` fails with "String to replace not found":
1.  **Silent Grep**: `Grep` for the `new_string` to see if it's already there.
    *   *Found*: Abort, report success.
2.  **Scrutiny**: Re-examine `old_string` for whitespace/indentation mismatches. Retry once.
3.  **MultiEdit Degradation**: Degrade `MultiEdit` to single `Edit` calls.
4.  **RMWR (Last Resort)**: Request permission to use Read-Modify-Write-Read (overwrite entire file).

