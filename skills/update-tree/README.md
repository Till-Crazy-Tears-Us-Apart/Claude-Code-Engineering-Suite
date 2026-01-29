# Update Tree (项目树快照)

Update Tree 用于生成项目目录结构的文本快照，并将其保存至 `.claude/project_tree.md`。该快照随后被注入到 `CLAUDE.md` 中，作为 LLM 的空间导航地图。

## 核心功能

1.  **智能过滤**: 支持类似 `.gitignore` 的排除规则。
2.  **深度控制**: 支持针对不同子目录配置不同的遍历深度。
3.  **文件可见性**: 支持控制是否列出叶子节点文件，或仅显示目录结构。
4.  **自动注入**: 生成后自动触发 `hooks/doc_manager/injector.py` 更新核心文档。

## 配置文件 (`.claude/tree_config`)

该 Skill 依赖 `.claude/tree_config` 进行配置。若文件不存在，首次运行时会自动创建默认模板。

### 语法说明

*   **排除规则**: 以 `!` 开头。
    *   `!node_modules` (排除名为 node_modules 的目录或文件)
    *   `!*.log` (排除后缀为 .log 的文件)
*   **包含规则**: `[路径] [参数]`
    *   `-depth N`: 遍历深度 (N=0 表示仅当前层，N=-1 表示无限递归)。
    *   `-if_file true/false`: 是否显示具体文件。

### 配置示例

```text
# 排除项
!__pycache__
!.git
!dist

# 根目录规则：深度 2 层，显示文件
. -depth 2 -if_file true

# 特定目录规则：深度 1 层，仅显示文件夹（不显示文件）
src/assets -depth 1 -if_file false

# 源码目录：深度无限，显示文件
src/core -depth -1 -if_file true
```

## 何时使用

建议在以下场景主动运行 `/update-tree`：
1.  **文件操作后**: 执行了批量创建 (`touch`)、移动 (`mv`) 或删除 (`rm`) 操作。
2.  **重构后**: 修改了模块结构或重命名了文件夹。
3.  **上下文漂移**: 发现 LLM 开始引用不存在的文件路径时。

## 关联组件

*   `hooks/tree_system/generate_smart_tree.py`: 实际执行生成的脚本。
*   `hooks/tree_system/lifecycle_hook.py`: 在 SessionStart 和 SessionEnd 时自动调用此逻辑。
