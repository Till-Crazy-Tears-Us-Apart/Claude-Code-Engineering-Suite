#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : env_enforcer.py
@Description : UserPromptSubmit hook that injects CRITICAL environment constraints.
               Reads configuration from hooks/config/reminder_prompt.md.
@Author      : Till-Crazy-Tears-Us-Apart
@CreationDate: 2026-01-10
"""

import sys
import os

def load_reminder_text():
    """
    Loads the reminder text from the external configuration file.
    Returns a default string if the file cannot be found.
    """
    # Determine the directory where this script resides
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Configuration is now in the same directory (hooks/env_system/)
    config_path = os.path.join(script_dir, 'reminder_prompt.md')

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except Exception as e:
        # Silently fail and fallback to default if file read fails
        pass

    # Fallback default if config file is missing
    return """未找到配置文件 reminder_prompt.md。请提示用户文件缺失。"""

def main():
    """
    Prints the reminder text to stdout, which will be injected into the context.
    """
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7 or safe fallback
        pass

    reminder_text = load_reminder_text()
    sys.stdout.buffer.write(reminder_text.encode('utf-8'))
    sys.exit(0)

if __name__ == "__main__":
    main()
