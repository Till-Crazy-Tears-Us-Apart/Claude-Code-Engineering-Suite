# Milestone (里程碑管理)

Milestone 用于在技术开发周期中创建标准化的阶段性报告，并维护项目时间线索引。它强制执行“先审计后留档”的流程，确保技术决策和实验结果被完整记录。

## 核心功能

1.  **报告生成**: 自动捕捉最近的 Git 变更记录，生成结构化的 Markdown 报告草稿。
2.  **时间线同步**: 提取报告摘要，自动更新 `.claude/history/timeline.md` 索引表。
3.  **文档注入**: 通过 `hooks/doc_manager/injector.py` 自动更新 `CLAUDE.md` 中的时间线引用。

## 使用流程

### 1. 生成草稿
运行 `/milestone` 技能。系统将：
- 扫描 `git diff --staged` 或最近一次提交。
- 在 `.claude/history/reports/` 下创建以时间戳命名的报告文件（如 `20260130_103000.md`）。
- 自动更新 `.claude/history/timeline.md`，添加新行。

### 2. 编写内容
用户需编辑生成的报告文件，填写以下必填项（使用简体中文）：
- **1. 工作摘要 (Summary)**: 技术变更的简要总结。
- **2. 技术决策 (Technical Decisions)**: 记录关键架构选择及其理由。
- **3. 实现细节 (Implementation Details)**: 描述代码变更对数据流和系统状态的影响。

### 3. 同步摘要
报告编写完成后，再次运行 `/milestone` (或手动执行 `python skills/milestone/sync_timeline.py`)。系统将：
- 读取报告文件的 `## 1. 工作摘要 (Summary)` 章节。
- 将内容回填至 `timeline.md` 的表格中，确保索引与详情一致。

## 目录结构

```text
.claude/history/
├── timeline.md          # 核心索引表 (Date | ID | Link | Summary)
└── reports/             # 详细报告存储目录
    ├── 20260124_xxxx.md
    └── 20260130_xxxx.md
```

## 注意事项

- **禁止占位符**: `sync_timeline.py` 会检测并拒绝同步包含 `[AI TODO: ...]` 占位符的报告。
- **中文强制**: 报告内容必须使用简体中文。
- **文件幂等**: 多次运行生成脚本不会覆盖已存在的同名文件（基于分钟级时间戳）。
