#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : context_manager.py
@Description : Automated context persistence and restoration system.
               - PreCompact: Generates .compact_args.md snapshot automatically.
               - SessionStart: Injects .compact_args.md content into new sessions.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-10
"""

import sys
import json
import os
import subprocess
from datetime import datetime

SNAPSHOT_FILE = ".compact_args.md"

def generate_snapshot(cwd):
    """
    Generates the snapshot file using git status and file listings.
    Replicates the logic of the original /prepare-compact command.
    """
    try:
        # 1. Capture Git Info
        # Branch
        branch = "Unknown"
        last_commit = "Unknown"
        git_check = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=cwd, capture_output=True)

        if git_check.returncode == 0:
            # Get Branch
            res_branch = subprocess.run(["git", "branch", "--show-current"], cwd=cwd, capture_output=True, encoding='utf-8', errors='replace')
            if res_branch.returncode == 0:
                branch = res_branch.stdout.strip()

            # Get Last Commit
            res_commit = subprocess.run(["git", "log", "-1", "--pretty=format:%h - %s (%an)"], cwd=cwd, capture_output=True, encoding='utf-8', errors='replace')
            if res_commit.returncode == 0:
                last_commit = res_commit.stdout.strip()

            # Get Status
            status_output = subprocess.run(["git", "status", "--short"], cwd=cwd, capture_output=True, encoding='utf-8', errors='replace').stdout
            if not status_output.strip():
                status_output = "(工作区干净，无未提交变更)"
        else:
            status_output = "--- 非 Git 仓库 ---\n"
            # Fallback listing
            try:
                file_list = []
                for root, dirs, files in os.walk(cwd):
                    # Skip .git and hidden dirs
                    dirs[:] = [d for d in dirs if not d.startswith('.')]

                    depth = root[len(cwd):].count(os.sep)
                    if depth < 2:
                        for f in files:
                            if not f.startswith('.'):
                                rel_path = os.path.relpath(os.path.join(root, f), cwd)
                                file_list.append(rel_path)
                status_output += "\n".join(file_list[:30])
                if len(file_list) > 30:
                    status_output += "\n... (文件过多已截断)"
            except Exception as e:
                status_output += f"Error listing files: {e}"

        # 2. Generate Content
        # Dynamic Reading List Generation
        reading_list = []

        # Priority Docs
        priority_files = ["CLAUDE.md", "README.md", "CONTRIBUTING.md", "requirements.txt", "pyproject.toml", "package.json"]
        for f in priority_files:
            if os.path.exists(os.path.join(cwd, f)):
                desc = "系统指令" if f == "CLAUDE.md" else "项目文档/配置"
                reading_list.append(f"- `[{desc}]` {f}")

        # Scan for project directories (exclude hidden and venv)
        try:
            ignore_dirs = {'.git', '.idea', '.vscode', '__pycache__', 'node_modules', 'venv', 'env', 'dist', 'build'}
            dirs = [d for d in os.listdir(cwd)
                   if os.path.isdir(os.path.join(cwd, d))
                   and not d.startswith('.')
                   and d not in ignore_dirs]

            if dirs:
                # Simple Heuristic: Sort 'src', 'lib', 'core' to front
                dirs.sort(key=lambda x: (0 if x in ['src', 'lib', 'core', 'app', 'skills', 'hooks'] else 1, x))
                dir_str = ", ".join([f"`{d}/`" for d in dirs[:15]])
                reading_list.append(f"- **目录结构**: {dir_str}")
        except Exception:
            pass

        reading_list_str = "\n".join(reading_list)

        content = f"""# 🔄 自动上下文快照 (Automated Context Snapshot)
> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 项目状态概览 (Project State)
- **当前分支**: `{branch}`
- **最近提交**: `{last_commit}`
- **工作区状态**:
```text
{status_output.strip()}
```

## 2. 关键文件索引 (Key References)
{reading_list_str}

## 3. 会话恢复协议 (Restoration Protocol)
**[系统指令]**: 本会话由 `hooks/context_manager.py` 自动恢复。

1.  **状态审查**: 优先检查上方“工作区状态”中的变更文件（如有）。
2.  **上下文加载**: 必须读取 `CLAUDE.md` 以加载核心 Persona 与工程协议。
3.  **协议强制**: 严格遵守 `Protocol Commitment` 头信息的约束（中断驱动、禁止黑话）。

**[待办事项]**:
(由此处开始，AI 应根据上文状态自动推断待办事项，或等待用户指令)
"""

        # 3. Write File
        with open(os.path.join(cwd, SNAPSHOT_FILE), 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Snapshot generated at {SNAPSHOT_FILE}", file=sys.stderr)

    except Exception as e:
        print(f"Failed to generate snapshot: {e}", file=sys.stderr)

def inject_context(cwd):
    """
    Reads the snapshot file and returns it for injection.
    """
    snapshot_path = os.path.join(cwd, SNAPSHOT_FILE)
    if os.path.exists(snapshot_path):
        try:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Return structured JSON for SessionStart
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"\n\n=== AUTOMATED CONTEXT RESTORED FROM {SNAPSHOT_FILE} ===\n{content}\n===============================================\n"
                }
            }
            print(json.dumps(output))
        except Exception as e:
            # If read fails, just print error to stderr
            print(f"Error reading snapshot: {e}", file=sys.stderr)
            sys.exit(0)
    else:
        # No snapshot exists, do nothing
        sys.exit(0)

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        input_data = json.load(sys.stdin)
        event_name = input_data.get("hook_event_name", "")
        cwd = input_data.get("cwd", os.getcwd())

        if event_name == "PreCompact":
            generate_snapshot(cwd)
            sys.exit(0) # Always continue compaction

        elif event_name == "SessionStart":
            inject_context(cwd)
            sys.exit(0)

        else:
            sys.exit(0)

    except Exception as e:
        print(f"Error in context_manager.py: {e}", file=sys.stderr)
        sys.exit(0)

if __name__ == "__main__":
    main()
