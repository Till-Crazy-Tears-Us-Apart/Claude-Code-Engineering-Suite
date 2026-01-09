# Claude Code Engineering Suite

一个为 [Claude Code](https://code.claude.com) + [Claude Code Router](https://github.com/musistudio/claude-code-router) 的氛围编程框架设计的提示词工程系统，通过更严格的约束、模块化的技能定义和自动化的上下文注入，抑制模型的幻觉问题，将 Claude Code 转变为一个**纪律严明、基于证据、遵循开发流程**的 python 开发者。

## 🚀 核心特性

- **工程化思维 (Engineering Mindset)**: 内置 Linus Torvalds (数据结构优先)、Kent Beck (TDD/反馈驱动) 和 John Ousterhout (深模块) 的工程哲学。
- **PVE 工作流 (Plan-Verify-Execute)**: 强制执行“计划-验证-执行”循环，严禁盲目修改代码。
- **严格调试协议**: 实施强制性的 6 步调试生命周期 (Insert -> Observe -> Fix -> Verify -> Confirm -> Clean Up)，拒绝“打地鼠”式修复。
- **持续上下文注入**: 利用 Claude Code 的 Hooks 机制，通过 Python 脚本在每次对话中动态注入核心指令，确保 AI 始终“不忘初心”。
- **模块化技能系统**: 将 Git 工作流、文件操作、代码审查等能力封装为独立的 Skills，按需加载，降低上下文开销。

## 📂 目录结构

```text
.
├── CLAUDE.md              # 系统入口，定义核心 Persona 和静态指令
├── style.md               # 统一风格指南 (通信协议、工程宪法)
├── language.md            # 语言偏好设置
├── settings.example.json  # 配置文件模板 (含 Hook 配置)
├── commands/              # 自定义 Slash 命令 (如 /prepare-compact)
├── output-styles/         # 输出风格定义 (默认为 engineer-professional)
├── skills/                # 动态技能库
│   ├── debug-protocol/    # 调试协议 (核心技能)
│   ├── git-workflow/      # Git 操作规范
│   ├── file-ops/          # 文件安全操作
│   └── ...
└── hooks/                 # 自动化脚本
    └── tabu_reminder.py   # 核心指令注入脚本
```

## 🛠️ 安装与配置

### 1. 复制文件
将本项目的所有文件复制到你的 Claude Code 全局配置目录中。
- Windows: `%USERPROFILE%\.claude\`
- macOS/Linux: `~/.claude/`

### 2. 配置 Settings (⚠️ 重要)
本项目包含一个 `settings.example.json`。**切勿直接覆盖**你现有的 `settings.json`（如果存在）。

1.  如果你的 `.claude` 目录中没有 `settings.json`，将 `settings.example.json` 重命名为 `settings.json`。
2.  如果已有 `settings.json`，请手动合并内容。

**关键配置修改**：
打开 `settings.json`，找到 `UserPromptSubmit` 钩子配置。由于 Claude Code 目前需要绝对路径来执行外部脚本，**你必须修改 `command` 字段中的路径为你本地的实际路径**。

```json
"hooks": {
  "UserPromptSubmit": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          // ⚠️ 修改下方路径为你机器上的实际绝对路径 ⚠️
          "command": "python3 C:/Users/YourName/.claude/hooks/tabu_reminder.py"
        }
      ]
    }
  ]
}
```

*注意：请确保你的系统环境中已安装 Python 3，并且 `python3` (或 `python`) 命令在 PATH 中可用。*

### 3. 验证安装
重启 Claude Code 终端，输入 `CLAUDE.md` 定义的任意指令或开始对话。如果 Hook 配置正确，系统将在每次交互时自动应用 `<core_directives>` 约束。

## 🧠 设计哲学

### 沟通协议 (Communication Protocol)
本系统强制 Claude 采用 **"No Fluff" (无废话)** 的沟通风格：
- **拒绝**: 奉承、客套话、主观臆断、情绪化表达。
- **坚持**: 客观事实、证据支持、简洁直接、专业术语。
- **禁止词汇**: "完美的"、"彻底的"、"我保证"、"根本原因" (在未验证前)。

### 工具使用规范 (Tool Usage)
- **串行执行**: 严禁并行调用有依赖关系的工具。
- **静默执行**: 工具调用期间不输出任何中间对话（Chatter）。
- **写后即读**: 任何 `Edit` 或 `Write` 操作后必须紧跟 `Read` 进行验证。

## 🔧 自定义

- **修改语言**: 编辑 `language.md` 可调整 AI 的回复语言（默认配置为简体中文）。
- **调整风格**: 编辑 `style.md` 可微调 AI 的性格设定和工程原则。
- **扩展技能**: 在 `skills/` 目录下参考现有结构添加新的技能文件夹和 `SKILL.md`。

## ⚠️ 免责声明
本系统旨在辅助 python 软件开发活动。用户需对 AI 生成的代码和执行的操作负责。在执行破坏性操作（如删除文件、强制 Git 回滚）前，系统会要求用户确认，但用户仍应保持警惕。
