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
from datetime import datetime, timedelta

SNAPSHOT_FILE = os.path.join(".claude", "context_snapshot.md")
LOGIC_INDEX_FILE = os.path.join(".claude", "logic_index.json")
MAX_STATUS_LINES = 50  # Limit git status output to avoid memory issues

def get_git_env():
    """Returns environment with UTF-8 encoding forced for Git."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return env

def check_logic_index_status(cwd):
    """
    Checks if logic_index.json exists and if it's stale relative to source code.
    Returns a warning string if stale, or None if fresh/missing.
    """
    index_path = os.path.join(cwd, LOGIC_INDEX_FILE)
    if not os.path.exists(index_path):
        return None

    try:
        # Get index modification time
        index_mtime = os.path.getmtime(index_path)

        # Check a few key source files to see if they are newer
        # This is a heuristic check, not exhaustive scan
        check_dirs = ["hooks", "skills", "src"]
        is_stale = False

        for d in check_dirs:
            dir_path = os.path.join(cwd, d)
            if not os.path.exists(dir_path): continue

            for root, _, files in os.walk(dir_path):
                for f in files:
                    if any(f.endswith(ext) for ext in ('.py', '.c', '.h', '.cpp', '.hpp', '.cc', '.cxx')):
                        file_path = os.path.join(root, f)
                        if os.path.getmtime(file_path) > index_mtime:
                            is_stale = True
                            break
                if is_stale: break
            if is_stale: break

        if is_stale:
            return "⚠️ **逻辑索引已过期** (Source code is newer than index). Run `/update-logic-index` to refresh."

        # Also check expiry based on time (e.g. > 24 hours)
        if datetime.now().timestamp() - index_mtime > 86400:
             return "⚠️ **逻辑索引可能陈旧** (Index > 24h old). Consider running `/update-logic-index`."

        return "✅ **逻辑索引有效** (Logic Index is fresh)."

    except Exception:
        return None

def generate_snapshot(cwd):
    """
    Generates the snapshot file using git status and file listings.
    Optimized for Windows performance and large repo safety.
    """
    try:
        # Ensure .claude directory exists
        os.makedirs(os.path.join(cwd, ".claude"), exist_ok=True)
        # 1. Capture Git Info
        branch = "Unknown"
        last_commit = "Unknown"

        # [NEW] Check Logic Index Status
        index_status = check_logic_index_status(cwd)
        index_status_str = f"\n- {index_status}" if index_status else ""

        status_output = ""

        # Check if inside git tree
        git_check = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            capture_output=True,
            env=get_git_env()
        )

        if git_check.returncode == 0:
            # OPTIMIZATION: Combine branch info with status if possible, but --show-current is cleaner.
            # We keep them separate but ensure robust encoding.

            # Get Branch
            res_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=cwd,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                env=get_git_env()
            )
            if res_branch.returncode == 0:
                branch = res_branch.stdout.strip()

            # Get Last Commit
            res_commit = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%h - %s (%an)"],
                cwd=cwd,
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                env=get_git_env()
            )
            if res_commit.returncode == 0:
                last_commit = res_commit.stdout.strip()

            # Get Status (Optimized for Memory)
            # Use Popen to stream output instead of loading all into memory
            try:
                proc = subprocess.Popen(
                    ["git", "status", "--short"],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    encoding='utf-8',
                    errors='replace',
                    env=get_git_env()
                )

                lines = []
                for i, line in enumerate(proc.stdout):
                    if i < MAX_STATUS_LINES:
                        lines.append(line.rstrip())
                    else:
                        lines.append(f"... (Truncated: too many changes, showing first {MAX_STATUS_LINES})")
                        proc.terminate() # efficient stop
                        break

                # Ensure process is cleaned up if we didn't iterate all
                if proc.poll() is None:
                    proc.stdout.close()
                    proc.stderr.close()
                    proc.wait()

                status_output = "\n".join(lines)
                if not status_output.strip():
                    status_output = "(工作区干净，无未提交变更)"
            except Exception as e:
                status_output = f"Error reading git status: {e}"

        else:
            status_output = "--- 非 Git 仓库 ---\n"
            # Fallback listing using os.scandir (Optimized)
            try:
                file_list = []
                # Only scan top-level depth=2 for efficiency
                for entry in os.scandir(cwd):
                    if entry.is_dir() and not entry.name.startswith('.'):
                        try:
                            # Level 2 scan
                            for sub in os.scandir(entry.path):
                                if not sub.name.startswith('.'):
                                    rel_path = os.path.relpath(sub.path, cwd)
                                    file_list.append(rel_path)
                                    if len(file_list) >= MAX_STATUS_LINES: break
                        except PermissionError:
                            pass
                    elif entry.is_file() and not entry.name.startswith('.'):
                        file_list.append(entry.name)

                    if len(file_list) >= MAX_STATUS_LINES: break

                status_output += "\n".join(file_list)
                if len(file_list) >= MAX_STATUS_LINES:
                    status_output += "\n... (文件过多已截断)"
            except Exception as e:
                status_output += f"Error listing files: {e}"

        # 2. Generate Content
        reading_list = []
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
                dirs.sort(key=lambda x: (0 if x in ['src', 'lib', 'core', 'app', 'skills', 'hooks'] else 1, x))
                dir_str = ", ".join([f"`{d}/`" for d in dirs[:15]])
                reading_list.append(f"- **目录结构**: {dir_str}")

            # [NEW] Scan for Available Skills
            skills_dir = os.path.join(cwd, "skills")
            if os.path.isdir(skills_dir):
                skill_list = []
                for skill_name in os.listdir(skills_dir):
                    skill_path = os.path.join(skills_dir, skill_name, "SKILL.md")
                    if os.path.isfile(skill_path):
                        # Extract description from frontmatter
                        description = "Available"
                        try:
                            with open(skill_path, 'r', encoding='utf-8') as sf:
                                for line in sf:
                                    if line.startswith("description:"):
                                        description = line.replace("description:", "").strip()
                                        break
                        except:
                            pass
                        skill_list.append(f"- **{skill_name}**: {description}")

                if skill_list:
                    reading_list.append("\n## 3. Available Skills (强化提示)")
                    reading_list.extend(skill_list)

        except Exception:
            pass

        reading_list_str = "\n".join(reading_list)

        content = f"""# 🔄 自动上下文快照 (Automated Context Snapshot)
> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 1. 项目状态概览 (Project State)
- **当前分支**: `{branch}`
- **最近提交**: `{last_commit}`{index_status_str}
- **工作区状态**:
```text
{status_output.strip()}
```

## 2. 关键文件索引 (Key References)
{reading_list_str}

## 4. 会话恢复协议 (Restoration Protocol)
**[系统指令]**: 本会话由 `hooks/context_manager.py` 自动恢复。

1.  **状态审查**: 优先检查上方“工作区状态”中的变更文件（如有）。
2.  **上下文加载**: 必须读取 `CLAUDE.md` 以加载核心 Persona 与工程协议。
3.  **技能意识**: 查看上方 "Available Skills" 列表，**主动 (Proactively)** 使用相关技能（如 TDD, Debugging）。
4.  **协议强制**: 严格遵守 UserPromptSubmit hook 中附加的 `system_reminder` 信息的约束（中断驱动、禁止黑话）。

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

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": f"\n\n=== AUTOMATED CONTEXT RESTORED FROM {SNAPSHOT_FILE} ===\n{content}\n===============================================\n"
                }
            }
            print(json.dumps(output))
        except Exception as e:
            print(f"Error reading snapshot: {e}", file=sys.stderr)
            sys.exit(0)
    else:
        sys.exit(0)

def main():
    # Force UTF-8 for stdin/stdout to handle Chinese paths correctly on Windows
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

    try:
        # Handle empty input safely
        if sys.stdin.isatty():
             sys.exit(0)

        input_data = json.load(sys.stdin)
        event_name = input_data.get("hook_event_name", "")
        cwd = input_data.get("cwd", os.getcwd())

        if event_name == "PreCompact":
            generate_snapshot(cwd)
            sys.exit(0)

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
