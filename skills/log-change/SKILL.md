---
name: log-change
description: Generate a standardized change log for context compression.
argument-hint: "[task_id] [status]"
allowed-tools: Bash, Read, Write
disable-model-invocation: true
---

# Change Log Generation Protocol

You must generate a change log file at `.claude/temp_log/_temp_${ARGUMENTS}_[timestamp].md`.
All content MUST be in **Simplified Chinese (简体中文)**.

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

## 3. Content Standards (Strict)
You MUST adhere to the following 4 rules when writing the log:

1.  **Completeness (No Token Saving)**: DO NOT summarize, compress, or omit technical details to save space/tokens. You MUST preserve the FULL technical context.
2.  **Negative Knowledge (Falsification)**: You MUST document *refuted* hypotheses and *failed* attempts. Explaining "why approach X failed" is as critical as "how approach Y succeeded".
3.  **Style (Objective)**: Use formal, simple indicative sentences (`Subject` + `Verb` + `Object`). STRICTLY PROHIBIT unnecessary `Adjectives`, `Adverbs`, and `Metaphors`.
4.  **Epistemic Humility**: DO NOT declare "Fixed" or "Solved" without empirical data (logs/tests). Use "Implemented" or "Attempted" for unverified changes.

## 4. Execution Rule
- **No Adjectives**: Use "Implemented X", not "Successfully implemented X".
- **No Innocence Presumption**: Document risks even if tests passed.
- **Write File**: Use `Write` tool to save the file. Ensure the directory `.claude/temp_log` exists.

## 5. Strict Schema Compliance (Implicit)
You MUST read `~/.claude/skills/log-change/output_schema.json` to understand the required verification depth.
**Do NOT output the JSON block.** Populate the Markdown structure to satisfy the schema's rigor.
