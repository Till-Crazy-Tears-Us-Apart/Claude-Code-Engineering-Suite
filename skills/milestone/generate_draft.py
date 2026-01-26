#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : generate_draft.py
@Description : Standalone script to generate a milestone draft and update the timeline.
               Designed to be called manually by the agent via /milestone skill.
@Author      : Claude Sonnet 4.5
@CreationDate: 2026-01-26
"""

import sys
import os
import subprocess
from datetime import datetime

# Relative paths from project root
HISTORY_DIR = ".claude/history"
REPORTS_DIR = os.path.join(HISTORY_DIR, "reports")
TIMELINE_FILE = os.path.join(HISTORY_DIR, "timeline.md")
CLAUDE_MD = "CLAUDE.md"

def ensure_structure():
    """Ensures the history directory structure exists."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    if not os.path.exists(TIMELINE_FILE):
        os.makedirs(os.path.dirname(TIMELINE_FILE), exist_ok=True)
        with open(TIMELINE_FILE, "w", encoding="utf-8") as f:
            f.write("# Project Timeline\n\n项目历史里程碑索引。详细内容请参考关联报告。\n\n---\n")

def get_recent_summary():
    """Captures a brief summary of staged/recent changes."""
    try:
        res = subprocess.run(
            ["git", "diff", "--staged", "--stat"],
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()

        res = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            capture_output=True,
            encoding='utf-8',
            errors='replace'
        )
        return res.stdout.strip() if res.returncode == 0 else "Routine update"
    except:
        return "Manual milestone"

def main():
    # Force UTF-8
    sys.stdout.reconfigure(encoding='utf-8')

    cwd = os.getcwd()
    ensure_structure()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_text = get_recent_summary().split('\n')[0][:60]

    report_filename = f"{timestamp}.md"
    report_path = os.path.join(REPORTS_DIR, report_filename)

    # 1. Generate Report Template
    report_content = f"""# Milestone: {summary_text}
> Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | ID: {timestamp}

## 1. Summary
[AI TODO: 简要总结本阶段的工作内容 (1-3句) - 必须使用简体中文]

## 2. Technical Decisions & Ambiguity Resolution
[AI TODO: 列出关键技术决策 - 必须使用简体中文]
- **Decision**: ... | **Reason**: ...

## 3. Implementation Details
[AI TODO: 请针对每个修改的文件，详细填写以下内容]

### 3.1 [File Path]
- **Modification Summary**: [Change description]
- **Reason**: [Why necessary]
- **Role in Data Flow**: [Input -> Processing -> Output]
- **Ripple Effects**: [Upstream/Downstream impact]
- **Code Logic**: [Specific logic explanation]

[Git Summary for Reference]
{get_recent_summary()}

## 4. Systemic Impact Analysis
- **Data Flow**: TBD
- **Interface Consistency**: TBD
- **Hardcoding Status**: TBD
- **System Risks**: TBD
- **Complexity (Time/Space)**: TBD
- **Concurrency/Locks**: TBD

## 5. Experiments & Debugging
[AI TODO: 记录测试结果、调试日志或 Bug 根因 - 必须使用简体中文]
- N/A

## 6. Invariants & PBT Spec
[AI TODO: 如果有 PBT 属性，请在此记录 - 必须使用简体中文]
- N/A

## 7. Technical Debt & Future Plan
[AI TODO: 遗留问题或下一步计划 - 必须使用简体中文]
- TBD
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. Update Timeline (Prepending)
    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    header = lines[:4]
    rest = lines[4:]

    # Use forward slashes for markdown links
    link_path = os.path.join(REPORTS_DIR, report_filename).replace(os.sep, '/')

    new_entry = [
        f"### **[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]** - {summary_text}\n",
        f"- **关联报告**: `{link_path}`\n\n"
    ]

    with open(TIMELINE_FILE, "w", encoding="utf-8") as f:
        f.writelines(header + new_entry + rest)

    # Call centralized injector
    try:
        # Resolve injector relative to this script: ../../hooks/doc_manager/injector.py
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        injector_path = os.path.abspath(os.path.join(current_script_dir, "../../hooks/doc_manager/injector.py"))

        if os.path.exists(injector_path):
            subprocess.run([sys.executable, injector_path], cwd=cwd, check=False)
        else:
            print(f"Warning: Injector not found at {injector_path}")
    except Exception as e:
        print(f"Warning: Failed to run injector: {e}")

    print(f"Draft generated: {report_path}")
    print(f"Timeline updated: {TIMELINE_FILE}")

if __name__ == "__main__":
    main()
