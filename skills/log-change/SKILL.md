---
name: log-change
description: Generate a standardized change log for context compression.
argument-hint: "[task_id] [status]"
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# Change Log Generation Protocol

You must generate a change log file at `.claude/temp_log/_temp_${ARGUMENTS}_[timestamp].md`.

## 1. Input Analysis
- **Task ID**: $1
- **Status**: $2
- **Git State**: !`git diff --staged --stat` (summary) AND !`git diff --staged` (details)

## 2. Content Structure (STRICT TEMPLATE)

The output file MUST strictly follow this markdown structure:

```markdown
# Change Log: [Task ID]
> Generated: [Current Date] | Status: [Status]

## 1. Pre-Implementation Discussion (Q&A)
*(Required if multiple rounds of discussion occurred. If no discussion, state "N/A".)*
- **Q**: [Technical question raised during planning]
- **A**: [Consensus reached]
- **Decision**: [Final architectural decision]

## 2. File-Level Modifications
*(One chapter per modified file)*

### 2.1 [File Path]
- **Modification Summary**: [Concise description]
- **Reason**: [Why this change was necessary]
- **Role in Data Flow**: [Input -> Processing -> Output role]
- **Ripple Effects**:
    - [Upstream dependencies affected]
    - [Downstream consumers affected]
    - [Cohesion impact]
- **Code Logic**:
    - [Line X-Y]: [Explanation of specific logic change]

## 3. Systemic Impact Analysis
*(No subjective adjectives allowed)*
- **Data Flow**: [Changes in data passing mechanisms]
- **Functional Hierarchy**: [Changes in module layering]
- **Framework Impact**: [Decorator/Middleware effects]
- **API Consistency**: [Signature changes?]
- **Performance**: [Complexity analysis / Memory risks]

## 4. Verification Status
- [ ] Tests Passed: [List tests]
- [ ] Manual Check: [List checks]
```

## 3. Execution Rule
- **No Adjectives**: Use "Implemented X", not "Successfully implemented X".
- **No Innocence Presumption**: Document risks even if tests passed.
- **Write File**: Use `Write` tool to save the file. Ensure the directory `.claude/temp_log` exists.
