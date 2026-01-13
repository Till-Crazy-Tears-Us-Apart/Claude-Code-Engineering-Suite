#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : pre_tool_guard.py
@Description : PreToolUse hook for path validation, snake_case correction, and Bash environment enforcement.
               Features:
               1. Absolute Path Check: Warns on absolute paths for modification tools.
               2. Snake Case Guard: Smartly detects and corrects kebab-case to snake_case.
               3. Bash Environment Guard: Auto-injects POSIX/Python/Mamba environment setup into Bash commands.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-10
"""

import sys
import json
import re
import os
import platform

# Tools that are allowed to use absolute paths (Read-only tools)
READ_ONLY_TOOLS = {"Read", "Glob", "Grep", "Search", "ls", "cat", "find"}

# -------------------------------------------------------------------------
# Bash Environment Injection Templates
# -------------------------------------------------------------------------
# Auto-detection logic:
# 1. Check for project-specific setup (.env_setup.sh) and source it if exists.
# 2. If no project setup, check for conda/mamba availability and initialize.
# 3. Always ensure PYTHONIOENCODING is UTF-8.

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
    # Matches common python tools and .py files
    # Word boundaries (\b) prevent matching 'typython' or 'pyping'
    pattern = r'\b(python3?|pip3?|pytest|uv|poetry|pdm|conda|mamba|ipython|jupyter|twine|tox)\b|\.py\b'
    return bool(re.search(pattern, command, re.IGNORECASE))

def is_absolute_path(path):
    """Check if path is absolute in a cross-platform way."""
    return os.path.isabs(path)

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
    Avoids double injection if already present.
    """
    # Simple heuristic to check if already injected
    if "PYTHONIOENCODING" in original_command and "miniforge3" in original_command:
        return None # Already looks good

    # Clean up the preamble to be a single line or minimal block
    clean_preamble = BASH_PREAMBLE.strip().replace('\n', ' ')

    # Conditional Injection
    env_vars = ""
    if is_python_related(original_command):
        # Case A: Python tools -> Force UTF-8 via env var
        env_vars = 'export PYTHONIOENCODING="utf-8"; '
    else:
        # Case B: Native Windows commands (ping, ipconfig) -> Force Console Code Page 65001 (UTF-8)
        # We check platform to be safe, though this script is primarily for your Windows environment.
        if platform.system() == "Windows":
            # Use chcp.com explicitly as 'chcp' might not be found in Git Bash PATH
            env_vars = 'chcp.com 65001 >/dev/null 2>&1 && '

    # Combine: Env Vars + Preamble + Original Command
    return f"{env_vars}{clean_preamble} {original_command}"

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        # 1. Read Input
        input_data = json.load(sys.stdin)
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        # ---------------------------------------------------------
        # Logic 0: Bash Environment Auto-Correction
        # ---------------------------------------------------------
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            new_command = inject_bash_env(command)

            if new_command:
                # Construct updated input
                new_input = tool_input.copy()
                new_input["command"] = new_command

                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow", # Auto-allow the injection
                        "permissionDecisionReason": f"🛡️ 环境自动修正：已注入 PYTHONIOENCODING 及 Mamba 激活脚本。\n(原: {command[:20]}...)",
                        "updatedInput": new_input
                    }
                }
                print(json.dumps(output))
                sys.exit(0)
            else:
                # Command looks safe, pass through to other checks (if any apply to Bash?)
                # Bash usually doesn't have 'file_path', so we might exit here.
                sys.exit(0)

        # ---------------------------------------------------------
        # Path Logic (For File Tools: Read, Write, Edit, Glob, etc.)
        # ---------------------------------------------------------
        # We generally check 'file_path', but sometimes it might be 'path' (Glob/Grep)
        file_path = tool_input.get("file_path") or tool_input.get("path")

        if not file_path:
            sys.exit(0)

        # ---------------------------------------------------------
        # Logic 1: Absolute Path Check & Correction
        # ---------------------------------------------------------
        if is_absolute_path(file_path):
            cwd = input_data.get("cwd", os.getcwd())

            # Check if path is inside project
            # normalize paths to avoid case mismatch issues on Windows
            norm_file = os.path.normcase(os.path.normpath(file_path))
            norm_cwd = os.path.normcase(os.path.normpath(cwd))

            is_inside = norm_file.startswith(norm_cwd)

            if is_inside:
                # Case 1: Absolute path INSIDE project -> Auto-convert to relative
                rel_path = os.path.relpath(file_path, cwd)

                # Check READ_ONLY status again if needed, but here we just fix the path
                # If we want to allow modification inside project without asking:
                new_input = tool_input.copy()
                if "file_path" in new_input:
                    new_input["file_path"] = rel_path
                if "path" in new_input:
                    new_input["path"] = rel_path

                # If it's a modification tool, we SILENTLY allow it because it's safe (inside project)
                # But we still updated the path to relative for better tool behavior
                if tool_name not in READ_ONLY_TOOLS:
                     output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "allow",
                            "permissionDecisionReason": f"🛡️ 路径优化：将绝对路径转换为相对路径 '{rel_path}' (项目内文件安全)",
                            "updatedInput": new_input
                        }
                    }
                     print(json.dumps(output))
                     sys.exit(0)
                else:
                    # Read-only tools with absolute path inside project -> also convert for consistency
                    # or just let them pass. Let's convert to be safe/clean.
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "allow",
                            "updatedInput": new_input
                        }
                    }
                    print(json.dumps(output))
                    sys.exit(0)

            else:
                # Case 2: Absolute path OUTSIDE project -> Block/Ask
                if tool_name not in READ_ONLY_TOOLS:
                    output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "ask",
                            "permissionDecisionReason": f"⚠️ 检测到项目外绝对路径: '{file_path}'。\n工作目录: {cwd}\n为了安全，修改外部文件需确认。"
                        }
                    }
                    print(json.dumps(output))
                    sys.exit(0)

        # ---------------------------------------------------------
        # Logic 2: Smart Snake Case Correction
        # ---------------------------------------------------------
        if has_kebab_case(file_path):
            original_path = file_path
            snake_path = to_snake_case(file_path)

            cwd = input_data.get("cwd", os.getcwd())
            abs_original = os.path.join(cwd, original_path) if not os.path.isabs(original_path) else original_path
            abs_snake = os.path.join(cwd, snake_path) if not os.path.isabs(snake_path) else snake_path

            exists_original = os.path.exists(abs_original)
            exists_snake = os.path.exists(abs_snake)

            if exists_original and exists_snake:
                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "ask",
                        "permissionDecisionReason": f"⚠️ 命名歧义警告：\n检测到同时存在 '{original_path}' 和 '{snake_path}'。\nLLM 试图访问 kebab-case 版本，但这可能是幻觉。\n请确认是否继续？(建议统一使用 snake_case)"
                    }
                }
                print(json.dumps(output))
                sys.exit(0)

            elif not exists_original and exists_snake:
                new_input = tool_input.copy()
                if "file_path" in new_input:
                    new_input["file_path"] = snake_path
                if "path" in new_input:
                    new_input["path"] = snake_path

                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "allow",
                        "permissionDecisionReason": f"自动纠错：将 '{original_path}' 修正为存在的 '{snake_path}'",
                        "updatedInput": new_input
                    }
                }
                print(json.dumps(output))
                sys.exit(0)

            elif exists_original and not exists_snake:
                sys.exit(0)

            else:
                if tool_name == "Write":
                     output = {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": f"命名规范强制：试图创建非 snake_case 文件 '{original_path}'。\n请使用 '{snake_path}' 重试。"
                        }
                    }
                     print(json.dumps(output))
                     sys.exit(0)
                sys.exit(0)

        sys.exit(0)

    except Exception as e:
        print(f"Error in pre_tool_guard.py: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
