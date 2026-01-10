# Claude Code Engineering Suite

一套为 [Claude Code](https://code.claude.com) 设计的工程化配置方案，旨在通过结构化的协议约束、自动化的环境检查和模块化的技能定义，提升 AI 在 Python 开发任务中的准确性与合规性。

## 核心功能

*   **环境安全 (Environment Safety)**:
    *   **Hook 拦截**: 通过 `hooks/pre_tool_guard.py` 自动拦截并修正绝对路径使用，智能检查文件名规范 (snake_case)。
    *   **自动配置**: 针对 `Bash` 工具，自动注入 `PYTHONIOENCODING` 及 Conda/Mamba 激活脚本，确保 Shell 环境一致性。
    *   **持续强化**: 通过 `hooks/env_enforcer.py` 在交互中维持对核心环境约束的注意力。
*   **上下文管理 (Context Management)**:
    *   **自动快照**: 在压缩 (`/compact`) 前自动生成项目状态快照 (`.compact_args.md`)。
    *   **会话热启动**: 新会话启动 (`SessionStart`) 时自动加载快照，实现无缝衔接。
*   **审计协议 (Audit Protocol)**:
    *   **结构化日志**: 提供 `/log-change` 指令，生成包含技术决策、数据流分析和涟漪效应的标准化变更日志。
    *   **双盲复核**: 定义 `auditor` 子代理，在无编辑记忆的前提下，基于日志对代码进行对抗性审查。

## 目录结构

```text
.
├── CLAUDE.md              # 系统入口，定义核心 Persona 和静态协议
├── style.md               # 统一风格指南 (通信协议、工程原则)
├── settings.example.json  # 配置文件模板 (含 Hooks 配置)
├── commands/              # 自定义指令
│   └── log-change.md      # 标准化变更日志生成指令：强制生成包含Q&A与数据流分析的结构化文档
├── output-styles/         # 输出风格定义
│   └── engineer-professional.md
├── skills/                # 动态技能库
│   ├── auditor/           # 审计代理技能：基于日志对代码进行"双盲"对抗性审查，拒绝仪式化测试
│   ├── debug-protocol/    # 调试协议技能：强制执行 Insert -> Observe -> Fix 科学调试闭环
│   ├── git-workflow/      # Git工作流技能：规范 Commit Message 与版本控制行为
│   ├── code-modification/ # 代码修改技能：确保重构安全与架构完整性
│   └── ...
└── hooks/                 # 自动化脚本
    ├── context_manager.py # 上下文快照与恢复
    ├── env_enforcer.py    # 环境约束注入
    └── pre_tool_guard.py  # 工具调用前的安全检查与修正
```

## 安装与配置

### 1. 部署文件
将本项目内容复制到 Claude Code 全局配置目录：
*   **macOS/Linux**: `~/.claude/`
*   **Windows**: `%USERPROFILE%\.claude\` (通常是 `C:\Users\<YourName>\.claude\`)

### 2. 应用配置
1.  将 `settings.example.json` 重命名为 `config.json`（或合并到现有的 `config.json` 中）。
2.  **Windows 用户特别注意**：
    *   `settings.example.json` 默认使用了 Unix 风格的路径 (`~/.claude/hooks/...`)。
    *   **Windows `cmd.exe` 不支持 `~` 符号**。您**必须**手动将所有 `~` 替换为您实际的绝对路径。
    *   *示例*: 将 `~/.claude/hooks/pre_tool_guard.py` 修改为 `C:/Users/YourName/.claude/hooks/pre_tool_guard.py` (推荐使用正斜杠 `/`)。
3.  **验证**: 重启 Claude Code，确保没有报错。

### 3. 环境要求
*   **平台兼容性**: 本配置默认针对 **Windows + PowerShell** 环境下的 Claude Code 进行了优化（Bash 指令通常在后台通过 WSL 或 Git Bash 执行）。
    *   **迁移提示**: 若在原生 Linux、macOS 或纯 Git Bash 环境下使用，可能需要微调 `CLAUDE.md` 或 `hooks/` 中的路径处理逻辑及 Shell 交互提示词（如 POSIX 语法的具体约束）。
*   请确保系统 PATH 中 `python` 指向 Python 3.x。
*   如果您的项目需要特定的环境初始化（如 source 特定的 setup 脚本），请在项目根目录下创建 `.env_setup.sh` 文件。`pre_tool_guard.py` 会优先加载该文件。否则，系统将尝试自动探测 `mamba` 或 `conda`。

## 使用说明

### 日志与审计
1.  **记录**: 开发完成后，运行 `/log-change [TaskID] [Status]` 生成结构化日志。
2.  **审计**: 启动新会话，指示 AI 使用 `auditor` 代理，基于生成的日志文件对代码进行盲审。

### 自动合规
*   **路径检查**: 系统会自动拦截绝对路径的使用（Read 操作除外），并请求用户确认。
*   **命名规范**: 系统会自动检测 kebab-case 文件名，并在确认文件存在性后尝试自动纠正为 snake_case。

## 协议声明

本配置强制 AI 遵守以下工程原则：
*   **交互协议 (P-A-E-R)**:
    *   **修改操作**: 遵循 Plan -> Ask -> Execute (Silent) -> Report 闭环。
    *   **只读操作**: 实行 **Direct Act**，立即执行无需请示。
*   **调试纪律**: 遵循 Insert -> Observe -> Fix -> Verify 闭环。
*   **沟通风格**: 客观、无形容词、证据导向；严禁过渡性废话与预告。
