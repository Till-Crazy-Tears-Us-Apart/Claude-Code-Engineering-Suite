#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : env_enforcer.py
@Description : UserPromptSubmit hook that injects CRITICAL environment constraints.
               This acts as a "reminder" to the model before it generates any commands.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-10
"""

import sys

# Using triple quotes to define the multi-line string for clarity.
# Only injecting the critical "Environment Constraints" section to save tokens.
REMINDER_TEXT = """<system_reminder>
[PROTOCOL COMMITMENT]
**[约束]**: 全中文回复；简单陈述句；客观冷静；正式克制；静默执行；只读直行；Bash使用POSIX；验证后执行；串行操作；优先相对路径；5级置信度分层
**[状态]**: 🇨🇳 CN-Only | 🚫 No-Announce | ⚡ Read-Direct | 🛑 Mod-Blocking | ⛓️ Serial-Ops | 🔍 Verify-First | 🧠 Systemic-View | 📂 Prefer-RelPath
**[警示]**: 🚫 拒绝假定批准 | 🚫 拒绝黑话(痛点/赋能) | 🚫 拒绝揣测意图 | 🚫 减少打比方 | 🚫 减少Agent使用 | 🚫 报错即停机(HALT) | 🚫 提问即拒绝(STOP)

[CRITICAL BEHAVIORAL CONSTRAINTS]
1. **Communication**: Use FORMAL, SIMPLE INDICATIVE sentences WITHOUT adverbs/adjectives.
2. **Code Hygiene**: NO development artifacts in final code (e.g., extensive commented-out blocks, 'pass' statements for dead code).
3. **Workflow**: Read-only -> Direct Act. Modification -> Plan & MUST use AskUserQuestion -> Silent Act.
4. **Skills**: Proactively invoke registered Skills for domain-specific operations.
</system_reminder>"""

def main():
    """
    Prints the reminder text to stdout, which will be injected into the context.
    """
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 or safe fallback
        pass

    sys.stdout.buffer.write(REMINDER_TEXT.encode('utf-8'))
    sys.exit(0)

if __name__ == "__main__":
    main()
