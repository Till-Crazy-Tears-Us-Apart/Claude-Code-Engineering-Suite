# Logic Indexer (推理式语义索引器)

Logic Indexer 是一个基于多语言源码解析和 OpenAI-compatible API 的语义索引工具。它通过解析 Python、C、C++、TypeScript/TSX 代码并生成精简的语义摘要，帮助 Claude Code 在不读取完整源码的情况下理解项目逻辑。

## 支持的语言

| 语言 | 扩展名 | 解析方式 |
| :--- | :--- | :--- |
| Python | `.py` | 标准库 `ast` 模块（内置） |
| C | `.c`, `.h` | 正则（内置）/ tree-sitter（可选） |
| C++ | `.cpp`, `.hpp`, `.cc`, `.cxx`, `.hh`, `.hxx` | 正则（内置）/ tree-sitter（可选） |
| TypeScript | `.ts`, `.tsx` | 正则（内置）/ tree-sitter（可选，需 `tree-sitter-typescript`） |

`.h` 文件自动检测：若包含 `class`、`namespace`、`template` 等 C++ 关键字，使用 C++ 语法解析。

## 核心特性

- **多语言支持**: 可插拔的 `LanguageParser` 架构，按文件扩展名自动分发至对应解析器。
- **AST 精确解析 (Python)**: 识别 Class、Function、Method 等代码结构。
- **正则 + tree-sitter 双路径 (C/C++/TypeScript)**: 默认零依赖正则模式；安装 tree-sitter 后自动切换至高精度模式。
- **跨文件上下文感知**: 解析 Python `import` 和 C/C++ `#include "..."` 依赖，将上游模块的语义摘要注入 Prompt。
- **增量更新**:
    - **文件级哈希**: 基于源码内容计算 MD5。
    - **依赖感知哈希**: 被依赖文件的摘要变更时，自动触发下游文件重新分析。
    - **精准变更追踪 (Usage-Aware)**: 仅当被引用符号在当前文件中实际使用时才触发更新。
- **混合摘要策略**:
    - **Docstring/Doxygen 优先**: 自动提取 Python docstring 和 C/C++ Doxygen 注释（`[Doc]` 标识），零成本。
    - **短函数跳过**: 对小于 3 行且无文档的函数自动标记（可配置）。
    - **LLM 语义增强**: 仅对复杂逻辑调用 LLM API 生成摘要。
- **数据流追踪**: 强制 LLM 识别数据源 `[Source]` 和数据汇点 `[Sink]`。
- **健壮性设计**:
    - **原子回退 (Atomic Fallback)**: 批处理失败时自动降级为单符号处理模式。
    - **截断恢复**: 智能检测 API 响应截断并触发自动重试。
    - 内置指数退避重试、熔断机制（429/401 自动停止）和断点续传保护。

## 安装 tree-sitter（可选）

C/C++ 和 TypeScript/TSX 解析默认使用正则模式（零依赖）。安装 tree-sitter 可提升解析精度：

```bash
pip install tree-sitter tree-sitter-c tree-sitter-cpp tree-sitter-typescript
```

**C/C++**：

| 特性 | 正则模式 | tree-sitter 模式 |
| :--- | :--- | :--- |
| 函数/struct/enum/macro | 支持 | 支持 |
| class 方法 | 支持 | 支持 |
| namespace 嵌套 | 仅外层 | 全部层级 |
| template class | 不支持 | 支持 |
| 运算符重载 | 不支持 | 支持 |

**TypeScript/TSX**：

| 特性 | 正则模式 | tree-sitter 模式 |
| :--- | :--- | :--- |
| function/class/interface/enum/type/namespace | 支持 | 支持 |
| 箭头函数（`export const foo = () => {}`） | 不支持 | 支持 |
| abstract class 方法 | 不支持 | 支持 |
| 嵌套 namespace 成员 | 不支持 | 支持 |
| TSX grammar（`.tsx`） | 支持（正则不区分） | 独立 grammar |

## 配置指南

### 1. 环境变量 (`settings.json`)

在项目的 `settings.local.json`（或全局 `~/.claude/settings.json`）中配置：

```json
{
  "env": {
    "OPENAI_API_KEY": "...",
    "OPENAI_MODEL": "glm-5",
    "OPENAI_MAX_WORKERS": "3",
    "OPENAI_BASE_URL": "https://coding.dashscope.aliyuncs.com/v1/chat/completions",
    "OPENAI_RETRY_LIMIT": "3",
    "OPENAI_TIMEOUT": "300"
  }
}
```

| 变量名 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | - | API 密钥 |
| `OPENAI_MODEL` | `glm-5` | 模型名称 |
| `OPENAI_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1/chat/completions` | API 端点 |
| `OPENAI_MAX_WORKERS` | `3` | 并发线程数 |
| `OPENAI_RETRY_LIMIT` | `3` | 重试次数 |
| `OPENAI_TIMEOUT` | `300` | 超时时间（秒） |
| `OPENAI_MAX_TOKENS` | `8192` | 响应 Token 上限 |
| `LOGIC_INDEX_AUTO_INJECT` | `ALWAYS` | `ALWAYS`/`ASK`/`NEVER` |
| `LOGIC_INDEX_FILTER_SMALL` | `false` | 是否跳过微型函数 |
| `LOGIC_INDEX_LANG` | `Simplified Chinese` | 摘要输出语言 |

### 2. 排除规则 (`.claude/logic_index_config`)

语法类似 `.gitignore`，`!` 前缀排除，支持通配符。

```text
!tests/
!**/migrations/
!**/CMakeFiles/
!**/*.o
```

## 符号类型

| 图标 | 含义 | 适用语言 |
| :--- | :--- | :--- |
| `[C]` | Class | Python, C++, TypeScript |
| `[f]` | Function | Python, C, C++, TypeScript |
| `[S]` | Struct | C, C++ |
| `[E]` | Enum | C, C++, TypeScript |
| `[T]` | Typedef / TypeAlias | C, C++, TypeScript |
| `[M]` | Macro | C, C++ |
| `[N]` | Namespace | C++, TypeScript |
| `[I]` | Interface | TypeScript |

## 成本控制

- **Docstring/Doxygen 优先**: 有文档的符号零 API 成本。
- **短函数跳过**: 小于 3 行且无文档的函数自动标记。
- **依赖感知增量更新**: 仅变更时重新生成。

## 故障排除

### Q: 遇到 `Fatal API Error 429: Rate limit exceeded`？
将 `OPENAI_MAX_WORKERS` 设置为 `1`（串行模式），或申请更高配额。

### Q: 遇到 `Fatal API Error 403: Forbidden`？
检查 `OPENAI_API_KEY` 是否正确，确认 `OPENAI_MODEL` 在服务中可用。

### Q: 运行中断后进度会丢失吗？
不会。`try...finally` 保护机制确保已生成的摘要被保存到 `.claude/logic_index.json`。

### Q: C/C++ 解析精度不够？
安装 `tree-sitter`（见上方安装说明）。tree-sitter 模式可处理模板、嵌套 namespace、运算符重载等复杂结构。

### Q: `.h` 文件被当作 C 解析但实际是 C++ 代码？
tree-sitter 模式下，`.h` 文件会自动检测 C++ 关键字并切换语法。正则模式下行为相同。

### Q: TypeScript/TSX 解析精度不够？
安装 `tree-sitter-typescript`（见上方安装说明）。tree-sitter 模式额外支持箭头函数、abstract class 方法和嵌套 namespace 成员提取。

### Q: 箭头函数（`export const foo = () => {}`）未被提取？
正则回退路径不支持箭头函数提取（箭头函数语法变体过多，正则边界误报率高）。安装 `tree-sitter-typescript` 后，箭头函数通过 `lexical_declaration → variable_declarator → arrow_function` 路径自动提取。
