---
name: post-verify
description: Use after code modification to discover/create tests, run them, assess coverage, and fix failures. Invoked explicitly by user.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, AskUserQuestion
argument-hint: "[target_files or changed_functions (optional)]"
disable-model-invocation: true
---

# Post-Verify Protocol

Post-implementation verification skill. Discovers existing tests, creates temporary tests when none exist, runs them, evaluates coverage and assertion quality, and drives a fix loop until all tests pass.

**Relationship to TDD**: TDD operates *before* implementation (RED→GREEN→REFACTOR). This skill operates *after* implementation to verify completed changes. They are complementary, not overlapping.

## External Files

> **Path Convention**: All paths below are relative to `~/.claude/`. Use `Read("~/.claude/skills/post-verify/...")` to access them — they are NOT in the project working directory.

| File | Purpose |
| :--- | :--- |
| `skills/post-verify/frameworks.json` | Test framework detection rules (Phase 2). User-extensible. |
| `skills/post-verify/anti_patterns.json` | Assertion anti-pattern detection rules (Phase 6). User-extensible. |
| `skills/post-verify/templates/test_python.py.j2` | Jinja2 template for temporary Python tests (Phase 3). |
| `skills/post-verify/templates/test_javascript.js.j2` | Jinja2 template for temporary JavaScript tests (Phase 3). |
| `skills/post-verify/templates/test_go.go.j2` | Jinja2 template for temporary Go tests (Phase 3). |
| `skills/post-verify/templates/report.md.j2` | Jinja2 template for the final report (Phase 8). |
| `skills/post-verify/render.py` | Template rendering helper. Uses Jinja2 when available, falls back to `str.format()`. |

## Optional Dependency: Jinja2

`render.py` attempts `import jinja2`. If unavailable, all templates are rendered via built-in string formatting (functionally equivalent, but templates are not externally editable in fallback mode). Jinja2 can be installed via `install.py` (optional step).

## 0. Configuration

| Environment Variable | Default | Description |
| :--- | :--- | :--- |
| `POST_VERIFY_MAX_RETRIES` | `-1` (unlimited) | Maximum test-fix iterations. `-1` = no limit. Positive integer = hard cap. |

Read `POST_VERIFY_MAX_RETRIES` from `os.environ` at the start of Phase 4. If the value is not parseable as an integer, treat as `-1`.

## Report Persistence

Final reports are saved to `.claude/temp_test/report_{timestamp}.md` in the project directory via `render.save_report()`. This directory is created automatically if absent.

---

## 1. Phase 1: Scope Identification

**Goal**: Determine what changed and what needs testing.

1. **If arguments provided**: Use them as the target scope (file paths or function names).
2. **If no arguments**: Run `git diff --name-only HEAD` (or `git diff --cached --name-only` if staged). If not a git repo, ask the user to specify targets via `AskUserQuestion`.
3. **Extract change units**: For each changed file, identify modified/added functions, classes, and methods by diffing against the previous version.
4. **Record**: Build an internal `change_set` list: `[{file, symbol, type}]`.

**Output**: Print the change set as a summary table to the user.

---

## 2. Phase 2: Test Discovery

**Goal**: Find existing tests that cover the change set.

### 2.1 Detection Strategy

Load detection rules from `frameworks.json`. Each entry defines:
- `indicators`: file existence or file-content checks, evaluated in `priority` order.
- `run_command` / `coverage_command`: command templates with `{test_files}`, `{module}`, `{package}`, `{test_pattern}` placeholders.
- `test_file_pattern` / `test_dir_patterns`: glob patterns for locating test files.

Execute indicator checks for each framework entry in priority order. Stop at the first match.

If no framework is detected and no test directories exist → proceed to Phase 3.

### 2.2 Mapping Changes to Tests

For each item in `change_set`:

1. **Grep** for the symbol name in test directories.
2. **Grep** for import/require statements referencing the changed file.
3. **Record** mapping: `{symbol → [test_file:test_function]}`.
4. **Flag uncovered symbols**: Symbols with zero test references.

**Output**: Print a coverage mapping table. Flag uncovered symbols.

---

## 3. Phase 3: Test Creation (Conditional)

**Trigger**: Any symbol in `change_set` has no existing test coverage.

### 3.1 Placement Strategy (Mixed)

| Condition | Location | Cleanup |
| :--- | :--- | :--- |
| Module importable without project-specific setup | `/tmp/_postverify_{timestamp}/` | Delete entire directory after Phase 7 |
| Module requires project structure (relative imports, config files, fixtures) | Project directory: `_temp_postverify_test_{timestamp}.py` | Delete file after Phase 7 |

### 3.2 Template-Based Generation

Use `render.render_template()` to generate test files from the appropriate language template (`test_python.py.j2`, `test_javascript.js.j2`, `test_go.go.j2`). Populate the context dict with:

```python
{
    "module_name": "...",
    "imports": ["import ...", ...],
    "test_cases": [
        {
            "name": "function_name_scenario_expected",
            "description": "...",
            "body_lines": ["result = func(arg)", "assert result == expected"],
            "is_async": False
        }
    ]
}
```

If the target language has no matching template, generate tests directly via LLM (no template).

### 3.3 Test Quality Requirements

Temporary tests MUST satisfy:

- **One assertion per logical behavior**. No multi-behavior bundling.
- **Test the public interface**, not internal state.
- **Include at least**:
  - 1 happy-path case
  - 1 edge-case (empty input, boundary value, None/null)
  - 1 error-case (invalid input, expected exception)
- **No mocks** unless the dependency is external I/O (network, filesystem, database). When mocking is unavoidable, mock at the boundary, not deep internals.
- **Deterministic**. No random data without fixed seeds. No time-dependent assertions without freezing time.

### 3.4 Test Naming Convention

```
test_{function_name}_{scenario}_{expected_outcome}
```

Example: `test_load_policy_missing_env_var_returns_always`

---

## 4. Phase 4: Test Execution & Fix Loop

### 4.1 Initial Run

1. **Run** the relevant test command (from `frameworks.json` or constructed for temp tests).
2. **Capture** stdout, stderr, and exit code.
3. **Parse** results: count passed, failed, errored.

### 4.2 Failure Triage (Critical)

When a test fails, determine the fault location **before** attempting any fix. Do NOT default to blaming the implementation.

**Triage decision tree:**

```
Test fails
├─ Is the assertion itself correct?
│   ├─ NO → Test defect. Fix the test.
│   └─ YES ↓
├─ Does the test setup match real-world conditions?
│   ├─ NO → Test defect. Fix setup/fixtures.
│   └─ YES ↓
├─ Is the test importing/calling the correct symbol?
│   ├─ NO → Test defect. Fix import/call.
│   └─ YES ↓
└─ Implementation defect. Fix the code.
```

**Rule**: When triage is ambiguous, report both hypotheses to the user via `AskUserQuestion` and let them decide. Do NOT guess.

### 4.3 Fix Loop

```
iteration = 0
max_retries = POST_VERIFY_MAX_RETRIES (from env, default -1)

LOOP:
  IF max_retries >= 0 AND iteration >= max_retries:
      HALT. Report: "Reached maximum retry limit ({max_retries}). {N} tests still failing."
      EXIT with failure summary.

  1. Triage failure (Section 4.2).
  2. Propose fix via AskUserQuestion:
     - Show: failing test name, error message, triage conclusion (test defect vs. code defect).
     - Options: "Apply fix" / "Skip this failure" / "Abort verification".
  3. IF user approves:
     - Apply fix (Edit tool).
     - Re-run tests.
     - IF all pass → break LOOP.
     - ELSE → iteration += 1, continue LOOP.
  4. IF user skips → continue to next failure.
  5. IF user aborts → EXIT immediately, skip to Phase 7 cleanup.
```

---

## 5. Phase 5: Coverage Assessment

**Trigger**: All tests pass (or user chose to skip remaining failures).

### 5.1 Branch Coverage Measurement

1. **If coverage tool available**: Use the `coverage_command` from `frameworks.json` (e.g., `pytest --cov={module} --cov-branch --cov-report=term-missing`).
2. **If coverage tool unavailable**: Perform static analysis — enumerate branches (if/elif/else, try/except, ternary, loop conditions) in changed functions and check whether tests exercise both sides.
3. **Threshold**: Branch coverage of changed functions/classes >= 80%.

### 5.2 Coverage Report

Print a table:

| Symbol | Branches | Covered | Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| `load_policy` | 6 | 5 | 83% | PASS |
| `inject_all` | 10 | 7 | 70% | FAIL |

### 5.3 Below Threshold

If any symbol is below 80%:

1. Identify uncovered branches (from `--cov-report=term-missing` or static analysis).
2. **Create additional tests** targeting those branches (same rules as Phase 3).
3. Re-run and re-assess. This counts toward the fix loop iteration limit.

---

## 6. Phase 6: Assertion Quality Audit

**Goal**: Verify that passing tests are testing meaningful behavior, not trivially true.

### 6.1 Anti-Pattern Detection

Load detection rules from `anti_patterns.json`. Each entry defines:
- `id`, `name`, `severity` (`critical` / `warning` / `info`)
- `regex`: list of patterns to match against test source
- `negative_regex` (optional): patterns that, if present, negate the match
- `detection`: `"ast_scan"` for rules requiring structural analysis (no regex shortcut)
- `languages`: applicable language filter

For each relevant test file:
1. Filter rules by detected language.
2. Apply regex-based rules via `Grep`.
3. Apply `ast_scan` rules by reading the test file and analyzing structure.
4. For rules with `negative_regex`: flag only if positive matches exist AND no negative matches exist.

### 6.2 Report

Print findings. Critical anti-patterns MUST be fixed (following the same AskUser fix loop). Warnings are reported but not blocking.

---

## 7. Phase 7: Cleanup

1. **Delete** all temporary test files created in Phase 3:
   - `/tmp/_postverify_{timestamp}/` — `rm -rf`
   - `_temp_postverify_test_{timestamp}.py` in project directory — `rm -f`
2. **Delete** any `.pyc` / `__pycache__` generated by temp tests in `/tmp`.
3. **Verify** cleanup: `ls` the temp paths to confirm deletion.
4. **Do NOT delete** existing project tests, coverage reports, or any file not created by this skill.

---

## 8. Final Report

Use `render.save_report()` to generate and persist the report to `.claude/temp_test/report_{timestamp}.md`.

Populate the context dict:

```python
{
    "project_name": "...",
    "change_set": [{"file": "...", "symbol": "...", "type": "..."}],
    "coverage_map": [{"symbol": "...", "existing_count": N, "temp_count": N}],
    "test_results": [{"name": "...", "status": "PASS/FAIL", "duration": "..."}],
    "passed": N,
    "total": N,
    "fix_iterations": N,
    "coverage_data": [{"symbol": "...", "branches": N, "covered": N, "percent": N, "status": "PASS/FAIL"}],
    "audit_findings": [{"id": "AP-001", "pattern_name": "...", "severity": "...", "file": "...", "line": N}],
    "final_status": "PASS / FAIL"
}
```

Also print a condensed summary to stdout:

```
Post-Verify Complete
====================
Change Set:     {N} symbols across {M} files
Tests:          {existing} existing, {created} temporary (cleaned)
Results:        {passed}/{total} passed | Fix iterations: {iterations}
Branch Coverage: {min}% - {max}% (threshold: 80%)
Audit:          {critical} critical, {warning} warnings
Status:         PASS / FAIL
Report:         .claude/temp_test/report_{timestamp}.md
```

---

## 9. Critical Rules

1. **Never modify production code without user confirmation** via `AskUserQuestion`.
2. **Never skip failure triage**. Blaming implementation by default is a protocol violation.
3. **Never leave temporary files behind**. Phase 7 is mandatory even on early abort.
4. **Never lower the coverage threshold**. 80% branch coverage is non-negotiable.
5. **Never trust a passing test without auditing it** (Phase 6). A tautological test is worse than no test.
6. **Clean separation**: This skill does not write permanent tests for the project unless the user explicitly requests it. All created tests are temporary by default.
