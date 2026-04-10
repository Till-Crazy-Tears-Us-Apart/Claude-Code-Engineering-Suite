#!/usr/bin/env python3
"""
Claude Code Engineering Suite - Installer

Usage:
    python install.py              # Install (default)
    python install.py --uninstall  # Uninstall
    python install.py --verify     # Verify installation
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SUITE_VERSION = "2.0.0"
MANIFEST_FILE = ".installer_manifest.json"

DEPLOY_DIRS = ["hooks", "skills", "output-styles"]
DEPLOY_FILES = ["CLAUDE.md", "language.md", "style.md", "tools_ref.md"]
SETTINGS_TEMPLATE = "settings.example.json"

BACKUP_SUFFIX = ".bak"

SCRIPT_DIR = Path(__file__).resolve().parent


def get_claude_home() -> Path:
    return Path.home() / ".claude"


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_tree(src: Path, dst: Path) -> list:
    """Recursively copy directory, return list of {path, sha256} records."""
    records = []
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    for root, _dirs, files in os.walk(dst):
        for fname in files:
            fpath = Path(root) / fname
            records.append({
                "path": str(fpath),
                "sha256": compute_sha256(fpath),
            })
    return records


def copy_file(src: Path, dst: Path) -> dict:
    """Copy single file, return {path, sha256} record."""
    shutil.copy2(src, dst)
    return {
        "path": str(dst),
        "sha256": compute_sha256(dst),
    }


def backup_file(path: Path) -> Optional[Path]:
    """Backup file to path.bak. Returns backup path or None if source absent."""
    if not path.exists():
        return None
    backup_path = path.with_suffix(path.suffix + BACKUP_SUFFIX)
    shutil.copy2(path, backup_path)
    return backup_path


def expand_hook_paths(settings: dict, claude_home: Path) -> None:
    """Replace ~/.claude/ in hook commands with actual absolute path."""
    abs_prefix = str(claude_home).replace("\\", "/")
    hooks = settings.get("hooks", {})
    for _event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            hook_list = entry.get("hooks", [])
            for hook in hook_list:
                cmd = hook.get("command", "")
                hook["command"] = cmd.replace("~/.claude/", abs_prefix + "/")


def hooks_equal(h1: dict, h2: dict) -> bool:
    """Check if two hook entries have the same command."""
    return h1.get("command", "").strip() == h2.get("command", "").strip()


def merge_settings(template: dict, target_path: Path, claude_home: Path) -> Optional[Path]:
    """
    Merge template settings into existing settings.json.
    Returns backup path if settings.json existed, else None.
    """
    existing = {}
    settings_backup = None

    if target_path.exists():
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            settings_backup = backup_file(target_path)
        except json.JSONDecodeError:
            corrupted = target_path.with_suffix(".json.corrupted")
            shutil.copy2(target_path, corrupted)
            print(f"  [!] settings.json 格式损坏，已备份至 {corrupted.name}")
            existing = {}

    # --- hooks: deep merge by event type, deduplicate by command ---
    tpl_hooks = template.get("hooks", {})
    ext_hooks = existing.setdefault("hooks", {})

    for event, tpl_entries in tpl_hooks.items():
        if not isinstance(tpl_entries, list):
            continue
        ext_entries = ext_hooks.setdefault(event, [])

        for tpl_entry in tpl_entries:
            tpl_hook_list = tpl_entry.get("hooks", [])
            matched_ext_entry = None

            # Find existing entry with same matcher
            for ext_entry in ext_entries:
                if ext_entry.get("matcher", "") == tpl_entry.get("matcher", ""):
                    matched_ext_entry = ext_entry
                    break

            if matched_ext_entry is not None:
                ext_hook_list = matched_ext_entry.setdefault("hooks", [])
                for tpl_hook in tpl_hook_list:
                    already_exists = any(
                        hooks_equal(tpl_hook, eh) for eh in ext_hook_list
                    )
                    if not already_exists:
                        ext_hook_list.append(tpl_hook)
            else:
                ext_entries.append(tpl_entry)

    # --- permissions.allow: array dedup append ---
    tpl_perms = template.get("permissions", {}).get("allow", [])
    ext_perms = existing.setdefault("permissions", {}).setdefault("allow", [])
    for perm in tpl_perms:
        if perm not in ext_perms:
            ext_perms.append(perm)

    # --- env: write only missing keys ---
    tpl_env = template.get("env", {})
    ext_env = existing.setdefault("env", {})
    missing_keys = []
    for key, value in tpl_env.items():
        if key not in ext_env:
            ext_env[key] = value
            missing_keys.append(key)

    # --- outputStyle: write if absent ---
    if "outputStyle" not in existing and "outputStyle" in template:
        existing["outputStyle"] = template["outputStyle"]

    # --- expand hook paths ---
    expand_hook_paths(existing, claude_home)

    # --- write ---
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
        f.write("\n")

    if missing_keys:
        print(f"  [i] env 中新增以下 key（需手动配置实际值）：{', '.join(missing_keys)}")

    return settings_backup


def write_manifest(claude_home: Path, records: list, settings_backup: Optional[Path]) -> None:
    manifest = {
        "version": SUITE_VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "settings_backup": str(settings_backup) if settings_backup else None,
        "files": records,
    }
    manifest_path = claude_home / MANIFEST_FILE
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")


def remove_suite_hooks(settings: dict, template: dict) -> None:
    """Remove hooks injected by the suite from settings."""
    tpl_hooks = template.get("hooks", {})
    ext_hooks = settings.get("hooks", {})

    for event, tpl_entries in tpl_hooks.items():
        if event not in ext_hooks:
            continue
        for tpl_entry in tpl_entries:
            tpl_hook_list = tpl_entry.get("hooks", [])
            for ext_entry in ext_hooks[event]:
                if ext_entry.get("matcher", "") != tpl_entry.get("matcher", ""):
                    continue
                ext_hook_list = ext_entry.get("hooks", [])
                ext_entry["hooks"] = [
                    eh for eh in ext_hook_list
                    if not any(hooks_equal(eh, th) for th in tpl_hook_list)
                ]
        # Remove empty entries
        ext_hooks[event] = [
            e for e in ext_hooks[event] if e.get("hooks")
        ]
        if not ext_hooks[event]:
            del ext_hooks[event]

    if not ext_hooks:
        settings.pop("hooks", None)


def remove_suite_permissions(settings: dict, template: dict) -> None:
    """Remove permissions injected by the suite."""
    tpl_perms = template.get("permissions", {}).get("allow", [])
    ext_perms = settings.get("permissions", {}).get("allow", [])
    if ext_perms:
        settings["permissions"]["allow"] = [
            p for p in ext_perms if p not in tpl_perms
        ]
        if not settings["permissions"]["allow"]:
            settings["permissions"].pop("allow", None)
        if not settings["permissions"]:
            settings.pop("permissions", None)


# ── Main Commands ──────────────────────────────────────────────


def do_install() -> None:
    claude_home = get_claude_home()
    claude_home.mkdir(parents=True, exist_ok=True)

    print(f"Claude Code Engineering Suite v{SUITE_VERSION}")
    print(f"目标目录: {claude_home}\n")

    records = []

    # 1. Backup and copy CLAUDE.md + standalone files
    for fname in DEPLOY_FILES:
        src = SCRIPT_DIR / fname
        dst = claude_home / fname
        if not src.exists():
            print(f"  [!] 源文件缺失: {fname}，跳过")
            continue
        if dst.exists():
            bp = backup_file(dst)
            if bp:
                print(f"  [~] 已备份 {fname} -> {bp.name}")
        rec = copy_file(src, dst)
        records.append(rec)
        print(f"  [+] {fname}")

    # 2. Copy directories
    for dirname in DEPLOY_DIRS:
        src = SCRIPT_DIR / dirname
        dst = claude_home / dirname
        if not src.exists():
            print(f"  [!] 源目录缺失: {dirname}/，跳过")
            continue
        dir_records = copy_tree(src, dst)
        records.extend(dir_records)
        print(f"  [+] {dirname}/ ({len(dir_records)} 个文件)")

    # 3. Merge settings.json
    tpl_path = SCRIPT_DIR / SETTINGS_TEMPLATE
    if tpl_path.exists():
        with open(tpl_path, "r", encoding="utf-8") as f:
            template = json.load(f)
        settings_path = claude_home / "settings.json"
        settings_backup = merge_settings(template, settings_path, claude_home)
        print(f"  [+] settings.json (合并)")
    else:
        print(f"  [!] {SETTINGS_TEMPLATE} 缺失，跳过 settings.json 合并")
        settings_backup = None

    # 4. Write manifest
    write_manifest(claude_home, records, settings_backup)
    print(f"  [+] {MANIFEST_FILE}")

    # 5. Optional: tree-sitter
    print()
    ts_installed = False
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_c  # noqa: F401
        import tree_sitter_cpp  # noqa: F401
        ts_installed = True
    except ImportError:
        pass

    if ts_installed:
        print("  [i] tree-sitter 已安装，跳过")
    else:
        answer = input("是否安装 tree-sitter（C/C++ 高精度解析）？[y/N] ").strip().lower()
        if answer == "y":
            import subprocess
            print("  正在安装 tree-sitter ...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user",
                 "tree-sitter", "tree-sitter-c", "tree-sitter-cpp"],
                check=False,
            )

    # 6. Summary
    print(f"\n安装完成。共部署 {len(records)} 个文件。")
    print("建议运行 python install.py --verify 检查安装结果。")


def do_uninstall() -> None:
    claude_home = get_claude_home()
    manifest_path = claude_home / MANIFEST_FILE

    if not manifest_path.exists():
        print("未找到安装记录 (.installer_manifest.json)，无法执行卸载。")
        return

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files = manifest.get("files", [])
    removed = 0
    skipped = 0

    for entry in files:
        fpath = Path(entry["path"])
        if not fpath.exists():
            continue
        current_hash = compute_sha256(fpath)
        if current_hash != entry["sha256"]:
            print(f"  [~] 跳过（已被修改）: {fpath.name}")
            skipped += 1
            continue
        fpath.unlink()
        removed += 1

    # Clean empty directories
    for dirname in DEPLOY_DIRS:
        dirpath = claude_home / dirname
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
            except OSError:
                pass

    # Remove hooks/permissions from settings.json
    settings_path = claude_home / "settings.json"
    tpl_path = SCRIPT_DIR / SETTINGS_TEMPLATE
    if settings_path.exists() and tpl_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        with open(tpl_path, "r", encoding="utf-8") as f:
            template = json.load(f)

        remove_suite_hooks(settings, template)
        remove_suite_permissions(settings, template)

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("  [+] settings.json 中的套件配置已移除")

    # Restore CLAUDE.md backup
    claude_md_bak = claude_home / ("CLAUDE.md" + BACKUP_SUFFIX)
    claude_md = claude_home / "CLAUDE.md"
    if claude_md_bak.exists():
        shutil.copy2(claude_md_bak, claude_md)
        claude_md_bak.unlink()
        print("  [+] CLAUDE.md 已从备份恢复")

    # Remove manifest
    manifest_path.unlink()

    print(f"\n卸载完成。删除 {removed} 个文件，跳过 {skipped} 个已修改文件。")


def do_verify() -> None:
    claude_home = get_claude_home()
    errors = []

    # 1. Python version
    if sys.version_info < (3, 7):
        errors.append(f"Python 版本过低: {sys.version} (需要 >= 3.7)")

    # 2. settings.json validity
    settings_path = claude_home / "settings.json"
    if not settings_path.exists():
        errors.append("settings.json 不存在")
    else:
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"settings.json JSON 格式错误: {e}")
            settings = None

        # 3. Hook file existence
        if settings:
            hooks = settings.get("hooks", {})
            for event, entries in hooks.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        cmd = hook.get("command", "")
                        # Extract path from: python "path/to/script.py"
                        parts = cmd.split('"')
                        if len(parts) >= 2:
                            hook_path = Path(parts[1])
                            if not hook_path.exists():
                                errors.append(f"hook 文件不存在: {hook_path}")

    # 4. Manifest check
    manifest_path = claude_home / MANIFEST_FILE
    if not manifest_path.exists():
        errors.append(f"{MANIFEST_FILE} 不存在")
    else:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        missing = 0
        for entry in manifest.get("files", []):
            if not Path(entry["path"]).exists():
                missing += 1
        if missing:
            errors.append(f"manifest 中 {missing} 个文件缺失")

    # 5. tree-sitter check (informational)
    ts_available = False
    try:
        import tree_sitter  # noqa: F401
        ts_available = True
    except ImportError:
        pass

    # Report
    print(f"Claude Code Engineering Suite v{SUITE_VERSION} - 安装验证\n")
    print(f"  Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print(f"  目标目录: {claude_home}")
    print(f"  tree-sitter: {'已安装' if ts_available else '未安装（可选）'}")
    print()

    if errors:
        print(f"发现 {len(errors)} 个问题：")
        for err in errors:
            print(f"  [X] {err}")
        sys.exit(1)
    else:
        print("验证通过。所有检查项正常。")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Claude Code Engineering Suite 安装工具",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--uninstall", action="store_true", help="卸载套件")
    group.add_argument("--verify", action="store_true", help="验证安装")
    args = parser.parse_args()

    if args.uninstall:
        do_uninstall()
    elif args.verify:
        do_verify()
    else:
        do_install()


if __name__ == "__main__":
    main()
