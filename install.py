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
import subprocess
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

# ── Bilingual UI Messages ─────────────────────────────────────

UI = {
    "en": {
        "target_dir": "Target directory: {path}",
        "src_missing_file": "  [!] Source file missing: {name}, skipping",
        "backed_up": "  [~] Backed up {name} -> {bak}",
        "copied_file": "  [+] {name}",
        "src_missing_dir": "  [!] Source directory missing: {name}/, skipping",
        "copied_dir": "  [+] {name}/ ({count} files)",
        "settings_corrupted": "  [!] settings.json corrupted, backed up to {name}",
        "settings_merged": "  [+] settings.json (merged)",
        "settings_tpl_missing": "  [!] {name} missing, skipping settings.json merge",
        "env_new_keys": "  [i] New keys added to env (configure actual values): {keys}",
        "manifest_written": "  [+] {name}",
        "ts_installed": "  [i] tree-sitter already installed, skipping",
        "ts_prompt": "Install tree-sitter (high-precision C/C++/TypeScript parsing)? [y/N] ",
        "ts_installing": "  Installing tree-sitter ...",
        "j2_installed": "  [i] Jinja2 already installed, skipping",
        "j2_prompt": "Install Jinja2 (post-verify template rendering)? [y/N] ",
        "j2_installing": "  Installing Jinja2 ...",
        "install_done": "\nInstallation complete. {count} files deployed.",
        "install_verify_hint": "Run python install.py --verify to check the installation.",
        "no_manifest": "No install manifest (.installer_manifest.json) found. Cannot uninstall.",
        "skip_modified": "  [~] Skipped (modified): {name}",
        "hooks_removed": "  [+] Suite hooks/permissions removed from settings.json",
        "claude_restored": "  [+] CLAUDE.md restored from backup",
        "uninstall_done": "\nUninstall complete. Removed {removed} files, skipped {skipped} modified files.",
        "verify_python_old": "Python version too old: {ver} (requires >= 3.7)",
        "verify_settings_missing": "settings.json not found",
        "verify_settings_invalid": "settings.json JSON format error: {err}",
        "verify_hook_missing": "Hook file not found: {path}",
        "verify_manifest_missing": "{name} not found",
        "verify_files_missing": "{count} files missing from manifest",
        "verify_header": "Claude Code Engineering Suite v{ver} - Installation Verification\n",
        "verify_python": "  Python: {ver}",
        "verify_target": "  Target directory: {path}",
        "verify_ts": "  tree-sitter: {status}",
        "verify_j2": "  Jinja2: {status}",
        "verify_ts_yes": "installed",
        "verify_ts_no": "not installed (optional)",
        "verify_issues": "Found {count} issues:",
        "verify_ok": "Verification passed. All checks OK.",
        "argparse_desc": "Claude Code Engineering Suite Installer",
        "argparse_uninstall": "Uninstall the suite",
        "argparse_verify": "Verify installation",
        "argparse_lang": "Language for UI and REMY_LANG setting (default: en)",
    },
    "zh-CN": {
        "target_dir": "目标目录: {path}",
        "src_missing_file": "  [!] 源文件缺失: {name}，跳过",
        "backed_up": "  [~] 已备份 {name} -> {bak}",
        "copied_file": "  [+] {name}",
        "src_missing_dir": "  [!] 源目录缺失: {name}/，跳过",
        "copied_dir": "  [+] {name}/ ({count} 个文件)",
        "settings_corrupted": "  [!] settings.json 格式损坏，已备份至 {name}",
        "settings_merged": "  [+] settings.json (合并)",
        "settings_tpl_missing": "  [!] {name} 缺失，跳过 settings.json 合并",
        "env_new_keys": "  [i] env 中新增以下 key（需手动配置实际值）：{keys}",
        "manifest_written": "  [+] {name}",
        "ts_installed": "  [i] tree-sitter 已安装，跳过",
        "ts_prompt": "是否安装 tree-sitter（C/C++/TypeScript 高精度解析）？[y/N] ",
        "ts_installing": "  正在安装 tree-sitter ...",
        "j2_installed": "  [i] Jinja2 已安装，跳过",
        "j2_prompt": "是否安装 Jinja2（post-verify 模板渲染增强）？[y/N] ",
        "j2_installing": "  正在安装 Jinja2 ...",
        "install_done": "\n安装完成。共部署 {count} 个文件。",
        "install_verify_hint": "建议运行 python install.py --verify 检查安装结果。",
        "no_manifest": "未找到安装记录 (.installer_manifest.json)，无法执行卸载。",
        "skip_modified": "  [~] 跳过（已被修改）: {name}",
        "hooks_removed": "  [+] settings.json 中的套件配置已移除",
        "claude_restored": "  [+] CLAUDE.md 已从备份恢复",
        "uninstall_done": "\n卸载完成。删除 {removed} 个文件，跳过 {skipped} 个已修改文件。",
        "verify_python_old": "Python 版本过低: {ver} (需要 >= 3.7)",
        "verify_settings_missing": "settings.json 不存在",
        "verify_settings_invalid": "settings.json JSON 格式错误: {err}",
        "verify_hook_missing": "hook 文件不存在: {path}",
        "verify_manifest_missing": "{name} 不存在",
        "verify_files_missing": "manifest 中 {count} 个文件缺失",
        "verify_header": "Claude Code Engineering Suite v{ver} - 安装验证\n",
        "verify_python": "  Python: {ver}",
        "verify_target": "  目标目录: {path}",
        "verify_ts": "  tree-sitter: {status}",
        "verify_j2": "  Jinja2: {status}",
        "verify_ts_yes": "已安装",
        "verify_ts_no": "未安装（可选）",
        "verify_issues": "发现 {count} 个问题：",
        "verify_ok": "验证通过。所有检查项正常。",
        "argparse_desc": "Claude Code Engineering Suite 安装工具",
        "argparse_uninstall": "卸载套件",
        "argparse_verify": "验证安装",
        "argparse_lang": "界面语言及 REMY_LANG 配置值（默认: en）",
    },
}

_ui_lang = "en"


def _t(key, **kwargs):
    template = UI.get(_ui_lang, UI["en"]).get(key, UI["en"].get(key, key))
    return template.format(**kwargs) if kwargs else template


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


def merge_settings(template: dict, target_path: Path, claude_home: Path, lang_override: str = None) -> Optional[Path]:
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
            print(_t("settings_corrupted", name=corrupted.name))
            existing = {}

    # --- expand template hook paths before comparison ---
    expand_hook_paths(template, claude_home)

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

    # --- REMY_LANG override from --lang ---
    if lang_override:
        ext_env["REMY_LANG"] = lang_override

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
        print(_t("env_new_keys", keys=', '.join(missing_keys)))

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
    print(_t("target_dir", path=claude_home) + "\n")

    records = []

    for fname in DEPLOY_FILES:
        src = SCRIPT_DIR / fname
        dst = claude_home / fname
        if not src.exists():
            print(_t("src_missing_file", name=fname))
            continue
        if dst.exists():
            bp = backup_file(dst)
            if bp:
                print(_t("backed_up", name=fname, bak=bp.name))
        rec = copy_file(src, dst)
        records.append(rec)
        print(_t("copied_file", name=fname))

    for dirname in DEPLOY_DIRS:
        src = SCRIPT_DIR / dirname
        dst = claude_home / dirname
        if not src.exists():
            print(_t("src_missing_dir", name=dirname))
            continue
        dir_records = copy_tree(src, dst)
        records.extend(dir_records)
        print(_t("copied_dir", name=dirname, count=len(dir_records)))

    tpl_path = SCRIPT_DIR / SETTINGS_TEMPLATE
    if tpl_path.exists():
        with open(tpl_path, "r", encoding="utf-8") as f:
            template = json.load(f)
        settings_path = claude_home / "settings.json"
        settings_backup = merge_settings(template, settings_path, claude_home, lang_override=_ui_lang)
        print(_t("settings_merged"))
    else:
        print(_t("settings_tpl_missing", name=SETTINGS_TEMPLATE))
        settings_backup = None

    write_manifest(claude_home, records, settings_backup)
    print(_t("manifest_written", name=MANIFEST_FILE))

    print()
    ts_installed = False
    try:
        import tree_sitter  # noqa: F401
        import tree_sitter_c  # noqa: F401
        import tree_sitter_cpp  # noqa: F401
        import tree_sitter_typescript  # noqa: F401
        ts_installed = True
    except ImportError:
        pass

    if ts_installed:
        print(_t("ts_installed"))
    else:
        answer = input(_t("ts_prompt")).strip().lower()
        if answer == "y":
            print(_t("ts_installing"))
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user",
                 "tree-sitter", "tree-sitter-c", "tree-sitter-cpp",
                 "tree-sitter-typescript"],
                check=False,
            )

    print()
    j2_installed = False
    try:
        import jinja2  # noqa: F401
        j2_installed = True
    except ImportError:
        pass

    if j2_installed:
        print(_t("j2_installed"))
    else:
        answer = input(_t("j2_prompt")).strip().lower()
        if answer == "y":
            print(_t("j2_installing"))
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "Jinja2"],
                check=False,
            )

    print(_t("install_done", count=len(records)))
    print(_t("install_verify_hint"))

    lang_directives = {"zh-CN": "Always respond in Chinese-simplified", "en": "Always respond in English"}
    lang_md_path = claude_home / "language.md"
    lang_md_path.write_text(lang_directives.get(_ui_lang, lang_directives["en"]) + "\n", encoding="utf-8")


def do_uninstall() -> None:
    claude_home = get_claude_home()
    manifest_path = claude_home / MANIFEST_FILE

    if not manifest_path.exists():
        print(_t("no_manifest"))
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
            print(_t("skip_modified", name=fpath.name))
            skipped += 1
            continue
        fpath.unlink()
        removed += 1

    for dirname in DEPLOY_DIRS:
        dirpath = claude_home / dirname
        if dirpath.exists():
            try:
                shutil.rmtree(dirpath)
            except OSError:
                pass

    settings_path = claude_home / "settings.json"
    tpl_path = SCRIPT_DIR / SETTINGS_TEMPLATE
    if settings_path.exists() and tpl_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            settings = json.load(f)
        with open(tpl_path, "r", encoding="utf-8") as f:
            template = json.load(f)

        expand_hook_paths(template, claude_home)
        remove_suite_hooks(settings, template)
        remove_suite_permissions(settings, template)

        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(_t("hooks_removed"))

    claude_md_bak = claude_home / ("CLAUDE.md" + BACKUP_SUFFIX)
    claude_md = claude_home / "CLAUDE.md"
    if claude_md_bak.exists():
        shutil.copy2(claude_md_bak, claude_md)
        claude_md_bak.unlink()
        print(_t("claude_restored"))

    manifest_path.unlink()

    print(_t("uninstall_done", removed=removed, skipped=skipped))


def do_verify() -> None:
    claude_home = get_claude_home()
    errors = []

    if sys.version_info < (3, 7):
        errors.append(_t("verify_python_old", ver=sys.version))

    settings_path = claude_home / "settings.json"
    if not settings_path.exists():
        errors.append(_t("verify_settings_missing"))
    else:
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(_t("verify_settings_invalid", err=e))
            settings = None

        if settings:
            hooks = settings.get("hooks", {})
            for event, entries in hooks.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    for hook in entry.get("hooks", []):
                        cmd = hook.get("command", "")
                        parts = cmd.split('"')
                        if len(parts) >= 2:
                            hook_path = Path(parts[1])
                            if not hook_path.exists():
                                errors.append(_t("verify_hook_missing", path=hook_path))

    manifest_path = claude_home / MANIFEST_FILE
    if not manifest_path.exists():
        errors.append(_t("verify_manifest_missing", name=MANIFEST_FILE))
    else:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        missing = 0
        for entry in manifest.get("files", []):
            if not Path(entry["path"]).exists():
                missing += 1
        if missing:
            errors.append(_t("verify_files_missing", count=missing))

    ts_available = False
    try:
        import tree_sitter  # noqa: F401
        ts_available = True
    except ImportError:
        pass

    j2_available = False
    try:
        import jinja2  # noqa: F401
        j2_available = True
    except ImportError:
        pass

    pyver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(_t("verify_header", ver=SUITE_VERSION))
    print(_t("verify_python", ver=pyver))
    print(_t("verify_target", path=claude_home))
    print(_t("verify_ts", status=_t("verify_ts_yes") if ts_available else _t("verify_ts_no")))
    print(_t("verify_j2", status=_t("verify_ts_yes") if j2_available else _t("verify_ts_no")))
    print()

    if errors:
        print(_t("verify_issues", count=len(errors)))
        for err in errors:
            print(f"  [X] {err}")
        sys.exit(1)
    else:
        print(_t("verify_ok"))


def main() -> None:
    global _ui_lang
    parser = argparse.ArgumentParser(
        description=_t("argparse_desc"),
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--uninstall", action="store_true", help=_t("argparse_uninstall"))
    group.add_argument("--verify", action="store_true", help=_t("argparse_verify"))
    parser.add_argument("--lang", default="en", choices=["en", "zh-CN"],
                        help=_t("argparse_lang"))
    args = parser.parse_args()

    _ui_lang = args.lang

    if args.uninstall:
        do_uninstall()
    elif args.verify:
        do_verify()
    else:
        do_install()


if __name__ == "__main__":
    main()
