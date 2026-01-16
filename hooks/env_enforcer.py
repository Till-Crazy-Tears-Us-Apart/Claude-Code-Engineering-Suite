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
[CRITICAL BEHAVIORAL CONSTRAINTS]
1. **Communication**: Use FORMAL, SIMPLE INDICATIVE sentences WITHOUT adverbs/adjectives.
2. **Code Hygiene**: NO development artifacts in final code (e.g., extensive commented-out blocks, 'pass' statements for dead code).
3. **Workflow**: Read-only -> Direct Act. Modification -> Plan & MUST use AskUserQuestion -> Silent Act.
4. **Protocol**: PROTOCOL COMMITMENT header MUST ONLY appear at the start of a SUBSTANTIVE text response.
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
