---
name: writing-skills
description: "Use when creating new SKILL.md files, editing existing skills, validating skill frontmatter and structure, or verifying skills work before deployment. Generates YAML frontmatter, validates naming conventions, applies TDD methodology to skill documentation, and structures content for Claude Search Optimization (CSO)."
disable-model-invocation: true
---

# Writing Skills

**Writing skills IS Test-Driven Development applied to process documentation.**

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

**REQUIRED BACKGROUND:** You MUST understand `superpowers:test-driven-development` before using this skill.

**Official guidance:** See `anthropic-best-practices.md` for Anthropic's skill authoring best practices.

## What is a Skill?

A **skill** is a reference guide for proven techniques, patterns, or tools. **Skills are NOT** narratives about how you solved a problem once.

**Create when:** technique wasn't obvious, you'd reference it across projects, pattern applies broadly, others benefit.
**Don't create for:** one-off solutions, well-documented standard practices, project-specific conventions (use CLAUDE.md).

## Skill Types

- **Technique** — concrete method with steps (condition-based-waiting, root-cause-tracing)
- **Pattern** — way of thinking about problems (flatten-with-flags, test-invariants)
- **Reference** — API docs, syntax guides, tool documentation

## Directory Structure

```
skills/
  skill-name/
    SKILL.md              # Main reference (required)
    supporting-file.*     # Only if needed (100+ lines reference, reusable tools)
```

## SKILL.md Structure

**Frontmatter (YAML):** Only `name` and `description` fields. Max 1024 characters total.
- `name`: letters, numbers, hyphens only
- `description`: Third-person, "Use when..." triggering conditions only — **NEVER summarize workflow** (see CSO below)

```markdown
---
name: skill-name-with-hyphens
description: "Use when [specific triggering conditions and symptoms]"
---
# Skill Name
## Overview — core principle in 1-2 sentences
## When to Use — symptoms, use cases, when NOT to use
## Core Pattern — before/after code comparison
## Quick Reference — table for scanning
## Implementation — inline or link to file
## Common Mistakes — what goes wrong + fixes
```

## Claude Search Optimization (CSO)

**CRITICAL: Description = When to Use, NOT What the Skill Does.** Testing revealed that descriptions summarizing workflow cause Claude to follow the description as a shortcut, skipping the full skill body.

```yaml
# BAD: Summarizes workflow — Claude follows this instead of reading skill
description: Use when executing plans - dispatches subagent per task with code review between tasks
# GOOD: Triggering conditions only
description: Use when executing implementation plans with independent tasks in the current session
```

**Keyword Coverage:** Use words Claude would search for — error messages, symptoms, synonyms, tool names.

**Naming:** Active voice, verb-first (`creating-skills` not `skill-creation`). Gerunds work well for processes.

**Token Efficiency:** getting-started < 150 words, frequently-loaded < 200 words, other skills < 500 words. Use cross-references instead of repeating content. Reference `--help` instead of documenting all flags.

**Cross-Referencing:** Use skill name with explicit markers:
- `**REQUIRED SUB-SKILL:** Use superpowers:test-driven-development`
- Never use `@` syntax (force-loads files, burns 200k+ context)

## RED-GREEN-REFACTOR for Skills

### RED: Baseline

Run pressure scenario with subagent WITHOUT the skill. Document: choices made, rationalizations used (verbatim), which pressures triggered violations.

### GREEN: Write Minimal Skill

Address those specific rationalizations. Run same scenarios WITH skill — agent should now comply.

### REFACTOR: Close Loopholes

New rationalization found? Add explicit counter. Re-test until bulletproof.

See `@testing-skills-with-subagents.md` for full testing methodology (pressure types, plugging holes, meta-testing).

## Bulletproofing Discipline Skills

- **Close every loophole explicitly** — don't just state the rule, forbid specific workarounds
- **Address "spirit vs letter"** — add: "Violating the letter of the rules is violating the spirit"
- **Build rationalization table** from baseline testing
- **Create red flags list** for agent self-checking
- See `persuasion-principles.md` for research foundation on persuasion techniques

## Flowcharts & Code Examples

**Flowcharts ONLY for:** non-obvious decisions, process loops, A/B choices. See `@graphviz-conventions.dot` for style.

**Code examples:** One excellent example beats many. Complete, runnable, from real scenario. Don't implement in 5+ languages.

## Skill Creation Checklist

**RED:** Create pressure scenarios → run WITHOUT skill → identify rationalization patterns
**GREEN:** Name (hyphens only), YAML frontmatter, "Use when..." description, keywords, clear overview, one example → run WITH skill → verify compliance
**REFACTOR:** New rationalizations → explicit counters → rationalization table → red flags → re-test
**Quality:** Flowchart only if non-obvious, quick reference table, common mistakes, no narratives
**Deploy:** Commit, push, consider contributing via PR

```
NO SKILL WITHOUT A FAILING TEST FIRST
```

No exceptions — not for "simple additions," not for "documentation updates." Delete means delete.
