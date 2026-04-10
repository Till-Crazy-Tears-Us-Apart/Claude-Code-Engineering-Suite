---
name: repo-audit
description: "Use when evaluating an unfamiliar GitHub repository, assessing repo complexity before cloning, or inspecting a remote codebase without polluting the local workspace. Fetches metadata and README via GH CLI, warns on large repos, then clones to a temporary sandbox for deep file-tree and tech-stack analysis upon user confirmation."
disable-model-invocation: true
allowed-tools: Bash, Glob, Grep, Read
---

# Repository Audit

Two-stage inspection of GitHub repositories: lightweight metadata first, sandboxed deep clone only after user confirmation.

**Requirements**: `git`, `gh` (authenticated via `gh auth login`)

**Usage**: `/repo-audit <url>`

## Stage 1: Reconnaissance

1. **Validate URL**: Confirm valid GitHub URL format.
2. **Fetch Metadata**:
   ```bash
   gh repo view <url> --json description,stargazerCount,diskUsage,defaultBranchRef
   ```
3. **Fetch README**:
   ```bash
   gh api repos/<owner>/<repo>/readme --jq .content | python -c "import sys, base64; print(base64.b64decode(sys.stdin.read().strip()).decode('utf-8', errors='replace'))"
   ```
4. **Report & Gate**: Present summary with full README.
   - If `diskUsage` > 500MB → WARN user.
   - Ask user whether to proceed to Stage 2. **STOP and wait for confirmation.**

## Stage 2: Deep Inspection (Sandboxed)

**Only after user confirmation.**

1. **Run audit script** (clones to temp directory, generates structure report):
   ```bash
   python ~/.claude/skills/repo-audit/scripts/audit_runner.py <repo_url> [--force]
   ```
   The `--force` flag overrides the 500MB safety limit.
2. **Analyze**: Review file tree and tech stack from the report.
3. **Explore**: Use `Glob`, `Grep`, `Read` on the temp directory.
4. **Cleanup**: Delete the temp directory using the command provided in the report.
