---
name: systematic-debugging
description: "Use when encountering bugs, test failures, build errors, performance regressions, or unexpected behavior. Diagnoses root causes by reading error messages, reproducing issues, tracing data flow across component boundaries, and testing hypotheses one at a time before proposing any fix."
---

# Systematic Debugging

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## The Four Phases

Complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully** — read stack traces completely, note line numbers, file paths, error codes.

2. **Reproduce Consistently** — if not reproducible, gather more data. Don't guess.

3. **Check Recent Changes** — `git diff`, recent commits, new dependencies, config changes, environmental differences.

4. **Gather Evidence in Multi-Component Systems**

   For each component boundary: log what enters, log what exits, verify environment/config propagation.

   ```bash
   # Example: multi-layer diagnostic
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"
   env | grep IDENTITY || echo "IDENTITY not in environment"
   security list-keychains
   security find-identity -v
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   This reveals which layer fails (e.g., secrets → workflow ✓, workflow → build ✗).

5. **Trace Data Flow** — see `root-cause-tracing.md` for the complete backward tracing technique. Quick version: trace the bad value upstream until you find the source. Fix at source, not symptom.

### Phase 2: Pattern Analysis

1. **Find working examples** in same codebase — what works that's similar to what's broken?
2. **Compare against references** — read reference implementations completely, don't skim.
3. **Identify differences** — list every difference, however small. Don't assume "that can't matter."
4. **Understand dependencies** — what components, settings, config, environment does this assume?

### Phase 3: Hypothesis and Testing

1. **Form single hypothesis** — "I think X is the root cause because Y." Be specific.
2. **Test minimally** — smallest possible change, one variable at a time.
3. **Verify** — worked → Phase 4. Didn't work → new hypothesis. Don't stack fixes.

### Phase 4: Implementation

1. **Create failing test** — simplest reproduction. Use `superpowers:test-driven-development` for proper test structure.
2. **Implement single fix** — address root cause only. No bundled refactoring.
3. **Verify** — test passes, no regressions.
4. **If fix fails** — count attempts. < 3: return to Phase 1 with new information. ≥ 3: **STOP and question architecture.**

**3+ failures pattern**: each fix reveals new coupling, requires massive refactoring, or creates symptoms elsewhere → this is an architectural problem. Discuss with your human partner before attempting more fixes.

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## Supporting Techniques

- **`root-cause-tracing.md`** — trace bugs backward through call stack to find original trigger
- **`defense-in-depth.md`** — add validation at multiple layers after finding root cause
- **`condition-based-waiting.md`** — replace arbitrary timeouts with condition polling

**Related skills:**
- **superpowers:test-driven-development** — for creating failing test cases (Phase 4)
- **superpowers:verification-before-completion** — verify fix worked before claiming success
