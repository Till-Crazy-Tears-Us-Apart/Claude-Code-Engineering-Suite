# Claude Code Engineering Suite

一个为 [Claude Code](https://code.claude.com) + [Claude Code Router](https://github.com/musistudio/claude-code-router) 的氛围编程框架设计的提示词工程系统，通过更严格的约束、模块化的技能定义和自动化的上下文注入，抑制模型的幻觉问题，将 Claude Code 转变为一个**纪律严明、基于证据、遵循开发流程**的 python 开发者。

## 📂 目录结构

```text
.
├── CLAUDE.md              # 系统入口，定义核心 Persona 和静态指令
├── style.md               # 统一风格指南 
├── language.md            # 语言偏好设置
├── settings.example.json  # 配置文件模板 (含 Hook 配置)
├── commands/              # 自定义 Slash 命令 
├── output-styles/         # 输出风格定义
├── skills/                # 动态技能库
│   ├── debug-protocol/    # 调试协议
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

## 🔧 自定义

- **修改语言**: 编辑 `language.md` 可调整 AI 的回复语言（默认配置为简体中文）。
- **调整风格**: 编辑 `style.md` 可微调 AI 的性格设定和工程原则。
- **扩展技能**: 在 `skills/` 目录下参考现有结构添加新的技能文件夹和 `SKILL.md`。

## ⚠️ 免责声明
本系统旨在辅助 python 软件开发活动。用户需对 AI 生成的代码和执行的操作负责。在执行破坏性操作（如删除文件、强制 Git 回滚）前，系统会要求用户确认，但用户仍应保持警惕。
