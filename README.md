# Claude Code Engineering Suite

一套为 [Claude Code](https://code.claude.com) 设计的工程化配置方案，通过 Hooks 拦截、提示词注入与结构化协议，约束 AI 在 Python 开发任务中的行为边界与合规性。

## 核心机制

*   **交互约束 (Interaction Control)**:
    *   **协议承诺 (Protocol Commitment)**: 强制 AI 在每次实质回复前输出包含状态机与否定约束的三行协议头（Protocol Header）。配合 Hooks 实现 **System Prompt Refreshing**，通过高频重复注入对抗长上下文带来的指令衰减。
    *   **中断驱动工作流 (Interrupt-Driven Workflow)**: 任何用户提问、条件句或错误报告均被视为 **STOP** 信号。严禁在报错后自动执行“打地鼠”式修复，必须强制停机 (HALT) 并重新请求授权。
    *   **反黑话过滤器 (Anti-Jargon Filter)**: 在提示词末尾注入高权重词汇表，并在协议头中显式警示，从源头抑制“痛点/赋能”等非工程化词汇。

*   **环境修正 (Environment Correction)**:
    *   **路径归一化**: 通过 `hooks/pre_tool_guard.py` 拦截绝对路径。若路径位于项目内，自动转换为相对路径并放行；若位于项目外，则阻断并请求确认。
    *   **Shell 环境注入**: 针对 `Bash` 工具，自动注入 `PYTHONIOENCODING` 及 Conda/Mamba 激活脚本，确保跨平台 Shell 环境一致性。

*   **上下文管理 (Context Management)**:
    *   **自动快照**: 在压缩 (`/compact`) 前自动生成项目状态快照 (`.compact_args.md`)。
    *   **会话热启动**: 新会话启动 (`SessionStart`) 时自动加载快照，实现上下文无缝衔接。

## 目录结构

```text
.
├── CLAUDE.md              # 系统入口，定义核心 Persona 和静态协议
├── style.md               # 统一协议层 (定义 "Can/Cannot" 边界与 Agent 限制)
├── settings.example.json  # 配置文件模板 (含 Hooks 配置)
├── commands/              # 自定义指令
│   └── log-change.md      # /log-change: 生成结构化变更日志
├── output-styles/         # 输出风格定义
│   └── engineer-professional.md # 工程师角色卡 (定义语气、反模式与词汇表)
├── skills/                # 动态技能库 (按需加载)
│   ├── auditor/           # 审计代理: 双盲代码审查
│   ├── debug-protocol/    # 调试协议: Insert -> Observe -> Fix 闭环
│   ├── git-workflow/      # Git 规范: Conventional Commits
│   ├── code-modification/ # 代码修改: 防御性重构
│   ├── file-ops/          # 文件操作: 批量读写与 PVE 校验
│   └── tool-guide/        # 工具指南: MCP 选型策略
└── hooks/                 # 自动化脚本
    ├── context_manager.py # 上下文快照与恢复
    ├── env_enforcer.py    # 环境约束注入 (Prompt Injection)
    └── pre_tool_guard.py  # 路径/环境 前置拦截器
```

## 安装与配置

### 1. 部署文件
将本项目内容复制到 Claude Code 全局配置目录：
*   **macOS/Linux**: `~/.claude/`
*   **Windows**: `%USERPROFILE%\.claude\` (通常是 `C:\Users\<YourName>\.claude\`)

### 2. 应用配置
1.  将 `settings.example.json` 的内容合并到您的 `settings.json` 文件中（位于配置目录下）。
2.  **Windows 用户注意**:
    *   `settings.json` 不支持 `~` 路径展开。
    *   必须将所有路径修改为绝对路径 (例如: `C:/Users/YourName/.claude/hooks/...`)。建议使用正斜杠 `/`。

## 协议声明

本配置强制 AI 遵守以下工程原则，违者将触发拦截或协议头警示：

*   **Agent 降级策略**: 鉴于 Thinking Model (如 Gemini 3) 的特性，**Deprecated** `Plan` 和 `Task` Agent。**Prohibited** `Explore` Agent。强制使用 `TodoWrite` + 手动工具链。
*   **修改操作**: 遵循 `Analyze` -> `Plan` -> `Ask (Block)` -> `Execute (Silent)` 流程。
*   **只读操作**: 实行 **Direct Act**，立即执行无需请示。
*   **调试纪律**: 遵循 `Insert` -> `Observe` -> `Fix` -> `Verify` 闭环，严禁盲目猜测。
