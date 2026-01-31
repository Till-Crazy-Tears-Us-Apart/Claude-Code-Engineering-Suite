# 🧠 Logic Indexer (推理式语义索引器)

Logic Indexer 是一个基于 AST（抽象语法树）和 Google Gemini API 的语义索引工具。它通过解析 Python 代码并生成精简的语义摘要，帮助 Claude Code 在不读取完整源码的情况下理解项目逻辑。

## 🌟 核心特性

- **AST 精确解析**: 能够识别 Class、Function、Method 等代码结构，而非简单的文本分块。
- **跨文件上下文感知**: 自动解析 Python `import` 依赖，将上游模块的语义摘要注入 Prompt，使 LLM 理解跨文件调用链。
    - **别名支持**: 完整支持 `import ... as ...` 语法解析，消除引用盲区。
- **增量更新**:
    - **文件级哈希**: 基于源码内容计算 MD5。
    - **依赖感知哈希**: 当被依赖文件的摘要变更时，自动触发下游文件重新分析，确保逻辑一致性。
    - **精准变更追踪 (Usage-Aware)**: 引入 `UsageVisitor`，仅当被引用符号在当前文件中**实际使用**时才触发更新，大幅减少无效 LLM 调用。
- **混合摘要策略**:
    - **Docstring 优先**: 自动提取源码中已有的文档字符串（带有 `[Doc]` 标识），零成本。
    - **短函数跳过**: 对小于 3 行且无文档的函数自动标记为 "Small utility function."（可配置）。
    - **LLM 语义增强**: 仅对复杂逻辑调用 Gemini API 生成摘要。
- **数据流追踪**: 强制 LLM 识别数据源 `[Source]` 和数据汇点 `[Sink]`，明确数据流向。
- **健壮性设计**:
    - **原子回退 (Atomic Fallback)**: 批处理若因 JSON 解析或截断失败，自动降级为单符号处理模式，保证高成功率。
    - **截断恢复**: 智能检测 API 响应截断，并触发自动重试。
    - 内置指数退避重试、严苛熔断机制（遇 429/401 自动停止）和断点续传保护。

## ⚙️ 配置指南

### 1. 环境变量 (`settings.json`)

在项目的 `settings.json` (或全局 `~/.claude/settings.json`) 中配置以下参数：

```json
{
  "env": {
    "GEMINI_API_KEY": "...",
    "GEMINI_MODEL": "gemini-3-flash-preview",
    "GEMINI_MAX_WORKERS": "2",
    "GEMINI_BASE_URL": "https://generativelanguage.googleapis.com/v1beta",
    "GEMINI_RETRY_LIMIT": "3",
    "GEMINI_TIMEOUT": "60"
  }
}
```

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `GEMINI_MAX_WORKERS` | `5` | 并发线程数。若遇 429 限流，请调低此值（建议 1-3）。 |
| `GEMINI_RETRY_LIMIT` | `3` | API 失败重试次数。 |
| `GEMINI_TIMEOUT` | `60` | 单次请求超时时间（秒）。 |
| `GEMINI_MAX_OUTPUT_TOKENS` | `8192` | 响应 Token 上限，防止大文件摘要截断。 |
| `LOGIC_INDEX_AUTO_INJECT` | `ALWAYS` | `ALWAYS` (自动注入), `ASK` (询问), `NEVER` (仅生成)。 |
| `LOGIC_INDEX_FILTER_SMALL` | `false` | 是否跳过微型函数（<3行无文档）的 LLM 调用。 |

### 2. 排除规则 (`.claude/logic_index_config`)

该文件语法类似 `.gitignore`，用于排除不需要建立索引的文件或目录。支持 `!` 前缀和通配符。

**示例**:
```text
!tests/          # 排除测试代码
!**/migrations/  # 排除数据库迁移文件
!setup.py        # 排除特定文件
```

## 💰 成本控制与 Thinking 模式

Logic Indexer 针对 Gemini 3 Flash 模型采用了动态 Thinking Level 策略以节省成本：

| 代码复杂度 | 判定依据 | Thinking Level | 说明 |
| :--- | :--- | :--- | :--- |
| **Simple** | 行数 < 100 且无元编程关键词 | `MINIMAL` | 极速模式，消耗极少 Token。 |
| **Complex** | 行数 > 100 或包含 `yield`/`eval` 等 | `low` | 开启轻量推理，确保复杂逻辑总结准确。 |

> **提示**: 尽量为代码编写 Docstring！如果函数有 Docstring，系统会直接使用它（`[Doc]` 模式），完全不调用 API，成本为 0。

## 🔧 故障排除

### Q: 遇到 `Fatal API Error 429: Rate limit exceeded`？
**A**: Gemini 免费层级或低配额账号容易触发限流。
- **解决**: 将 `GEMINI_MAX_WORKERS` 设置为 `1`（串行模式），或申请更高配额。

### Q: 遇到 `Fatal API Error 403: Forbidden`？
**A**: API Key 无效或该 Key 无权访问指定的模型。
- **解决**: 检查 `GEMINI_API_KEY` 是否正确，确认 `GEMINI_MODEL` 在您所在的区域可用。

### Q: 运行中断后，之前的进度会丢失吗？
**A**: **不会**。系统采用了 `try...finally` 保护机制，即使中途通过 `Ctrl+C` 强行终止或触发熔断，已生成的摘要也会被强制保存到 `.claude/logic_index.json` 中。下次运行将自动跳过已处理的节点。

### Q: 为什么生成的 `logic_tree.md` 没有注入到 `CLAUDE.md`？
**A**: 如果扫描过程中触发了熔断（Fatal Error），为了防止将包含错误信息的树注入文档，系统会自动跳过注入步骤。
- **解决**: 修复 API 问题后重新运行一次 Skill。
