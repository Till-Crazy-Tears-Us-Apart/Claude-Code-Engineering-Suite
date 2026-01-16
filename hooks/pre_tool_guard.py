#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : pre_tool_guard.py
@Description : PreToolUse hook for path validation, snake_case correction, and Bash environment enforcement.
               Features:
               1. Absolute Path Check: Warns on absolute paths for modification tools.
               2. Snake Case Guard: Smartly detects and corrects kebab-case to snake_case.
               3. Bash Environment Guard: Auto-injects POSIX/Python/Mamba environment setup into Bash commands.
               4. Agent Speed Bump: Intercepts high-cost agent calls for user confirmation.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-10
"""

import sys
import json
import re
import os

# Tools that are allowed to use absolute paths (Read-only tools)
READ_ONLY_TOOLS = {"Read", "Glob", "Grep", "Search"}

# Compiled regex for performance
PYTHON_RELATED_PATTERN = re.compile(
    r'\b(python3?|pip3?|pytest|uv|poetry|pdm|conda|mamba|ipython|jupyter|twine|tox)\b|\.py\b',
    re.IGNORECASE
)

# -------------------------------------------------------------------------
# Bash Environment Injection Templates
# -------------------------------------------------------------------------
BASH_PREAMBLE = """
if [ -f ".env_setup.sh" ]; then
    source ".env_setup.sh";
else
    if command -v mamba >/dev/null 2>&1; then
        eval "$(mamba shell hook --shell=bash 2>/dev/null)";
    elif command -v conda >/dev/null 2>&1; then
        eval "$(conda shell.bash hook 2>/dev/null)";
    fi;
fi;
"""

def is_python_related(command):
    """Check if the command involves Python execution."""
    return bool(PYTHON_RELATED_PATTERN.search(command))

def is_absolute_path(path):
    """Check if path is absolute in a cross-platform way."""
    # On Windows, a path like \Users\foo is absolute on current drive but not fully qualified.
    # os.path.abspath resolves this, but here we just want to know if user provided an abs path.
    return os.path.isabs(path)

def path_is_contained(inner_path, root_path):
    """
    Check if inner_path is inside root_path using rigorous path resolution.
    Resolves symlinks and normalizes case.
    """
    try:
        abs_inner = os.path.realpath(inner_path)
        abs_root = os.path.realpath(root_path)
        return os.path.commonpath([abs_root, abs_inner]) == abs_root
    except ValueError:
        # Can happen on Windows if paths are on different drives
        return False

def to_snake_case(path):
    """Convert path basename from kebab-case to snake_case."""
    directory, filename = os.path.split(path)
    new_filename = filename.replace('-', '_')
    return os.path.join(directory, new_filename)

def has_kebab_case(path):
    """Check if the filename part contains hyphens."""
    _, filename = os.path.split(path)
    return '-' in filename

def inject_bash_env(original_command):
    """
    Injects environment variables and activation scripts into the bash command.
    """
    if "PYTHONIOENCODING" in original_command and "miniforge3" in original_command:
        return None

    clean_preamble = BASH_PREAMBLE.strip().replace('\n', ' ')
    env_vars = ""

    if is_python_related(original_command):
        env_vars = 'export PYTHONIOENCODING="utf-8"; '
    else:
        # Lazy import platform only when needed
        import platform
        if platform.system() == "Windows":
            env_vars = 'chcp.com 65001 >/dev/null 2>&1 && '

    return f"{env_vars}{clean_preamble} {original_command}"

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        cwd = input_data.get("cwd", os.getcwd())

        # ---------------------------------------------------------
        # Logic 0: Bash Environment Auto-Correction
        # ---------------------------------------------------------
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            new_command = inject_bash_env(command)

            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    # JIT Context Injection for Bash
                    "additionalContext": "<system_reminder>Bash Constraint: Use POSIX syntax. Ensure all paths are relative.</system_reminder>"
                }
            }

            if new_command:
                new_input = tool_input.copy()
                new_input["command"] = new_command
                response["hookSpecificOutput"]["updatedInput"] = new_input
                response["hookSpecificOutput"]["permissionDecisionReason"] = f"🛡️ 环境自动修正：已注入 PYTHONIOENCODING 及 Mamba 激活脚本。\n(原: {command[:20]}...)"

            print(json.dumps(response))
            sys.exit(0)

        # ---------------------------------------------------------
        # Logic 0.5: Agent "Speed Bump" & Plan Config
        # ---------------------------------------------------------
        if tool_name == "Task":
            subagent = tool_input.get("subagent_type", "")

            # [NEW] Enforce Chinese language for Plan agent
            if subagent == "Plan":
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "additionalContext": "<system_reminder>IMPORTANT: You MUST generate the plan content in Simplified Chinese (简体中文). Do NOT use English for the plan description.</system_reminder>"
                    }
                }))
                sys.exit(0)

            # Intercept high-level agents (Explore, general-purpose)
            if subagent in ["Explore", "general-purpose"]:
                 print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": f"🛑 Agent 拦截警告：\n即将启动 '{subagent}' 代理。\n耗时操作需确认。\n[y] 允许 Agent 执行\n[n] 拒绝 (转为手动扁平化执行)"
                    }
                }))
                 sys.exit(0)

        # ---------------------------------------------------------
        # Logic 0.6: Edit/Write Safety Context (Accumulator)
        # ---------------------------------------------------------
        additional_context_buffer = []

        if tool_name in ["Edit", "Write"]:
            path = tool_input.get("file_path", "")
            if path:
                # Check for lock files
                if "lock" in path:
                    additional_context_buffer.append("Warning: You are editing a lock file (e.g., package-lock.json). Manual edits may be overwritten.")

                # Check for strict snake_case requirement (Soft reminder for Edit, Hard for Write is below)
                if has_kebab_case(path) and tool_name == "Edit":
                    additional_context_buffer.append("Warning: File uses kebab-case. Prefer snake_case for new files.")

        # ---------------------------------------------------------
        # Path Logic
        # ---------------------------------------------------------
        file_path = tool_input.get("file_path") or tool_input.get("path")
        if not file_path:
            # If no path, we can't do path logic.
            # But if we have accumulated context, we should output it?
            # Unlikely to have context without path (as context logic depends on path).
            sys.exit(0)

        # Helper to attach context
        def attach_context(response_dict):
            if additional_context_buffer:
                ctx_str = "<system_reminder>" + " ".join(additional_context_buffer) + "</system_reminder>"
                response_dict["hookSpecificOutput"]["additionalContext"] = ctx_str
            return response_dict

        # ---------------------------------------------------------
        # Logic 1: Absolute Path Check & Correction
        # ---------------------------------------------------------
        if is_absolute_path(file_path):
            if path_is_contained(file_path, cwd):
                # Case 1: Absolute path INSIDE project -> Auto-convert to relative
                rel_path = os.path.relpath(file_path, cwd)
                new_input = tool_input.copy()
                if "file_path" in new_input: new_input["file_path"] = rel_path
                if "path" in new_input: new_input["path"] = rel_path

                response = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": f"🛡️ 路径优化：将绝对路径转换为相对路径 '{rel_path}' (项目内文件安全)",
                        "updatedInput": new_input
                    }
                }
                print(json.dumps(attach_context(response)))
                sys.exit(0)
            else:
                # Case 2: Absolute path OUTSIDE project -> Block/Ask
                if tool_name not in READ_ONLY_TOOLS:
                    response = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "ask",
                            "permissionDecisionReason": f"⚠️ 检测到项目外绝对路径: '{file_path}'。\n工作目录: {cwd}\n为了安全，修改外部文件需确认。"
                        }
                    }
                    print(json.dumps(attach_context(response)))
                    sys.exit(0)

        # ---------------------------------------------------------
        # Logic 2: Smart Snake Case Correction
        # ---------------------------------------------------------
        if has_kebab_case(file_path):
            original_path = file_path
            snake_path = to_snake_case(file_path)

            # Check existence using absolute paths relative to CWD
            abs_original = os.path.abspath(os.path.join(cwd, original_path))
            abs_snake = os.path.abspath(os.path.join(cwd, snake_path))

            exists_original = os.path.exists(abs_original)
            exists_snake = os.path.exists(abs_snake)

            if exists_original and exists_snake:
                response = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": f"⚠️ 命名歧义警告：同时存在 '{original_path}' 和 '{snake_path}'。\n建议使用 snake_case。"
                    }
                }
                print(json.dumps(attach_context(response)))
                sys.exit(0)

            elif not exists_original and exists_snake:
                new_input = tool_input.copy()
                if "file_path" in new_input: new_input["file_path"] = snake_path
                if "path" in new_input: new_input["path"] = snake_path

                response = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": f"自动纠错：将 '{original_path}' 修正为存在的 '{snake_path}'",
                        "updatedInput": new_input
                    }
                }
                print(json.dumps(attach_context(response)))
                sys.exit(0)

            elif not exists_snake and tool_name == "Write":
                 response = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"命名规范强制：试图创建非 snake_case 文件 '{original_path}'。\n请使用 '{snake_path}' 重试。"
                    }
                }
                 print(json.dumps(attach_context(response)))
                 sys.exit(0)

        # ---------------------------------------------------------
        # Final Fallthrough: If we have context but no blocks triggered
        # ---------------------------------------------------------
        if additional_context_buffer:
            response = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    # No reason needed for simple allow
                }
            }
            print(json.dumps(attach_context(response)))
            sys.exit(0)

        sys.exit(0)

    except Exception as e:
        # Fallback: Just let it pass if hook fails, but log to stderr
        print(f"Error in pre_tool_guard.py: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
