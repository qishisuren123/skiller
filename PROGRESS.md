# PROGRESS.md — v4 迭代记录

## 问题诊断

v2/v3 生成的 skill 自评 24/24 满分，但用 `skill-metric` 实际打分只得 21-22/24。根本原因：
1. **YAML 解析器不支持多行 `>-`**：skill-metric 的简易解析器把 `description: >-` 读为 `">-"`（2 字符），导致 task boundary 和 trigger 检查失败（-2 分）
2. **缺少 error handling 关键词**：部分 skill 的 body 缺少 "error/exception" + "handle/troubleshoot" 关键词组合（-1 分）

## v4 核心改进

1. **YAML 单行化**：`description` 和 `compatibility` 改为单行双引号字符串，禁止 `>`, `>-`, `|`, `|-`
2. **Error Handling 模板化**：在 SKILL.md body 模板中强制包含 `## Error Handling` 段落
3. **质量检查清单更新**：增加 YAML 解析器兼容性警告，标注每个 check 的具体关键词要求
4. **生成器模板修改**：`generate_skill.py` 系统 prompt 中的示例改为单行 description，增加显式指令

## v4 改动文件

| 文件 | 改动内容 |
|------|---------|
| `conversation-to-skill/SKILL.md` | description/compatibility 改为单行引号；增加 Error Handling 段落 |
| `conversation-to-skill/references/skill-template.md` | 增加 YAML Parser Compatibility Notes 段落 |
| `conversation-to-skill/references/manual-workflow.md` | Step 5 增加 YAML 格式兼容性规则 |
| `conversation-to-skill/references/quality-checklist.md` | 增加 YAML 解析器兼容性警告 |
| `conversation-to-skill/scripts/generate_skill.py` | 系统 prompt 模板改为单行 description |

## 生成的 2 个神经科学 skill

### Skill 1: `neuro-metadata-gen`
- **来源**: `conversations/01_neuro_metadata_gen.json`（14 轮）
- **功能**: 递归扫描 HDF5/MAT 目录，提取内部结构元数据，生成 meta.json
- **核心特性**: MAT v7.3 自动 fallback、大文件深度限制、通配符模式合并、灵活 shape 比较

### Skill 2: `spike-behavior-organize`
- **来源**: `conversations/06_spike_behavior_organize.json`（20 轮）
- **功能**: 多格式神经 spike/behavior 数据标准化为统一 trial-based HDF5
- **核心特性**: XDS struct 解包、NWB VectorIndex spike 提取、时间重采样、运动学统一、质量标记

## 评分结果

| Skill | Format (8) | Completeness (8) | Writing (8) | Total |
|-------|-----------|------------------|-------------|-------|
| neuro-metadata-gen | **8/8** | **8/8** | **8/8** | **24/24** |
| spike-behavior-organize | **8/8** | **8/8** | **8/8** | **24/24** |
| requirement-to-skill | **8/8** | **8/8** | **8/8** | **24/24** |

## 代码可用性测试

| 测试项 | neuro-metadata-gen | spike-behavior-organize |
|--------|-------------------|------------------------|
| `--help` 运行 | ✓ 通过 | ✓ 通过 |
| 合成数据端到端 | ✓ 通过（6 files → 2 merged entries） | ✓ 通过（50 bins × 10 units → HDF5 验证通过） |

## 关键修复验证
- ✅ description 被 skill-metric 正确读取为完整文本（非 ">-"）
- ✅ task boundary 检查通过（description >= 40 字符且内容具体）
- ✅ trigger 检查通过（description 包含 "Use this skill when..."）
- ✅ error handling 检查通过（body 包含 error + handle 关键词组合）

## Skill 3: `requirement-to-skill`（元技能）

- **来源**: 无对话文件，从工作流经验总结而成
- **功能**: 将纯文本需求描述转化为完整 skill 包的元工作流
- **5 阶段**: 需求分析 → 对话构造 → skill 提取 → 打分验证 → 代码测试
- **4 个子命令**: `scaffold`（创建骨架）、`analyze`（生成分析模板）、`validate`（运行 skill-metric）、`test`（代码可用性测试）
- **评分**: **24/24**（首次 23/24，修复：重命名 `conversation-design.md` → `conversation_design.md` 避免 `re.escape` 转义 `-` 导致 glob 失败；改写 body 避免外部工具路径被误识别为 `scripts/` 引用）
- **代码测试**: `--help` 通过，4 个子命令全部正常运行

### 额外发现的 skill-metric bug
- `_extract_refs_to_refs_or_scripts()` 使用 `re.escape(name)` 后传给 `glob()`，但 `re.escape` 会转义 `-` 为 `\-`，导致含 `-` 的文件名（如 `conversation-design.md`）无法被 glob 匹配。**规避方法**：skill 内部文件名用下划线代替连字符。

## 三系统对比实验（2026-03-07）

对同一任务（question.csv #1 神经科学数据元数据生成），对比三个 skill 生成系统的输出质量。

### 静态评分

| 系统 | Format | Completeness | Writing | Total |
|------|--------|-------------|---------|-------|
| A: conversation-to-skill | 8 | 8 | 8 | **24/24** |
| B: requirement-to-skill | 8 | 8 | 8 | **24/24** |
| C: 官方 skill-creator | 8 | 5 | 6 | **19/24** |

System C 扣分原因：缺少 license/compatibility/metadata 字段 + description 无触发语句。这是设计哲学差异而非质量问题。

### 实用性测试（7 项断言 × 3 场景）

| 系统 | 通过率 |
|------|--------|
| System A | **21/21 (100%)** |
| System B | **21/21 (100%)** |
| System C | **21/21 (100%)** |
| Baseline (无技能) | **9/21 (43%)** |

三个系统功能等价，技能比无技能提升 57 个百分点。

### 加权总分

| 系统 | 总分 (/20) |
|------|-----------|
| A: conversation-to-skill | **16.95** |
| B: requirement-to-skill | **16.70** |
| C: 官方 skill-creator | **15.15** |

完整报告：`comparison_test/COMPARISON_REPORT.md`

## 过程文档

- `generated_skills/GENERATION_PROCESS.md`：记录两个神经科学 skill 的完整生成过程（对话来源、轮次注释、遇到的问题、实际运行输出）
- `comparison_test/COMPARISON_REPORT.md`：三系统对比完整报告

## 版本对比

| 版本 | 评分 | 关键改进 |
|------|------|---------|
| v1 | ~10/24 | 初版，单文件输出，无 frontmatter |
| v2 | 24/24（自评） | 多文件结构、frontmatter、渐进式信息披露 |
| v3 | 24/24（自评） | 对话扩充、质量检查清单 |
| v4 | **24/24（skill-metric 实测）** | 修复 YAML 解析兼容性、error handling 关键词、代码可用性验证 |

---

## Pilot Experiment v2: Skill Effect on Code Generation（2026-03-10）

### 实验设计
- **10 个场景**（S01-S10），覆盖神经科学、生命科学、地球科学、材料科学
- **6 个模型**：弱(haiku, gpt4o_mini, gpt41_mini, gemini_flash) + 中(sonnet) + 强(opus)
- **条件**：no_skill vs exact_skill (Sonnet 生成)
- **4 层评估**：L1 执行、L2 功能正确性、L3 LLM-as-Judge、L4 代码指标

### 核心发现 1: Skill Paradox — 弱模型在不同场景上被不同 skill 伤害

| 模型 | Skill 伤害场景 | Δ | Skill 帮助场景 |
|------|--------------|---|--------------|
| haiku | S08_materials_qa | -100pp | S03 (+12pp) |
| gpt4o_mini | S04_satellite (-14pp), S09_earth_obs | -83pp | S02,S05,S06,S07,S08 (+56-100pp) |
| gpt41_mini | S04_satellite (-100pp), S09_earth_obs | -100pp | S03,S05,S10 (+38-100pp) |
| gemini_flash | 无明显伤害 | — | S01,S05,S06,S08,S10 (+100pp) |
| sonnet | 无（全部 100%） | 0 | — |
| opus | 无（全部 100%） | 0 | — |

### 核心发现 2: 失败根因分析

**S08 Haiku Paradox (100% → 0%)**:
- 无 skill 时 Haiku 写出干净正确的 stdlib 代码
- 有 skill 时 Haiku 试图适配参考代码模式，引入致命 typo: `enumerate(1, start=1)` 代替 `enumerate(f, start=1)`
- **机制**: Skill 增加认知负荷，超过弱模型的可靠适配阈值

**S09 GPT-4o-mini Paradox (100% → 17%)**:
- Skill 的参考代码使用已废弃的 pandas API (`infer_datetime_format=True`, `fillna(method='ffill')`)
- GPT-4o-mini 几乎逐字复制 skill 代码，继承了废弃 API
- **机制**: Skill 中的陈旧代码模式被弱模型无批判性复制

**S08 GPT-4o-mini 反转 (0% → 100%)**:
- 无 skill 时用 `import jsonlines`（测试环境未安装）
- 有 skill 时学会用 `json.loads(line)` 标准库方式
- **机制**: Skill 提供正确的标准库模式，替代不可用的第三方库

### 核心发现 3: 强模型完全免疫
- **Sonnet**: 10/10 场景 100%（仅 S09 为 83%），skill 无任何影响
- **Opus**: 6/6 测试场景全部 100%，skill 完全无影响
- 中强模型不依赖 skill 且不被 skill 干扰

### 核心发现 4: Exact-match Skill 比 Near-miss 更危险
- Haiku S08: exact_skill = 0/7, nearmiss (S09 skill) = 7/7
- 精确匹配的 skill 改变模型行为引入适配错误，不相关 skill 被忽略

### 核心发现 5: 强模型对 Poison 最敏感
- S09 Poison 实验: Opus 5/6 → **0/6**, Sonnet 5/6 → 5/6, Haiku 6/6 → 5/6
- 最强模型的指令遵循能力反而成为弱点

### 核心发现 6: 跨模型毒性 — 作者特异性
- S08: Haiku + Sonnet-authored = 0/7, Haiku + Haiku/Opus-authored = 7/7
- S02: Sonnet + Opus-authored = 0/9, Sonnet + 其他 = 9/9
- Opus skill 用 `squeeze_me=True`（非默认），Sonnet 遵循但写出不兼容的验证逻辑

### 核心发现 7: 部分 Skill 比完整 Skill 更危险
- S09 Haiku: full_skill = 6/6, first_half = **0/6**, second_half = 6/6
- 含毒性代码的前半段被后半段的上下文"中和"

### 成本
- 总花费 $15.86 / $200 预算 (7.9%), 252 次 API 调用
- 完整报告: `pilot_experiment/PILOT_REPORT_v2.md`

### 下一步
- 扩展到 30 个场景 + 9 个模型
- 添加重复实验验证统计显著性
- 实现 LLM-as-Judge (Layer 3)
- 更细粒度的消融（逐段落、代码 vs 文字）

---

## CSV 需求批量 Skill 生成（2026-03-11）

### 来源
从 `pilot_experiment/科学数据处理需求整理_数据表_表格.csv`（28条需求）中筛选合理需求。

### 筛选标准
- **具体**: 有明确输入格式、输出格式、处理步骤
- **可实现**: 可作为独立 Python 工具
- **非重复**: 不与已有 skill（neuro-metadata-gen, spike-behavior-organize）重复
- **排除**: #24-#28 Researcher H的蛋白质系列（已在其他地方实现）

### 筛选结果：12 条合理 / 28 条总计
不合理原因分布：太笼统(7)、已有(2)、非数据处理(1)、已实现(5)、边界(3)

### 生成的 5 个 Skill

使用 requirement-to-skill pipeline（Phase2: 模拟对话 → Phase3: 提取skill）, Sonnet 模型。

| # | Skill | 提交人 | 领域 | 质量评分 | 语法 | 花费 |
|---|-------|--------|------|---------|------|------|
| 3 | spatial-transcriptomics-preprocess | Researcher C | 生命科学 | **24/24** | ✓ | $0.30 |
| 11 | swissprot-protein-parser | Researcher D | 生命科学 | **24/24** | ✓ | $0.30 |
| 13 | proteomics-enrichment-analysis | Researcher E | 生命科学 | **24/24** | ✓ | $0.31 |
| 15 | pride-proteomics-downloader | Researcher F | 生命科学 | **24/24** | ✓ | $0.30 |
| 17 | fits-aperture-photometry | Researcher G | 天文科学 | **24/24** | ✓ | $0.32 |

总花费: **$1.52**

### 生成细节

| Skill | main.py行数 | SKILL.md大小 | Pitfalls数 | 依赖包 |
|-------|-----------|------------|-----------|--------|
| spatial-transcriptomics-preprocess | 225 行 | 4.0 KB | 6 个 | scanpy, anndata, STAGATE_pyG |
| swissprot-protein-parser | 301 行 | 4.2 KB | 6 个 | pandas, numpy, json |
| proteomics-enrichment-analysis | 330 行 | 4.5 KB | 5 个 | scipy, pandas, matplotlib, requests |
| pride-proteomics-downloader | 288 行 | 3.4 KB | 6 个 | requests, pandas, tqdm |
| fits-aperture-photometry | 353 行 | 4.7 KB | 6 个 | astropy, photutils, sep |

### 修复记录
- **初始评分 23/24**: SKILL.md 缺少代码片段（`has_code_snippet` 检查需 `text.count("```") >= 2`）
- **修复**: 为每个 SKILL.md 添加 Quick Reference 段落（含 bash 用法和核心 Python 代码模式）
- **修复后**: 全部 **24/24**

### 工具
- `generated_skills/generate_from_csv.py`: 完整的 CSV→Skill 生成脚本
- `generated_skills/csv_generation_report.json`: 生成结果 JSON 报告

### 运行时测试（修复后）

| Skill | --help | 端到端测试 | 发现并修复的bug |
|-------|--------|----------|---------------|
| spatial-transcriptomics-preprocess | ✓ | ✓ (200spots→QC→HVG→PCA→UMAP→Leiden→h5ad+PNG) | 3个: var_names_unique方法名; raw层维度不匹配; scanpy绘图API兼容 |
| swissprot-protein-parser | ✓ | ✓ (3蛋白→CSV含ID/名称/功能/GO/定位/序列) | 0个 |
| proteomics-enrichment-analysis | ✓ | ✓ (50蛋白→t-test→BH校正→差异蛋白结果) | 0个 |
| pride-proteomics-downloader | ✓ | ✓ (PRIDE API搜索10项目→逐一检查) | 1个: v1→v2 API endpoint和响应格式 |
| fits-aperture-photometry | ✓ | ✓ (3星×4孔径→12条测量含星等+误差) | 2个: positions格式; astropy Quantity转float |

### 发现的LLM生成代码典型bug模式
1. **API版本过时**: 代码用已废弃的endpoint（PRIDE v1、scanpy旧API）
2. **格式假设过强**: 只支持特定10X格式不支持h5ad
3. **类型不兼容**: astropy Quantity vs pandas, photutils positions格式

### GitHub Demo
- **仓库**: https://github.com/qishisuren123/scientific-skill-demo
- 包含5个匿名化后的skill包 + README说明
- 已验证无个人信息泄露

---

## Skill-Double-Edge 开源仓库（2026-03-12）

### 仓库
- **GitHub**: https://github.com/qishisuren123/skill-double-edge
- **本地路径**: `skill-bench/`
- **原名 skill-bench，已改名为 skill-double-edge**（避免与 milesgoscha/skillbench 冲突）

### 合并的内容（v2 更新）
- **README.md**: "七个悖论" 框架，英文+中文折叠摘要
- **MANIFEST.md**: 数据集卡片，覆盖度表，复现协议
- **run_benchmark.py**: 完整复现 CLI（--dry-run 验证为 1620 trials）
- **docs/deep_dive_paradoxes.md**: 七个悖论深度分析
- **docs/reports/**: pilot_report_v2 + comparison_report
- **docs/blog_zh.md**: 中文博客
- **data/**: 1620 条实验结果 CSV + 场景元数据
- **figures/**: 4 张核心图表
- **scenarios/**: 10 个示例场景（含测试套件）
- **skills/**: 8 个示例技能包（5 实验 + 3 生成展示）
- **tools/**: 2 个技能生成器（conversation-to-skill + requirement-to-skill）
- **analysis/**: 图表生成 + 统计汇总 + 数据导出

### 安全检查
- ✅ 无 API key（config.py 被 .gitignore 排除）
- ✅ 无 cost_log.jsonl
- ✅ CSV 中无 cost_usd、stdout/stderr 等敏感字段
- ✅ Remote URL 已移除 token
