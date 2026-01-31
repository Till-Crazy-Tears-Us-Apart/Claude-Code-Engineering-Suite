#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : injector.py
@Description : Centralized manager for injecting references into CLAUDE.md.
               Ensures idempotency and atomic updates.
@Author      : Logic Indexer Skill
@CreationDate: 2026-01-26
@Version     : 1.1.0
"""

import sys
import os
import json
import re

CLAUDE_MD = "CLAUDE.md"
SETTINGS_FILE = os.path.join(".claude", "settings.local.json")

# Registry of content to be injected
# Format: { "tag_name": "relative_file_path" }
# The script will inject:
# <tag_name>
# @relative_file_path
# </tag_name>
REGISTRY = {
    "project_structure": ".claude/project_tree.md",
    "history_timeline": ".claude/history/timeline.md",
    "logic_tree": ".claude/logic_tree.md"
}

def load_policy_from_settings(cwd):
    """Loads injection policy from settings.local.json or environment."""
    # 1. Try Environment Variable (Highest Priority if set explicitly in shell)
    env_policy = os.environ.get("LOGIC_INDEX_AUTO_INJECT")
    if env_policy:
        return env_policy

    # 2. Try Local Settings File
    settings_path = os.path.join(cwd, SETTINGS_FILE)
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Check nested structure: env -> LOGIC_INDEX_AUTO_INJECT
                return data.get("env", {}).get("LOGIC_INDEX_AUTO_INJECT")
        except Exception:
            pass

    # 3. Default Fallback
    return "ASK"

def remove_block(content, tag):
    """Removes a specific tag block from content."""
    pattern = f"\\n*<{tag}>.*?<\\/{tag}>\\n*"
    return re.sub(pattern, "", content, flags=re.DOTALL)

def inject_all(cwd):
    """Injects all registered references into CLAUDE.md."""
    claude_md_path = os.path.join(cwd, CLAUDE_MD)

    # Determine Policy
    logic_policy = load_policy_from_settings(cwd)

    # Create local registry copy to modify
    active_registry = REGISTRY.copy()
    removal_list = []

    if logic_policy != "ALWAYS":
        if "logic_tree" in active_registry:
            del active_registry["logic_tree"]
            # Mark for potential removal if policy is NEVER/ASK
            removal_list.append("logic_tree")

    # Create CLAUDE.md if not exists
    if not os.path.exists(claude_md_path):
        with open(claude_md_path, 'w', encoding='utf-8') as f:
            f.write("# System Context\n\n")

    with open(claude_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    changes_made = False

    # 1. Handle Removals (Reverse Injection)
    for tag in removal_list:
        if f"<{tag}>" in new_content:
            new_content = remove_block(new_content, tag)
            changes_made = True

    # 2. Handle Injections
    for tag, rel_path in active_registry.items():
        ref_line = f"@{rel_path}"

        # Check if already referenced (either by tag or direct link)
        if ref_line in new_content:
            continue

        # Build block
        # Ensure sufficient padding before the block
        prefix = "\n\n" if not new_content.endswith("\n\n") else ("\n" if not new_content.endswith("\n\n") else "")
        block = f"{prefix}<{tag}>\n\n{ref_line}\n\n</{tag}>\n"

        # Check if tag exists but content is different (simple append for now to be safe)
        if f"<{tag}>" not in new_content:
            new_content += block
            changes_made = True

    if changes_made:
        # Cleanup extra newlines potentially created by removal
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)

        with open(claude_md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"[Injector] Updated {CLAUDE_MD} (Policy: {logic_policy})")
    else:
        print(f"[Injector] No changes needed for {CLAUDE_MD} (Policy: {logic_policy})")

def main():
    # Force UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    cwd = os.getcwd()
    inject_all(cwd)

if __name__ == "__main__":
    main()
