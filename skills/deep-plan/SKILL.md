---
name: deep-plan
description: Use when an implementation plan is proposed but requires a deep architectural audit for risks, side effects, and ambiguities before writing any code.
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "[plan_summary (optional)]"
disable-model-invocation: true
---

# Deep Plan Audit Protocol

This skill enforces a rigorous pre-implementation review based on the **6-Point Defensive Check** and **Zero-Decision Principles**.

## 1. Execution Context
**Goal**: Identify architectural risks, side effects, and ambiguities that normal planning might miss.

## 2. Analysis Output (Strict Tables)

Prior to generating tables, you must perform a preliminary risk scan using Chain of Thought. Identify potential issues in the following areas:
1.  **Ambiguity**: Locate any "TBD" or vague parameters.
2.  **Side Effects**: Check for global state modification or OS-specific assumptions.
3.  **Consistency**: Verify library calls match actual signatures in the codebase.

After scanning, output your analysis in the following two markdown tables.

### Table 1: Physical Change Simulation (物理变更预演)
*   **Minimalist Check Criteria**: Confirm no changes to unrelated whitespace, comments, or indentation.
*   **Ripple Effect Criteria**: Confirm imports and dependencies do not create circular references.

| 文件路径 | 定位 | 操作 | 简述 | 最小化验证 | 涟漪效应 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `path/to/file` | `func_name` (L10) | Modify | 增加超时重试逻辑 | ✅ 仅修改目标函数 | 无 |

### Table 2: Logic & Contract Audit (逻辑与契约审计)
*   **Locked Status**: Requires explicit values (e.g., "5000ms"). Vague terms result in "Fail".
*   **Data Flow**: Verify upstream/downstream parameter compatibility.

| 维度 | 检查项 | 状态 | 决策/规约 |
| :--- | :--- | :--- | :--- |
| **数据流** | 上游依赖 / 下游兼容 | Pass/Warn | (Must define specific data contract) |
| **一致性** | 函数签名 / 库调用 | Pass/Fail | (Check recursively against definitions) |
| **数据结构** | 硬编码 / 参数化 | Pass/Locked | (Must prioritize args/config over hardcoding) |
| **系统风险** | 副作用 / 环境兼容 | Pass/Warn | (Check global mechanisms & OS differences) |
| **复杂度** | 时间 / 空间 / OOM | Pass/Warn | (Assess loops & memory usage) |
| **并发与锁** | 读写冲突 / 死锁 | Pass/Warn | (Check file IO & shared resources) |
| **零决策** | 参数锁定 / 歧义消除 | Locked | (No "TBD" allowed. Specify values.) |
| **验证契约** | 不变量 / 验收标准 | Def | (Define falsifiable success criteria) |

## 3. Strict Schema Compliance (Implicit)

You MUST read `~/.claude/skills/deep-plan/output_schema.json` to understand the required verification depth.
**Do NOT output the JSON block.**
Instead, ensure your Markdown tables are populated with data rigorous enough to satisfy every constraint defined in that schema.

## 4. Critical Rules
1.  **Stop & Think**: Do not generate this report if you haven't read the relevant files yet. Read them first.
2.  **Be Harsh**: The goal is to find problems, not to validate the plan. Play the "Devil's Advocate".
3.  **No Code Generation**: This step is pure analysis. Do not write implementation code here.

## 5. Explicit Stop Protocol (MANDATORY)
**CRITICAL**: You MUST generate ALL tables and analysis text in your response BEFORE calling any tool. The `AskUserQuestion` tool call MUST be the absolute LAST action in your turn.

1.  Do **NOT** write any code.
2.  Do **NOT** apply any changes.
3.  Use the `AskUserQuestion` tool to present the user with the option to proceed or revise.
    *   Question: "Audit Complete. How should we proceed?"
    *   Options: ["Proceed with Implementation", "Revise Plan", "Cancel"]
