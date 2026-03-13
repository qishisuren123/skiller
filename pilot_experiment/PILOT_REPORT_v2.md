# Pilot Experiment v2 Report — When Skills Fail

**实验时间**: 2026-03-10
**总花费**: $15.86 / $200 预算 (7.9%)
**API 调用**: 252 次
**模型**: 6 个（Haiku, GPT-4o-mini, GPT-4.1-mini, Gemini-Flash, Sonnet, Opus）
**场景**: 10 个科学数据处理任务

---

## 1. 实验设计

### 1.1 模型分级

| 级别 | 模型 | 厂商 |
|------|------|------|
| 弱 | Haiku (Claude 3.5) | Anthropic |
| 弱 | GPT-4o-mini | OpenAI |
| 弱 | GPT-4.1-mini | OpenAI |
| 弱 | Gemini-2.5-Flash | Google |
| 中 | Sonnet (Claude 4) | Anthropic |
| 强 | Opus (Claude 4) | Anthropic |

### 1.2 场景 (S01-S10)

| ID | 领域 | 难度 | 描述 | 测试项 |
|----|------|------|------|--------|
| S01 | 神经科学 | easy | HDF5/MAT 元数据扫描 | 9 |
| S02 | 神经科学 | hard | 多格式 spike+behavior 标准化 | 9 |
| S03 | 生命科学 | medium | 空间转录组归一化 | 8 |
| S04 | 地球科学 | medium | 卫星 NetCDF 重网格化 | 7 |
| S05 | 生命科学 | medium | 蛋白质 JSON 解析 | 8 |
| S06 | 生命科学 | hard | 基因表达标准化 | 6 |
| S07 | 神经科学 | easy | 神经数据可视化 | 4 |
| S08 | 材料科学 | medium | QA 数据清洗 | 7 |
| S09 | 地球科学 | easy | 多站观测合并 | 6 |
| S10 | 生命科学 | hard | 多模态数据索引 | 6 |

### 1.3 评估体系

4 层执行验证（非关键词匹配）：
- **L1 Execution**: 代码能否运行（returncode=0, 输出文件存在）
- **L2 Functional**: 输出是否正确（数据范围、列名、格式验证）
- **L3 LLM-Judge**: 代码质量评分（未在本轮实施）
- **L4 Code Metrics**: 行数、try/except 计数、防御性比率

---

## 2. 核心发现

### Finding 1: The Skill Paradox — 弱模型既是最大受益者也是最大受害者

**主实验结果矩阵**（no_skill → exact_skill, Δ 百分点）：

| 模型 | S01 | S02 | S03 | S04 | S05 | S06 | S07 | S08 | S09 | S10 | 平均Δ |
|------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-------|
| haiku | 0 | 0 | +12 | 0 | 0 | 0 | 0 | **-100** | 0 | 0 | -8.8 |
| gpt4o_mini | 0 | +56 | +12 | -14 | +100 | +100 | +100 | +100 | **-83** | 0 | +37.0 |
| gpt41_mini | 0 | 0 | +38 | **-100** | +100 | 0 | 0 | 0 | **-100** | +83 | +2.1 |
| gemini_flash | +100 | 0 | 0 | 0 | +100 | +100 | 0 | +100 | 0 | +100 | +50.0 |
| **sonnet** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0** | **0.0** |
| **opus** | **0** | **0** | **0** | — | **0** | — | — | **0** | **0** | — | **0.0** |

**关键观察**：
- 每个弱模型都有 skill 帮助的场景（高达 +100pp）和被 skill 伤害的场景（低至 -100pp）
- **不同弱模型被不同场景的 skill 伤害**：Haiku→S08, GPT-4o-mini→S09, GPT-4.1-mini→S04+S09
- Sonnet 和 Opus **完全不受 skill 影响**——既不帮忙也不添乱

---

### Finding 2: 失败根因分析 — 四种 Skill 毒性机制

| 编号 | 机制 | 实例 | 根因 |
|------|------|------|------|
| T1 | **适配错误** | Haiku S08: 100%→0% | Skill 的参考代码模式导致 Haiku 在重写时引入 typo (`enumerate(1, start=1)` 代替 `enumerate(f, start=1)`) |
| T2 | **陈旧 API** | GPT-4o-mini S09: 100%→17% | Skill 参考代码使用已废弃的 pandas API (`infer_datetime_format`, `fillna(method=)`)，弱模型无批判性复制 |
| T3 | **危险默认值** | Sonnet S02 + Opus skill: 100%→0% | Opus skill 推荐 `squeeze_me=True`（非默认），Sonnet 遵循后写了不兼容的验证逻辑 |
| T4 | **库依赖** | GPT-4o-mini S08 no_skill: 0% | 模型自发使用 `import jsonlines`（测试环境未安装），skill 纠正为 stdlib `json.loads(line)` |

**T1-T3 是 skill 引入的伤害，T4 是 skill 修复的问题。** 关键区别：T4 的 "伤害" 来自模型本身的不良习惯，skill 通过提供标准模式来修复。

---

### Finding 3: Exact-match Skill 比 Near-miss Skill 更危险

**S08 Haiku 实验**：

| 条件 | Haiku 得分 | 含义 |
|------|-----------|------|
| no_skill | 7/7 (100%) | 基线 |
| exact_skill (Sonnet 写) | **0/7 (0%)** | 精确匹配 skill 导致失败 |
| nearmiss (S09 的 skill) | **7/7 (100%)** | 错误场景的 skill 无害 |

**解释**：精确匹配的 skill 足够接近任务，模型会认真尝试遵循它的代码模式，从而引入适配错误。而不相关的 skill 被模型忽略，等同于 no_skill。

**这推翻了 "near-miss skill 最危险" 的假设**——精确匹配反而更危险。

---

### Finding 4: 强模型对 Poison 最敏感

**S09 Poison 实验**（在 skill 末尾注入错误建议："永远将数值转为字符串"、"for 循环比 numpy 快"）：

| 模型 | clean skill | poisoned skill | Δ |
|------|-------------|---------------|---|
| Haiku | 6/6 | 5/6 | -1 |
| Sonnet | 5/6 | 5/6 | 0 |
| **Opus** | **5/6** | **0/6** | **-5** |

**Opus 是最受 poison 影响的模型！** 反直觉——最强模型最容易被恶意指令欺骗。可能原因：
- Opus 具有更强的指令遵循能力（instruction following），因此更倾向于执行 skill 中的每一条建议
- Haiku 受限于能力，无法完全实现 poison 中的建议，反而"意外安全"
- Sonnet 介于两者之间

---

### Finding 5: 跨模型 Skill 毒性 — 作者特异性

**S08 Cross-model 实验（使用者 = Haiku）**：

| Skill 作者 | Haiku 得分 |
|-----------|-----------|
| 无 skill | 7/7 (100%) |
| **Haiku 写的** | **7/7 (100%)** |
| **Sonnet 写的** | **0/7 (0%)** |
| **Opus 写的** | **7/7 (100%)** |

**S02 Cross-model 实验（使用者 = Sonnet）**：

| Skill 作者 | Sonnet 得分 |
|-----------|------------|
| 无 skill | 9/9 (100%) |
| Haiku 写的 | 9/9 (100%) |
| Sonnet 写的 | 9/9 (100%) |
| **Opus 写的** | **0/9 (0%)** |

**模式**：
1. 同级或低级模型写的 skill 通常安全
2. **特定高级模型写的 skill 可能含有"专家级"API 选择**（如 `squeeze_me=True`），低级模型遵循但无法处理下游后果
3. 不是所有高级 skill 都有害——只有包含非默认 API 选择的才危险

---

### Finding 6: 消融实验 — Skill 的毒性成分可被"中和"

**S09 Haiku 消融**：

| 条件 | 得分 |
|------|------|
| no_skill | 6/6 |
| full_skill | 6/6 |
| overview_only | 5/6 |
| **first_half** | **0/6** |
| second_half | 6/6 |

**first_half 是毒性来源**（包含参考代码中的废弃 API），但 **full_skill 是安全的**——second_half 中的额外上下文"中和"了 first_half 的毒性。这意味着 **部分 skill 可能比完整 skill 更危险**。

---

## 3. Gemini Flash 的独特问题

Gemini Flash 有一个其他模型不存在的问题：**NO CODE** — 它经常不输出可解析的代码块。

| 场景 | no_skill | exact_skill |
|------|----------|-------------|
| S01 | 0/9 (code: 2L) | 9/9 (133L) |
| S02 | 0/9 (code: 12L) | NO CODE |
| S04 | NO CODE | 0/7 (146L) |
| S05 | NO CODE | 8/8 (151L) |
| S08 | NO CODE | 7/7 (138L) |
| S10 | 0/6 (code: 5L) | 6/6 (173L) |

无 skill 时，Gemini Flash 经常只输出几行代码或根本不输出代码块。Skill 帮助它生成完整的解决方案。

---

## 4. 代码度量分析

**Skill 对代码结构的影响（Haiku 平均值）**：

| 指标 | no_skill | exact_skill | 变化 |
|------|----------|-------------|------|
| 非空行数 | 283 | 287 | +1.4% |
| try/except | 3.6 | 4.6 | +28% |
| 防御性比率 | 0.48 | 0.63 | +31% |

**Skill 增加防御性编码**（更多 try/except），这在某些场景下有益但在其他场景下导致过度复杂化。

---

## 5. 论文方向建议

### 核心叙事

**"Skills as Double-Edged Swords: How Knowledge Transfer Fails in LLM Code Generation"**

### 六个可投稿的发现

1. **The Skill Paradox**: 弱模型同时是 skill 的最大受益者和最大受害者（Finding 1）
2. **Four Toxicity Mechanisms**: 适配错误、陈旧 API、危险默认值、库依赖（Finding 2）
3. **Exact > Near-miss Danger**: 精确匹配的 skill 比错误场景的 skill 更危险（Finding 3）
4. **Poison Paradox**: 最强模型对恶意注入最敏感（Finding 4）
5. **Author-Specificity**: Skill 毒性取决于作者-使用者的特定组合（Finding 5）
6. **Partial Skill Danger**: 部分 skill 可能比完整 skill 更危险（Finding 6）

### 与现有工作的区分

| 方面 | 现有工作 | 本文 |
|------|---------|------|
| 焦点 | Skill/RAG 帮助多少 | **Skill 什么时候伤害** |
| 评估 | 关键词匹配 | **执行验证** |
| 模型 | 单厂商 | **跨厂商 6 模型** |
| 发现 | "弱模型获益更多" | **弱模型同时受害最多 + 强模型对 poison 最敏感** |

### EMNLP 2026 投稿可行性

**优势**：
- 反直觉发现丰富，故事感强
- 跨厂商验证（不是单一模型的 artifact）
- 实用指导价值高（如何安全地使用 skill）
- 实验设计可扩展到 30+ 场景

**需要补充**：
- 扩大场景覆盖（30 个场景）
- 添加更多模型（GPT-4o, GPT-4.1 full, Gemini Pro）
- 统计显著性测试（每个条件重复 3-5 次）
- LLM-as-Judge 评分（Layer 3）
- 更细粒度的消融（逐段落消融、代码块 vs 文字部分）

### 预算估算

| 阶段 | 预计花费 |
|------|---------|
| 本次 pilot | $15.86 (已花) |
| 扩展主实验 (30 场景 × 9 模型) | ~$80 |
| 消融实验 (10 场景 × 5 条件 × 4 模型) | ~$30 |
| 跨模型实验 (10 场景 × 9 组合) | ~$40 |
| Poison 实验 (10 场景 × 3 poison × 6 模型) | ~$25 |
| 重复验证 (关键发现 × 3 次) | ~$10 |
| **总计** | **~$200** |

---

## 附录 A: 实验配置

```python
API_RELAY = "${ANTHROPIC_BASE_URL}"
TEMPERATURE = 0
MAX_TOKENS = 8192
SKILL_AUTHOR = "Sonnet" (主实验)
CONDA_ENV = "pilot_exp" (Python 3.12)
```

## 附录 B: 详细结果数据

所有原始数据保存在 `results/raw/` 目录下，格式为 `{scenario}__{condition}__{model}.json`。
评估结果汇总在 `results/v2_all_main.json`。
