---
name: code-modification
description: "Use when modifying, refactoring, or optimizing existing code. Traces data flow and call chains, verifies library signatures before writing code, checks Numba/JIT and decorator compatibility, enforces incremental changes over big-bang rewrites, and validates all downstream consumers are updated."
allowed-tools: Read, Edit, Write, Grep, Glob, Bash
disable-model-invocation: true
---

# Code Modification Standards

## Core Principles

1. **Downstream Adapts**: Modifications flow downstream. If you change a core data structure or API, update all consumers. Trace the data flow first.

2. **Configuration Over Hardcoding**: Use constants, config files, or function arguments. If configuration is impossible, inform the user before proceeding.

3. **Framework Integrity**: Do NOT break cross-file frameworks.
   - **Numba/JIT**: Verify new logic is supported in `nopython` mode for the specific Numba version in use.
   - **Decorators**: Respect existing metaprogramming patterns.

4. **Performance Preservation**: Respect existing optimizations (numpy vectorization, memory views, JAX arrays). If a change introduces overhead (view → copy, broken loop fusion), justify it or find an alternative.

5. **Verify, Don't Guess**: Never assume a function exists or has a specific signature. Read the library code or use `context7` / documentation tools to verify signatures before writing code.

6. **Incremental Change**: Minimize blast radius with additive changes. If a total rewrite is necessary, PAUSE and ask for user permission explaining why.

7. **Minimal Noise**: Only change what is necessary. Do NOT touch unrelated comments, formatting, whitespace, or variable names. Analyze the call chain for logical consistency across the project.

## Workflow

**Phase 1: Discovery & Tracing**
1. Map dependencies: use `grep` or `glob` to locate all files that import or call the target files.
2. Verify signatures of any external functions you intend to use.

**Phase 2: Framework Compliance**
1. If modifying `@jit` / `@numba` code, verify new logic is supported in `nopython` mode.
2. Ensure `numpy` / `jax` array operations don't trigger unintended copies or device transfers.

**Phase 3: Execution (Read-Plan-Edit)**
1. Pre-Read the file.
2. Apply the change.
3. Post-Read to verify the change was applied correctly.

**Phase 4: Validation**
1. Run tests specified in your plan.
2. If tests fail, diagnose the failure — do not blindly retry. See `superpowers:systematic-debugging`.
