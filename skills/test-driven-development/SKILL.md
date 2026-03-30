---
name: test-driven-development
description: "Use when implementing any feature or bugfix, before writing implementation code. Enforces the RED-GREEN-REFACTOR cycle: write a failing test first, write minimal code to pass it, then refactor while keeping tests green. Applies to new features, bug fixes, refactoring, and behavior changes."
user-invocable: false
---

# Test-Driven Development (TDD)

**Core principle:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Violating the letter of the rules is violating the spirit of the rules.**

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Write code before the test? Delete it. Start over. Don't keep it as "reference." Don't "adapt" it. Delete means delete.

## Red-Green-Refactor

**RED → verify fail → GREEN → verify pass → REFACTOR → repeat**

### RED — Write Failing Test

Write one minimal test showing what should happen.

```typescript
// Good: clear name, tests real behavior, one thing
test('retries failed operations 3 times', async () => {
  let attempts = 0;
  const operation = () => {
    attempts++;
    if (attempts < 3) throw new Error('fail');
    return 'success';
  };
  const result = await retryOperation(operation);
  expect(result).toBe('success');
  expect(attempts).toBe(3);
});
```

Requirements: one behavior, clear name, real code (no mocks unless unavoidable).

### Verify RED

```bash
npm test path/to/test.test.ts
```

Confirm: test fails (not errors), failure message is expected, fails because feature is missing (not typos). Test passes? Fix test. Test errors? Fix error, re-run.

### GREEN — Minimal Code

Write simplest code to pass the test. Don't add features, refactor other code, or "improve" beyond the test.

```typescript
async function retryOperation<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 3; i++) {
    try { return await fn(); }
    catch (e) { if (i === 2) throw e; }
  }
  throw new Error('unreachable');
}
```

### Verify GREEN

```bash
npm test path/to/test.test.ts
```

Confirm: test passes, other tests still pass, output pristine. Test fails? Fix code, not test.

### REFACTOR

After green only: remove duplication, improve names, extract helpers. Keep tests green. Don't add behavior.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test('validates email and domain and whitespace')` |
| **Clear** | Name describes behavior | `test('test1')` |
| **Shows intent** | Demonstrates desired API | Obscures what code should do |

## Example: Bug Fix

**Bug:** Empty email accepted

**RED** → `test('rejects empty email', () => { expect(submitForm({email: ''}).error).toBe('Email required'); })`
**Verify** → `FAIL: expected 'Email required', got undefined`
**GREEN** → Add `if (!data.email?.trim()) return { error: 'Email required' };`
**Verify** → `PASS`
**REFACTOR** → Extract validation for multiple fields if needed.

## Red Flags — STOP and Start Over

Code before test, test passes immediately, rationalizing "just this once," "keep as reference," "tests after achieve the same purpose," "TDD is dogmatic."

**All of these mean: Delete code. Start over with TDD.**

## Verification Checklist

- [ ] Every new function/method has a test
- [ ] Watched each test fail before implementing
- [ ] Each test failed for expected reason
- [ ] Wrote minimal code to pass each test
- [ ] All tests pass, output pristine
- [ ] Tests use real code (mocks only if unavoidable)
- [ ] Edge cases and errors covered

Can't check all boxes? You skipped TDD. Start over.

## When Stuck

| Problem | Solution |
|---------|----------|
| Don't know how to test | Write wished-for API. Assertion first. Ask your human partner. |
| Test too complicated | Design too complicated. Simplify interface. |
| Must mock everything | Code too coupled. Use dependency injection. |

## Testing Anti-Patterns

Read @testing-anti-patterns.md to avoid: testing mock behavior instead of real behavior, adding test-only methods to production classes, mocking without understanding dependencies.

```
Production code → test exists and failed first
Otherwise → not TDD
```

No exceptions without your human partner's permission.
