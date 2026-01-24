# Claude Code Engineering Suite

一套为 [Claude Code](https://code.claude.com) 设计的工程化配置方案，通过 Hooks 拦截、提示词注入与结构化协议，约束 AI 在 Python 开发任务中的行为边界与合规性。

## 环境限制

本项目对环境配置有以下偏好：

| 维度 | 要求 | 影响行为 |
| :--- | :--- | :--- |
| **软件版本** | Claude Code CLI >= 2.1.8 | 支持事件钩子机制和主动启动skill |
| **开发语言** | Python 3.7+ | 运行 Hooks 脚本 |
| **运行时环境** | Mamba / Conda | 自动注入 Shell 环境 |
| **交互语言** | 简体中文 | 协议头与输出强制中文 |
| **字符编码** | UTF-8 | 强制标准输入输出编码 |
| **Shell 语法** | POSIX Bash | 限制非标准语法使用 |
| **命名规范** | snake_case | 限制文件名格式 |
| **路径习惯** | 相对路径优先 | 自动转换绝对路径 |

## 设计哲学

本项目遵循“人机协作 (Human-in-the-loop)”原则，拒绝“完全自动化 (Fire-and-forget)”：

*   **阶段性确认**: 执行修改前强制进行“分析-计划-确认”闭环，禁止盲目执行。
*   **显式授权**: 读取操作直接执行；写入操作必须通过 `AskUserQuestion` 获取明确授权。
*   **工具透明**: 优先使用原子化工具链，限制使用不可控的黑盒 Agent。

## 核心机制

*   **交互约束 (Interaction Control)**:
    *   **协议注入 (Protocol Injection)**: 通过 Hooks 实现强制 **System Prompt Refreshing**，通过高频重复注入协议头（Protocol Header）对抗长上下文带来的指令衰减。
    *   **中断驱动工作流 (Interrupt-Driven Workflow)**: 任何用户提问、条件句或错误报告均被视为 **STOP** 信号。严禁在报错后自动执行“打地鼠”式修复，必须强制停机 (HALT) 并重新请求授权。
    *   **反俚语过滤器 (Anti-Jargon Filter)**: 在提示词末尾注入高权重词汇表，并在协议头中显式警示，从源头抑制“痛点/赋能”等非工程化词汇。

*   **环境修正 (Environment Correction)**:
    *   **路径归一化**: 通过 `hooks/pre_tool_guard.py` 拦截绝对路径。若路径位于项目内，自动转换为相对路径并放行；若位于项目外，则阻断并请求确认。
    *   **Shell 环境注入**: 针对 `Bash` 工具，自动注入 `PYTHONIOENCODING` 及 Conda/Mamba 激活脚本，确保跨平台 Shell 环境一致性。

*   **上下文管理 (Context Management)**:
    *   **自动快照**: 在压缩 (`/compact`) 前自动生成项目状态快照 (`.compact_args.md`)。
    *   **会话热启动**: 新会话启动 (`SessionStart`) 时自动加载快照，实现上下文无缝衔接。

*   **动态技能库 (Dynamic Skills Inventory)**:
    *   **systematic-debugging**: 当遇到 Bug、测试失败或意外行为时，执行根因分析与修复闭环。
    *   **test-driven-development**: 当开发新功能或修复 Bug 时，遵循“红-绿-重构”流程，先写测试。
    *   **code-modification**: 当重构或修改现有代码时，确保接口兼容性与防御性编程。
    *   **git-workflow**: 当进行版本控制操作时，强制 Conventional Commits 规范与危险操作确认。
    *   **receiving-feedback**: 当接收代码审查意见时，先验证反馈的准确性再实施修改。
    *   **auditor**: 当需要独立代码审计或生成变更日志时，基于变更日志进行双盲验证。
    *   **file-ops**: 当涉及批量文件读写或 PVE 校验时，确保文件操作的安全性与原子性。
    *   **doc-updater**: 当代码变更影响系统行为时，同步更新核心文档 (`CLAUDE.md`)。

## 目录结构

```text
.
├── CLAUDE.md                       # 系统入口，定义核心 Persona 和静态协议
├── style.md                        # 统一协议层 (定义 "Can/Cannot" 边界与 Agent 限制)
├── settings.example.json           # 配置文件模板 (含 Hooks 配置)
├── commands/                       # 自定义指令
│   ├── log-change.md               # /log-change: 生成结构化变更日志
│   └── update-tree.md              # /update-tree: 手动更新项目树
├── output-styles/                  # 输出风格定义
│   └── python-architect.md         # 工程师角色卡 (定义语气、反模式与词汇表)
├── skills/                         # 动态技能库 (按需加载)
│   ├── auditor/                    # 审计代理: 双盲代码审查
│   ├── systematic-debugging/       # 调试协议: 系统化根因分析
│   ├── test-driven-development/    # TDD: 红-绿-重构闭环
│   ├── receiving-feedback/         # 反馈处理: 验证优于盲从
│   ├── git-workflow/               # Git 规范: Conventional Commits
│   ├── code-modification/          # 代码修改: 防御性重构
│   ├── file-ops/                   # 文件操作: 批量读写与 PVE 校验
│   ├── tool-guide/                 # 工具指南: MCP 选型策略
│   └── writing-skills/             # 技能编写: 技能即代码
└── hooks/                          # 自动化脚本
    ├── context_manager.py          # 上下文快照与恢复
    ├── env_system/
    │   ├── enforcer_hook.py        # 环境约束注入 (原 env_enforcer.py)
    │   └── reminder_prompt.md      # 约束提示词
    ├── tree_system/
    │   ├── generate_smart_tree.py  # 项目树生成器
    │   └── lifecycle_hook.py       # 自动更新钩子
    └── pre_tool_guard.py           # 路径/环境 前置拦截器
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

## 鸣谢 / Credits

本项目中的部分 Skills (如 `systematic-debugging`, `test-driven-development` 等) 借鉴或移植自 **[superpowers](https://github.com/obra/superpowers)** 项目。特此感谢 Jesse Vincent (obra) 对 Claude Code 社区的贡献。
