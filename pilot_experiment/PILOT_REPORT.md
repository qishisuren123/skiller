# Pilot Experiment Report — The Skill Paradox

**实验时间**: 2026-03-10
**总花费**: $7.03 / $200 预算
**API 调用**: ~30 次

---

## 实验设计

### 场景
| 场景 | 复杂度 | 描述 | 测试项 |
|------|--------|------|--------|
| neuro_metadata | 简单 | 递归扫描 HDF5/MAT 生成 meta.json | 9 项（import, argparse, 运行, JSON 输出, summary, 文件列表, 嵌套 key, MAT 处理） |
| spike_behavior | 复杂 | 多格式 spike+behavior 标准化为 trial-based HDF5 | 9 项（import, argparse, binning, filtering, HDF5 write, QC, struct 解包, 重采样, e2e） |

### 模型
- **Haiku** (claude-haiku-4-5): 弱模型
- **Sonnet** (claude-sonnet-4): 中等模型
- **Opus** (claude-opus-4): 强模型

### 条件
- **no_skill**: 不给任何 skill，直接给任务描述
- **exact_skill**: 给完全匹配的 skill（SKILL.md + workflow + pitfalls + 参考代码）
- **nearmiss_skill**: 给另一个场景的 skill（互换）
- **消融**: skillmd_only, only_pitfalls, only_code, only_workflow, etc.
- **跨模型**: Haiku 生成的 skill vs Opus 生成的 skill

---

## 核心发现

### Finding 1: The Skill Paradox — 弱模型既是最大赢家也是最大输家

**neuro_metadata (简单任务):**

| Model | No Skill | Exact Skill | Δ |
|-------|----------|-------------|---|
| Haiku | 2/9 (22%) | 9/9 (100%) | **+78pp** |
| Sonnet | 9/9 | 9/9 | +0pp |
| Opus | 9/9 | 9/9 | +0pp |

**spike_behavior (复杂任务):**

| Model | No Skill | Exact Skill | Δ |
|-------|----------|-------------|---|
| Haiku | 8/9 (89%) | 4/9 (44%) | **-44pp** |
| Sonnet | 8/9 | 8/9 | +0pp |
| Opus | 8/9 | 8/9 | +0pp |

**结论**: Haiku 在简单任务上从 skill 获益 +78 个百分点，在复杂任务上被 skill 拖累 -44 个百分点。Sonnet 和 Opus 完全不受影响。Skill 的效果完全由 **任务复杂度 × 模型能力** 的交互决定。

---

### Finding 2: 二值阈值效应 — SKILL.md 概述无用，任意一个 reference 文件即可满分

**neuro_metadata + Haiku 消融:**

| 消融条件 | 得分 | 结论 |
|----------|------|------|
| no_skill | 2/9 | 基线 |
| skillmd_only（仅概述） | **2/9** | 概述 = 没用！ |
| only_pitfalls | **9/9** | 任意一个详细文件就够 |
| only_code | **9/9** | 同上 |
| only_workflow | **9/9** | 同上 |
| full_skill | **9/9** | 满配 |

**结论**: 存在信息量的二值阈值——低于阈值（仅概述）= 没效果，高于阈值（概述 + 任意一个 reference）= 满分。Skill 的价值来自具体细节，不是高层总结。

---

### Finding 3: 成分毒性不对称 — 代码是安全的，文字指令是危险的

**spike_behavior + Haiku 消融 (baseline 8/9):**

| 消融条件 | 得分 | Δ | 毒性分类 |
|----------|------|---|----------|
| no_skill | 8/9 | — | — |
| **only_code** | **8/9** | 0 | **安全** |
| **only_pitfalls** | **4/9** | -4 | **有害：过度防御** |
| **only_workflow** | **0/8** | -8 | **致命：复杂度压垮** |
| skillmd_only | 0/8 | -8 | 致命 |
| full_skill | 4/9 | -4 | 综合负面 |

**Sonnet 同样消融 (baseline 8/9):**

| 消融条件 | 得分 |
|----------|------|
| skillmd_only | 8/9 |
| only_pitfalls | 8/9 |
| only_code | 8/9 |
| only_workflow | 8/9 |

**结论**: 对弱模型在复杂任务上：
- **参考代码是唯一安全的 skill 成分**（不改变模型行为）
- **Pitfalls 警告导致过度防御**（模型添加不必要的错误处理，代码变臃肿）
- **Workflow 指令导致复杂度压垮**（模型试图遵循每个步骤但无法完成）
- 强模型（Sonnet）对所有成分免疫

---

### Finding 4: 自己写的 skill 最不适合自己

**spike_behavior 跨模型 skill 生成 (Haiku 作为使用者):**

| Skill 作者 | Haiku 得分 | Opus 得分 |
|-----------|-----------|-----------|
| 无 skill | 8/9 | 8/9 |
| Haiku 写的 | **0** (崩溃) | 8/9 |
| Opus 写的 | **8/9** | 8/9 |
| 手工精调 exact skill | 4/9 | 8/9 |

**结论**: 反直觉——Haiku 写的 skill 把自己带崩，Opus 写的反而安全。原因推测：
- Haiku 写的 skill 质量差，含错误指令，自己遵循时被误导
- Opus 写的 skill 更准确简洁，Haiku 更容易跟随
- 这打破了 "模型自己写的 skill 最适合自己" 的假设

---

## 对论文的启示

### 修正后的假设

| 原假设 | 实际发现 | 启示 |
|--------|---------|------|
| F1: Near-miss skill 比 no skill 更危险 | 不完全——取决于任务复杂度和模型能力 | 需要更细粒度的 alignment 分类 |
| F2: 弱模型获益更多 | **部分成立但有致命反转**——简单任务上获益最多，复杂任务上受害最严重 | Skill Paradox 是核心发现 |
| F3: 强模型写的 skill 不一定适合弱模型 | **反面成立**——强模型写的 skill 反而更安全 | Skill 质量 > Skill 复杂度匹配 |
| F4: Pitfalls 可能导致过度防御 | **完全成立**——pitfalls 是伤害弱模型的主要来源 | Skill 设计应优先给代码而非警告 |

### 论文叙事建议

核心故事：**Skills have an optimal complexity zone relative to model capability.**

```
        Skill Benefit
            ↑
     +78pp  |    ★ Haiku + simple task
            |
      0pp   |----★-★-★---- Sonnet/Opus (robust)
            |
    -44pp   |              ★ Haiku + complex task
            ↓
            ───────────────────→
            Simple              Complex
                  Task Complexity
```

### 实用指南（论文 Section 7）

| 场景 | 建议 |
|------|------|
| 弱模型 + 简单任务 | 给 skill，任何 reference 文件都能帮忙 |
| 弱模型 + 复杂任务 | **只给参考代码**，不给 workflow/pitfalls |
| 强模型 + 任何任务 | Skill 可有可无，不会帮倒忙 |
| Skill 作者选择 | 用最强模型写，不要让弱模型自己写 |

---

## 成本汇总

| 项目 | 花费 |
|------|------|
| Phase 1: 主实验 (3 模型 × 2 场景 × 3 条件) | $3.64 |
| Phase 3: 跨模型 (neuro_metadata) | $0.91 |
| Phase 4a: Haiku 消融 (neuro_metadata) | $0.25 |
| Phase 4b: Haiku 消融 (spike_behavior) | $0.26 |
| Phase 4c: Sonnet 消融 (spike_behavior) | $0.49 |
| Phase 5: 跨模型生成 (spike_behavior) | $1.49 |
| **总计** | **$7.03** |

在 $200 预算的 3.5% 内完成了 pilot 验证。
