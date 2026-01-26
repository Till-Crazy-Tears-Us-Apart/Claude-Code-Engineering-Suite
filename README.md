# Claude Code Engineering Suite

一套为 [Claude Code](https://code.claude.com) 设计的工程化配置方案，通过 Hooks 拦截、提示词注入与结构化协议，约束 AI 在 Python 开发任务中的行为边界与合规性。

## 环境限制

本项目对环境配置有以下偏好：

| 维度 | 要求 | 影响行为 |
| :--- | :--- | :--- |
| **软件版本** | Claude Code CLI >= 2.1.10 | 支持事件钩子机制和主动启动 skill |
| **操作系统** | Windows 优先 | 兼容路径处理与 Shell 语法 |
| **开发语言** | Python 3.7+ | 运行 Hooks 脚本 |
| **运行时环境** | Mamba / Conda | 自动注入 Shell 环境 |
| **交互语言** | 简体中文 | 协议头与输出强制中文 |
| **字符编码** | UTF-8 | 强制标准输入输出编码 |
| **Shell 语法** | POSIX Bash | 限制非标准语法使用 |
| **命名规范** | snake_case | 限制文件名格式 |
| **路径习惯** | 相对路径优先 | 自动转换绝对路径 |

## 设计哲学

本项目遵循“人机协作”原则，拒绝“完全自动化”：

*   **阶段性确认**: 执行修改前强制进行“分析-计划-确认”闭环，禁止盲目执行。
*   **显式授权**: 读取操作直接执行；写入操作必须通过 `AskUserQuestion` 获取明确授权。
*   **工具透明**: 优先使用原子化工具链，限制使用不可控的黑盒 Agent。

## 核心机制

### 1. 交互约束与协议
*   **协议注入**: 通过 `hooks/env_system/enforcer_hook.py` 实现强制 **System Prompt Refreshing**，对抗长上下文带来的指令衰减。
*   **中断驱动工作流**: 任何用户提问、条件句或错误报告均被视为 **STOP** 信号。严禁在报错后自动执行“打地鼠”式修复。
*   **反俚语过滤器**: 在提示词中注入词汇表，从源头抑制“痛点/赋能”等非工程化词汇。

### 2. 动态文件树
*   **自动维护**: 基于 `hooks/tree_system/` 自动维护 `.claude/project_tree.md` 快照。
*   **生命周期集成**: 在会话启动 (`SessionStart`) 和压缩前 (`PreCompact`) 自动更新，确保 AI 掌握最新结构。
*   **按需精简**: 支持通过 `.claude/tree_config` 控制目录深度和文件可见性。

### 3. 环境与路径防护
*   **路径归一化**: 通过 `hooks/pre_tool_guard.py` 拦截绝对路径，自动转换为项目内相对路径。
*   **Shell 环境增强**: 针对 `Bash` 工具自动注入 `PYTHONIOENCODING` 及 Conda/Mamba 激活脚本。
*   **Agent 拦截**: 拦截高耗时 Agent（如 `Explore`）并请求用户确认。

### 4. 上下文持久化
*   **自动快照**: 通过 `hooks/context_manager.py` 在压缩前生成项目状态快照 (`.claude/context_snapshot.md`)。
*   **无缝衔接**: 新会话启动时自动加载快照，恢复分支、提交记录及关键文件索引。

### 5. 核心开发工作流
本项目定义了严格的 "Plan-Act-Verify" 闭环，以下 Skills 需由用户**主动调用** (作为 Slash Commands)：

1.  **架构预审 (`/deep-plan`)**
    *   **阶段**: 计划阶段 (Plan)，在编写任何代码之前。
    *   **功能**: 执行 "零决策" 架构审计，输出 `物理变更预演表` 与 `逻辑契约审计表`，强制识别歧义与副作用。

2.  **里程碑报告 (`/milestone`)**
    *   **阶段**: 阶段性任务完成或 `/compact` 之前。
    *   **功能**: 手动触发生成结构化历史报告，记录技术决策、实验结果与遗留问题，并更新 `.claude/history/timeline.md` 索引。**强制**在上下文压缩前使用以固化记忆。

3.  **工程化修改 (`/code-modification`)**
    *   **阶段**: 执行阶段 (Act)，获得架构批准后。
    *   **功能**: 遵循 "Forked Context" 模式，强制执行数据流下游适配、框架完整性检查 (JIT/Numba) 及防御性编程。

4.  **变更固化 (`/log-change`)**
    *   **阶段**: 单次修改完成后。
    *   **功能**: 生成原子化的变更日志，记录 Q&A 与 Systemic Impact，作为审计阶段的信源之一。

5.  **上下文回退（`/rewind`）**
    *   **阶段**: 生成标准化变更日志后。
    *   **操作**：使用 /rewind 命令将对话上下文回退（Restore conversation only）到计划审计完成后、修改执行前的检查点。
    *   **功能**：确保 AI 不持对修改过程的记忆，从而避免在后续交互中引入偏见或误导，保持独立性。

5.  **三方审计 (`/auditor`)**
    *   **阶段**: 验证阶段 (Verify)，代码合并前。
    *   **功能**: 扮演 "对抗性审计员"，在无上下文前提下，基于变更日志进行 **"意图-日志-代码"** 的三方一致性校验。

## 目录结构

```text
.
├── CLAUDE.md                       # 系统入口，定义核心 Persona 和静态协议
├── style.md                        # 统一协议层 (定义 "Can/Cannot" 边界与 Agent 限制)
├── settings.example.json           # 配置文件模板 (含 Hooks 配置)
├── output-styles/                  # 输出风格定义
│   └── python-architect.md         # 工程师角色卡 (定义语气、反模式与词汇表)
├── skills/                         # 动态技能库 (按需加载)
│   ├── deep-plan/                  # 深度计划: 架构预审协议
│   ├── milestone/                  # 里程碑: 历史记录与阶段性总结
│   │   ├── generate_draft.py       # 草稿生成脚本
│   │   └── report_schema.json      # 报告内容规范
│   ├── code-modification/          # 代码修改: 工程化改动协议
│   ├── log-change/                 # 日志固化: 变更记录生成
│   ├── auditor/                    # 审计代理: 三方一致性校验
│   ├── update-tree/                # 树更新: 手动刷新快照 (Proactive 模式)
│   └── ...                         # 其他工程化技能 (TDD, Debugging, FileOps 等)
└── hooks/                          # 自动化钩子系统
    ├── pre_tool_guard.py           # 工具前置拦截 (路径、命名、环境)
    ├── context_manager.py          # 上下文快照与恢复 (SessionStart/PreCompact)
    ├── env_system/                 # 约束增强系统
    │   ├── enforcer_hook.py        # 协议注入 (UserPromptSubmit)
    │   └── reminder_prompt.md      # 约束提示词配置
    └── tree_system/                # 项目树自动化
        ├── generate_smart_tree.py  # 核心生成逻辑
        └── lifecycle_hook.py       # 生命周期集成
```

## 安装与配置

### 1. 部署文件
将本项目内容复制到 Claude Code 全局配置目录 `%USERPROFILE%\.claude\` / `~/.claude/` 下。

### 2. 应用配置
1.  将 `settings.example.json` 的内容合并到您的 `settings.json` 文件中。
2.  **路径设置**: 必须将所有路径修改为绝对路径 (例如: `C:/Users/YourName/.claude/hooks/...`)。

### 3. Git 配置 (推荐)
为了保持项目整洁，建议将自动生成的元数据目录加入 `.gitignore`：
```gitignore
.claude/
```

## 协议声明

本配置强制 AI 遵守以下工程原则：

*   **Agent 降级**: 废弃 `Plan` 和 `Task` Agent，严禁使用 `Explore` Agent。强制手动工具链。
*   **修改操作**: 遵循 `Analyze` -> `Plan` -> `Ask (Block)` -> `Execute (Silent)` 流程。
*   **命名规范**: 强制新文件使用 `snake_case`。
*   **调试纪律**: 遵循 `Insert` -> `Observe` -> `Fix` -> `Verify` 闭环。

## 鸣谢 / Credits

本项目中的部分 Skills 借鉴或移植自 **[superpowers](https://github.com/obra/superpowers)** 项目。感谢 Jesse Vincent (obra) 的贡献。
