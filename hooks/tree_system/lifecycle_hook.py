#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : tree_lifecycle.py
@Description : Automated project tree updater for SessionStart and PreCompact events.
               Ensures .claude/project_tree.md is fresh BEFORE the system prompts are assembled.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-24
"""

import sys
import json
import os
import subprocess

GENERATOR_SCRIPT = "generate_smart_tree.py"

def update_tree(cwd):
    """
    Executes the tree generation script.
    """
    # Resolve script path relative to this hook file, not CWD
    hook_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(hook_dir, GENERATOR_SCRIPT)

    if not os.path.exists(script_path):
        # Fail silently if script is missing to avoid blocking the session
        return

    try:
        subprocess.run(
            [sys.executable, script_path],
            cwd=cwd,
            check=True,
            stdout=subprocess.DEVNULL, # Silence stdout (avoid injecting context)
            stderr=subprocess.PIPE     # Capture stderr for logging if needed
        )
    except subprocess.CalledProcessError as e:
        # If generation fails, we log to stderr but don't crash the hook
        print(f"[TreeUpdater] Failed to update tree: {e.stderr.decode('utf-8', errors='replace')}", file=sys.stderr)
    except Exception as e:
        print(f"[TreeUpdater] Unexpected error: {e}", file=sys.stderr)

def main():
    # Force UTF-8
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

    try:
        if sys.stdin.isatty():
            sys.exit(0)

        input_data = json.load(sys.stdin)
        event_name = input_data.get("hook_event_name", "") # For SessionStart/PreCompact

        if not event_name:
             event_name = input_data.get("hookName", "")

        cwd = input_data.get("cwd", os.getcwd())

        # Trigger update on specific lifecycle events
        if event_name == "SessionStart":
            update_tree(cwd)

            # Advice user to run /update-tree if context is stale
            advice = "💡 提示：如果之前从未使用过 /update-tree 或刚安装 hooks，建议手动执行 /update-tree 以刷新项目结构上下文。"

            print(json.dumps({
                "systemMessage": advice
            }))

            sys.exit(0)

        if event_name == "PreCompact":
            update_tree(cwd)
            print(json.dumps({}))
            sys.exit(0)

        # Fallback for unhandled events
        sys.exit(0)

    except Exception as e:
        # Fail safe
        print(f"[TreeUpdater] Critical Error: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
