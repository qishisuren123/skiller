# 进展汇报（一）：skill-metric 评分工具开发与 v4 关键修复

## 总览

在 v2 版本完成多文件输出结构并在 3 个测试场景上自评达到 24/24 满分后，我开发了一个独立的**自动化评分工具 skill-metric**（756 行 Python），用于客观评估 skill 的结构质量。使用该工具实际打分后发现 v2/v3 生成的 skill 只能得到 21-22/24 分，存在两个隐性 bug。v4 版本针对性修复后，在 skill-metric 实测中真正达到了 24/24 满分。

---

## 一、为什么需要 skill-metric

v2 的自评流程依赖 Claude 自身理解评分标准（rank_skill.docx 中的 24 条规则），但存在两个问题：

1. **主观偏差**：Claude 倾向于对自己生成的内容给高分，缺乏客观检验
2. **规则理解偏差**：部分规则涉及文件存在性检查、字符数统计、关键词匹配等，纯靠 LLM 自评无法精确验证

因此我开发了一个**确定性评分脚本**，对 24 条规则逐一用代码检查，不依赖 LLM 判断。

## 二、skill-metric 评分工具

### 工具定位

| 属性 | 说明 |
|------|------|
| 位置 | `projects/10day/skill-metric/skill-metric/` |
| 代码量 | `scripts/skill_quality_eval.py`，756 行 Python |
| 依赖 | **零外部依赖**（YAML 用正则手动解析，不依赖 PyYAML） |
| 输出格式 | 文本报告 / JSON / CSV / 雷达图 (matplotlib) |
| 批量能力 | 支持多 skill 路径，`--csv` 输出对比表 |

### 评分维度（满分 24 分）

**2.1.1 格式审查（满分 8 分，每项不满足扣 1 分）**：

| 检查项 | 检查逻辑 |
|--------|---------|
| SKILL.md 存在且命名正确 | `os.path.exists()` + 大小写完全匹配 |
| 目录名 kebab-case | 正则 `^[a-z0-9]+(-[a-z0-9]+)*$` |
| 目录内无 README.md | 文件存在性检查 |
| YAML frontmatter 存在 | 检测 `---` 分隔符 |
| `name` 与目录名一致 | 字符串精确匹配 |
| `description` 字段存在 | YAML 解析后检查 |
| `description` < 1024 字符 | `len()` 检查 |
| `description` 无 XML 标签 | 正则匹配 `<[a-zA-Z]` |

**2.1.2 内容完整性（基础 0 分，每项满足加 1 分）**：

| 检查项 | 检查逻辑 |
|--------|---------|
| `license` 字段 | YAML 解析 |
| `compatibility` 字段（≤500 字符） | YAML 解析 + `len()` |
| `metadata` 字段（含 author/version） | 嵌套字段检查 |
| `scripts/` 子目录 | `os.path.isdir()` + 至少 1 个文件 |
| `references/` 子目录 | 同上 |
| `assets/` 子目录 | 同上 |
| 正文有具体案例 | 检测代码块 `` ``` `` |
| 正文有错误处理 | 同时包含 "error/exception" **和** "handle/troubleshoot" |

**2.1.3 写作质量（基础 0 分，每项满足加 1 分）**：

| 检查项 | 检查逻辑 |
|--------|---------|
| description 有明确任务边界 | 长度 ≥40 字符 + 包含动词/名词对 |
| description 有触发信号 | 包含 "use this skill when" 或 "use when" |
| 渐进式信息披露 | body ≤ 5000 字符 + 存在 references/ 或 scripts/ |
| 内容以英文为主 | ASCII 字符占比 ≥ 70% |
| 引用一致性 | body 中引用的 scripts/references/ 文件真实存在 |
| 反向一致性 | 若目录存在，body 至少引用其中 1 个文件 |
| license 非占位值 | 不是 "Unknown" / "TBD" / "N/A" |
| 版本信息 | frontmatter 或 body 中包含版本号 |

### 关键技术决策

**为什么不用 PyYAML 解析 frontmatter？**

因为 v2/v3 使用了 YAML block scalar 语法（`description: >-`），PyYAML 能正确解析但我们的 SKILL.md 是给 Claude 读的，而 Claude 的内部解析器（类似简易正则）**不支持** block scalar。为了让评分工具的行为与 Claude 实际读取行为一致，我选择用正则模拟 Claude 的解析方式——这正是发现 bug 的关键。

## 三、v2/v3 的隐性 bug

使用 skill-metric 对 v2 生成的 3 个满分 skill 重新打分后发现：

| Skill | 自评分 | 实测分 | 差距 | 原因 |
|-------|--------|--------|------|------|
| neuro-metadata-gen (v2) | 24/24 | 22/24 | -2 | YAML `>-` + 缺 error handling 关键词 |
| spike-behavior-organize (v2) | 24/24 | 21/24 | -3 | YAML `>-` + 缺关键词 + body 略超 5k |
| requirement-to-skill (v3) | 24/24 | 23/24 | -1 | 文件名含连字符导致 glob 匹配失败 |

### Bug 1：YAML block scalar 解析不兼容（-2 分）

```yaml
# v2/v3 写法（问题写法）
description: >-
  Recursively scan neuroscience data directories...
  Use this skill when the user needs to catalog...

# skill-metric 读到的：">-"（2 个字符）
# 结果：task boundary 检查失败（<40 字符）、trigger 检查失败（找不到 "use when"）
```

**根因**：`>-` 是 YAML 的 block scalar 语法，会把多行折叠成一行。但 skill-metric 的简易解析器只读 `description:` 后面同一行的内容，遇到 `>-` 就把整个值解析为字面量 `">-"`。

### Bug 2：缺少 error handling 关键词（-1 分）

v2 模板中有 `## Common Pitfalls` 段落，里面详细描述了各种错误和修复方法，但用的措辞是 "Pitfall" 和 "Fix"，**没有包含** skill-metric 要求的关键词组合：

- 必须同时出现 `error` 或 `exception`
- **和** `handle` 或 `troubleshoot`

"Pitfall" + "Fix" 在语义上等价，但 skill-metric 做的是关键词匹配，不是语义理解。

### Bug 3：文件名连字符导致引用检查失败（-1 分，skill-metric 自身 bug）

`references/conversation-design.md` 这个文件名在 body 中被引用后，skill-metric 的 `_extract_refs_to_refs_or_scripts()` 函数用 `re.escape(name)` 转义后传给 `glob()`，但 `re.escape` 把 `-` 转义成 `\-`，导致 glob 找不到文件。

**规避方法**：skill 内部文件名用下划线代替连字符（`conversation_design.md`）。

## 四、v4 修复方案

| 修复项 | 改动 | 影响文件 |
|--------|------|---------|
| YAML 单行化 | `description` 和 `compatibility` 改为单行双引号字符串，**禁止** `>`, `>-`, `\|`, `\|-` | SKILL.md 模板、generate_skill.py 系统 prompt |
| Error Handling 模板化 | 在 SKILL.md body 模板中**强制包含** `## Error Handling` 段落，要求使用 "error" + "handle" 措辞 | SKILL.md 模板、quality-checklist.md |
| 质量检查清单 | 增加 YAML 解析器兼容性警告，标注每个 check 的具体关键词要求 | quality-checklist.md |
| 生成器模板 | 系统 prompt 中的示例改为单行 description | generate_skill.py |

修复后重新打分：

```
$ python3 skill_quality_eval.py neuro-metadata-gen/ -j
{
  "format_score": 8,
  "completeness_score": 8,
  "writing_score": 8,
  "total_score": 24    ← 真正的 24/24
}
```

## 五、关键发现

1. **自评 ≠ 实测**：LLM 自评容易忽略实现层面的兼容性问题，必须有确定性工具验证
2. **YAML 解析器差异是隐性陷阱**：同一个 YAML 文件在 PyYAML、Claude 内部解析器、简易正则解析器中可能得到不同结果，生成器必须用最保守的语法（单行引号）
3. **关键词匹配 vs 语义理解**：评分标准中的 "error handling" 检查是基于关键词的，skill 必须使用标准措辞而非语义等价词

---

## TODO

- 将 skill-metric 工具发布为独立 skill 包，方便其他项目复用
- 考虑在 skill-metric 中增加语义理解层（而非纯关键词匹配），减少误判
- 在 generate_skill.py 中集成自动打分环节，生成后立即验证，未满分则自动修复重试
