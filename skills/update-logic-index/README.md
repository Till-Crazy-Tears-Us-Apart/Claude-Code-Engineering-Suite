# Logic Indexer (Semantic Code Index)

Logic Indexer is a semantic indexing tool based on multi-language source code parsing and an OpenAI-compatible API. It parses Python, C, C++, and TypeScript/TSX code to generate concise semantic summaries, enabling Claude Code to understand project logic without reading full source files.

## Supported Languages

| Language | Extensions | Parsing Method |
| :--- | :--- | :--- |
| Python | `.py` | Standard library `ast` module (built-in) |
| C | `.c`, `.h` | Regex (built-in) / tree-sitter (optional) |
| C++ | `.cpp`, `.hpp`, `.cc`, `.cxx`, `.hh`, `.hxx` | Regex (built-in) / tree-sitter (optional) |
| TypeScript | `.ts`, `.tsx` | Regex (built-in) / tree-sitter (optional, requires `tree-sitter-typescript`) |

`.h` files are auto-detected: if they contain C++ keywords (`class`, `namespace`, `template`, etc.), C++ parsing is used.

## Core Features

- **Multi-Language**: Pluggable `LanguageParser` architecture, auto-dispatching by file extension.
- **AST Parsing (Python)**: Identifies Class, Function, and Method structures.
- **Regex + tree-sitter Dual Path (C/C++/TypeScript)**: Zero-dependency regex mode by default; automatically switches to high-precision mode when tree-sitter is installed.
- **Cross-File Context**: Parses Python `import` and C/C++ `#include "..."` dependencies, injecting upstream module summaries into LLM prompts.
- **Incremental Updates**:
    - **File-Level Hashing**: MD5-based source content hashing.
    - **Dependency-Aware Hashing**: Upstream summary changes trigger downstream re-analysis.
    - **Usage-Aware Filtering**: Only triggers updates when referenced symbols are actually used in the current file.
- **Hybrid Summary Strategy**:
    - **Docstring/Doxygen Priority**: Auto-extracts Python docstrings and C/C++ Doxygen comments (`[Doc]` tag), zero API cost.
    - **Short Function Skip**: Functions under 3 lines without documentation are auto-tagged (configurable).
    - **LLM Semantic Enhancement**: Only invokes the LLM API for complex logic.
- **Data Flow Tracking**: Forces LLM to identify data sources `[Source]` and data sinks `[Sink]`.
- **Robustness**:
    - **Atomic Fallback**: Batch processing failure triggers automatic degradation to single-symbol mode.
    - **Truncation Recovery**: Detects API response truncation and triggers automatic retry.
    - Built-in exponential backoff, circuit breaker (auto-stop on 429/401), and checkpoint protection.

## Workflow (3 Steps)

### Step 1: Check Configuration

The skill checks for `.claude/logic_index_config`. If missing, it creates one from the default template and prompts the user to review exclusion rules before proceeding.

### Step 2: Execute Scanning

Runs the Python indexer:

```bash
python "~/.claude/skills/update-logic-index/run.py"
```

On first run (no existing `.claude/logic_tree.md`), a full codebase scan is performed.

### Step 3: Injection Strategy

Based on the `LOGIC_INDEX_AUTO_INJECT` policy:

| Policy | Behavior |
| :--- | :--- |
| `ALWAYS` (default) | Automatically injects `logic_tree.md` into `CLAUDE.md` |
| `ASK` | Prompts user for confirmation before injection |
| `NEVER` | Only generates files, no injection |

## Installing tree-sitter (Optional)

C/C++ and TypeScript/TSX parsing uses regex mode by default (zero dependencies). Install tree-sitter for higher precision:

```bash
pip install tree-sitter tree-sitter-c tree-sitter-cpp tree-sitter-typescript
```

**C/C++**:

| Feature | Regex Mode | tree-sitter Mode |
| :--- | :--- | :--- |
| Function/struct/enum/macro | Supported | Supported |
| Class methods | Supported | Supported |
| Namespace nesting | Outer only | All levels |
| Template class | Not supported | Supported |
| Operator overloading | Not supported | Supported |

**TypeScript/TSX**:

| Feature | Regex Mode | tree-sitter Mode |
| :--- | :--- | :--- |
| function/class/interface/enum/type/namespace | Supported | Supported |
| Arrow functions (`export const foo = () => {}`) | Not supported | Supported |
| Abstract class methods | Not supported | Supported |
| Nested namespace members | Not supported | Supported |
| TSX grammar (`.tsx`) | Supported (no distinction) | Separate grammar |

## Configuration

### Environment Variables (`settings.json`)

Configure in `settings.local.json` (project-level) or `~/.claude/settings.json` (global):

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OPENAI_API_KEY` | — | API key |
| `OPENAI_MODEL` | `glm-5` | Model name |
| `OPENAI_BASE_URL` | `https://coding.dashscope.aliyuncs.com/v1/chat/completions` | API endpoint |
| `OPENAI_MAX_WORKERS` | `3` | Concurrent threads |
| `OPENAI_RETRY_LIMIT` | `3` | Retry count |
| `OPENAI_TIMEOUT` | `300` | Timeout in seconds |
| `OPENAI_MAX_TOKENS` | `8192` | Response token limit |
| `LOGIC_INDEX_AUTO_INJECT` | `ALWAYS` | `ALWAYS` / `ASK` / `NEVER` |
| `LOGIC_INDEX_FILTER_SMALL` | `false` | Skip LLM summarization for small functions without docstrings |
| `REMY_LANG` | `en` | Summary output language (`en` / `zh-CN`) |

### Exclusion Rules (`.claude/logic_index_config`)

Syntax similar to `.gitignore`; `!` prefix for exclusion, supports wildcards.

```text
!tests/
!**/migrations/
!**/CMakeFiles/
!**/*.o
```

## Symbol Types

| Icon | Meaning | Languages |
| :--- | :--- | :--- |
| `[C]` | Class | Python, C++, TypeScript |
| `[f]` | Function | Python, C, C++, TypeScript |
| `[S]` | Struct | C, C++ |
| `[E]` | Enum | C, C++, TypeScript |
| `[T]` | Typedef / TypeAlias | C, C++, TypeScript |
| `[M]` | Macro | C, C++ |
| `[N]` | Namespace | C++, TypeScript |
| `[I]` | Interface | TypeScript |

## Cost Control

- **Docstring/Doxygen priority**: Symbols with documentation incur zero API cost.
- **Short function skip**: Functions under 3 lines without documentation are auto-tagged.
- **Dependency-aware incremental updates**: Only regenerates on actual changes.

## Troubleshooting

### Q: `Fatal API Error 429: Rate limit exceeded`?
Set `OPENAI_MAX_WORKERS` to `1` (serial mode), or request a higher quota.

### Q: `Fatal API Error 403: Forbidden`?
Check that `OPENAI_API_KEY` is correct and `OPENAI_MODEL` is available on the service.

### Q: Will progress be lost if interrupted?
No. The `try...finally` protection mechanism ensures generated summaries are saved to `.claude/logic_index.json`.

### Q: C/C++ parsing precision is insufficient?
Install `tree-sitter` (see installation section above). tree-sitter mode handles templates, nested namespaces, operator overloading, and other complex structures.

### Q: `.h` file parsed as C but is actually C++ code?
Both tree-sitter and regex modes auto-detect C++ keywords in `.h` files and switch syntax accordingly.

### Q: TypeScript/TSX parsing precision is insufficient?
Install `tree-sitter-typescript` (see installation section above). tree-sitter mode additionally supports arrow function extraction, abstract class methods, and nested namespace members.

### Q: Arrow functions (`export const foo = () => {}`) not extracted?
The regex fallback path does not support arrow function extraction (too many syntax variants, high false-positive rate). After installing `tree-sitter-typescript`, arrow functions are extracted via the `lexical_declaration → variable_declarator → arrow_function` AST path.
