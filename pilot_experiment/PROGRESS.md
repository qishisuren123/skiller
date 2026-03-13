# Pilot Experiment Progress

**Last updated**: 2026-03-11 (框架重构 Phase 0-1 完成 + Phase 4 调度器)
**Total cost**: $15.86 (旧实验) + $0 (新框架纯代码)
**Total API calls**: ~200 (旧)
**总预算**: $500 (目标 EMNLP 2026 Main)
**总预算**: $500 (目标 EMNLP 2026 Main)

## 2026-03-11 框架重构

### Phase 0: 框架搭建 ✅
- 创建 `lib/` 共享库包（8 个模块）
- `config.py` 移到根目录
- `lib/api_client.py` — 统一 API 调用（从 run_experiment_v2.py 提取）
- `lib/evaluator.py` — 4 层评估（从 scripts/evaluator_v2.py 移动）
- `lib/skill_injector.py` — 多文件 skill 序列化（5 级完整度: L0-L4）
- `lib/skill_stripper.py` — SKILL.md 子级裁剪（12 种模式）
- `lib/skill_mutator.py` — 5 种错误注入（stale_api, wrong_default, missing_edge_case, wrong_import, logic_error）
- `lib/scenario_loader.py` — 场景加载器 + 分层抽样
- `lib/llm_judge.py` — LLM-as-Judge（从 scripts/ 移动）
- `lib/stats_analysis.py` — 统计检验（从 scripts/ 移动）
- `scenarios/_registry.py` — 场景自动发现

### Phase 1: 场景迁移 ✅
- 30 个场景从 scenarios_v2.py + scenarios_extended.py 提取到独立目录
- 每个场景: scenario.yaml + task.md + test_script.py
- 目录格式: S001_neuro_metadata ~ S030_fossil_morpho
- 验证: 30/30 场景 test_script 可独立运行

### Phase 4: 实验主调度器 ✅
- `experiment_runner.py` — config-driven 实验调度器
- ExperimentConfig + TrialConfig 数据类
- RQ1-RQ4 + significance 配置生成器
- 崩溃恢复（append JSONL + 跳过已完成 trial）
- dry-run 验证通过

### 批处理工具 ✅
- `tools/validate_scenarios.py` — 场景验证（30/30 通过）
- `tools/validate_skills.py` — 24-point rubric 质量验证
- `tools/generate_scenarios.py` — 合成场景生成（10 领域 × 70 topics）
- `tools/generate_skills_batch.py` — 批量 skill 生成（direct + pipeline）
- `tools/export_figures.py` — RQ1-RQ4 图表生成
- `tools/export_latex.py` — LaTeX 表格导出

### 待做
- [ ] Phase 2: 为 S001-S030 生成 skill 包（~$25）
- [ ] Phase 3: 生成 S031-S100 合成场景（~$24）
- [ ] Phase 5: 采样 30 场景跑实验（~$230）
- [ ] Phase 6: 分析与可视化（$0）

| 范围 | 场景数 | 领域数 | 难度分布 | 测试项/场景 |
|------|-------|--------|---------|------------|
| 原始 S01-S10 | 10 | 5 领域 | 3 easy / 4 medium / 3 hard | 6-9 |
| 扩展 S11-S30 | 20 | 18 新领域 | 6 easy / 11 medium / 3 hard | 12-15 + 2 SCORE |
| **合计** | **30** | **23 领域** | **9 easy / 16 medium / 5 hard** | **6-15 + 2 SCORE** |

### 30 场景领域覆盖
| 场景 | 领域 | 难度 | 测试数 |
|------|------|------|--------|
| S01_neuro_metadata | neuroscience | easy | 9 |
| S02_spike_behavior | neuroscience | hard | 9 |
| S03_spatial_tx | life_science | medium | 8 |
| S04_satellite | earth_science | medium | 7 |
| S05_protein_parse | life_science | medium | 8 |
| S06_gene_expression | life_science | hard | 6 |
| S07_data_viz | neuroscience | easy | 8 |
| S08_materials_qa | materials_science | medium | 7 |
| S09_earth_obs | earth_science | easy | 6 |
| S10_multimodal | life_science | hard | 6 |
| S11_particle_physics | physics | medium | 12 |
| S12_uv_spectroscopy | chemistry | medium | 12 |
| S13_biodiversity | ecology | easy | 13 |
| S14_clinical_lab | medical | easy | 12 |
| S15_light_curves | astronomy | hard | 13 |
| S16_fastq_qc | genomics | medium | 12 |
| S17_ctd_ocean | oceanography | medium | 13 |
| S18_radiosonde | atmospheric_science | medium | 14 |
| S19_eeg_filtering | signal_processing | medium | 14 |
| S20_survey_analysis | social_science | easy | 14 |
| S21_air_quality | environmental_science | easy | 14 |
| S22_well_log | geology | medium | 14 |
| S23_epidemic_curve | epidemiology | medium | 14 |
| S24_xrd_peaks | materials_science | hard | 15 |
| S25_citation_graph | network_science | medium | 15 |
| S26_earthquake_catalog | seismology | medium | 14 |
| S27_crop_features | agricultural_science | easy | 14 |
| S28_audio_features | psychoacoustics | medium | 15 |
| S29_flood_frequency | hydrology | medium | 14 |
| S30_fossil_morpho | paleontology | easy | 15 |

## 实施进度

### ✅ Phase 1: 评价体系加固（代码改动，$0）
- [x] **1.1** scenarios_v2.py: 每场景增加 3-6 个 L2 测试 + 2 个 SCORE 连续指标
- [x] **1.2** evaluator_v2.py: 新增 classify_error() 函数，7 类错误分类，返回值加 error_type
- [x] **1.3** scripts/llm_judge.py: LLM-as-Judge 模块，用 Haiku 评 4 维度 (1-5)
- [x] **1.4** scripts/re_evaluate.py: 用增强测试重跑所有现有结果

### ✅ Phase 2: 公平性 — Baseline 条件
- [x] **2.1** run_experiment_v2.py: 新增 run_baseline_experiment() — CoT, few_shot_1, few_shot_3, doc_only
- [x] **2.2** data/human_expert_skills/: 5 个人工专家 skill (S02, S04, S08, S09, S10)
- [x] **2.2b** run_experiment_v2.py: 新增 run_human_expert_experiment()
- [x] **2.3** Token 公平性报告: analyze_results() 中输出 skill_token_count 统计
- [x] **2.4** temperature + n_runs: call_model() 支持 temperature 参数, main() 支持 --temperature 和 --n-runs

### ✅ Phase 3: 新实验
- [x] **3.1** run_self_skill_experiment(): Self-Skill 实验
- [x] **3.2** run_vaccination_experiment(): Skill 疫苗实验
- [x] **3.3** run_code_text_ablation(): Code vs Text 语义化消融
- [x] **3.4** run_length_ablation(): Skill 长度效应 (25%/50%/75%)
- [x] **3.5** run_calibrated_skill_experiment(): 能力校准 Skill

### ✅ Phase 4: 统计显著性
- [x] scripts/stats_analysis.py: paired t-test, bootstrap CI, Cohen's d, ANOVA

### ✅ Phase 5: 分析与可视化
- [x] scripts/analysis_v3.py: 7 个图表生成
- [x] scripts/latex_tables.py: 3 个 LaTeX 表格自动生成
- [x] data/few_shot_examples.py: 3 个 few-shot 范例

### ✅ Phase 6: 场景扩展（$0，纯代码）
- [x] **6.1** scripts/scenarios_extended.py: 20 个新场景 (S11-S30)，覆盖 18 个新学科领域
- [x] **6.2** run_experiment_v2.py 自动合并 SCENARIOS + SCENARIOS_EXTENDED = 30 场景
- [x] **6.3** 全部 30 场景通过 evaluator 集成验证（无 crash，正确计数 PASS/FAIL/SCORE）

## 新增/修改文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| scripts/config.py | 修改 | +TEMPERATURE, VACCINATION_PREFIX 常量 |
| scripts/evaluator_v2.py | 修改 | +classify_error(), error_type 字段 |
| scripts/scenarios_v2.py | 修改 | 每场景 +3-6 测试 + 2 SCORE 指标 |
| scripts/scenarios_extended.py | **新建** | **20 个新场景 S11-S30 (4670 行)** |
| run_experiment_v2.py | 重写 | +6 新实验函数 + 自动合并扩展场景 |
| scripts/llm_judge.py | 新建 | LLM-as-Judge (Haiku) |
| scripts/re_evaluate.py | 新建 | 增强测试重跑 |
| scripts/stats_analysis.py | 新建 | 统计检验 |
| scripts/analysis_v3.py | 新建 | 7 图表生成 |
| scripts/latex_tables.py | 新建 | LaTeX 表格 |
| data/few_shot_examples.py | 新建 | 3 个 few-shot 范例 |
| data/human_expert_skills/S02_expert.md | 新建 | 人工 skill |
| data/human_expert_skills/S04_expert.md | 新建 | 人工 skill |
| data/human_expert_skills/S08_expert.md | 新建 | 人工 skill |
| data/human_expert_skills/S09_expert.md | 新建 | 人工 skill |
| data/human_expert_skills/S10_expert.md | 新建 | 人工 skill |

## 执行计划（基于 30 场景 × 6 模型）

| 步骤 | Phase | 命令 | 预计花费 | 累计 |
|------|-------|------|---------|------|
| 1 | 1.4 | `python scripts/re_evaluate.py` | $0 | $0 |
| 2 | 1.3 | `python scripts/llm_judge.py` | $0.5 | $0.5 |
| 3 | main | `python run_experiment_v2.py --phases main --models haiku,sonnet,opus,gpt4o_mini,gpt41_mini,gemini_flash` | $50 | $50.5 |
| 4 | baseline | `python run_experiment_v2.py --phases baseline --models haiku,sonnet,opus,gpt4o_mini,gpt41_mini,gemini_flash` | $50 | $100.5 |
| 5 | human_expert | `python run_experiment_v2.py --phases human_expert` | $6 | $106.5 |
| 6 | self_skill | `python run_experiment_v2.py --phases self_skill` | $25 | $131.5 |
| 7 | vaccination | `python run_experiment_v2.py --phases vaccination` | $12 | $143.5 |
| 8 | code_text | `python run_experiment_v2.py --phases code_text` | $45 | $188.5 |
| 9 | length | `python run_experiment_v2.py --phases length` | $18 | $206.5 |
| 10 | calibrated | `python run_experiment_v2.py --phases calibrated` | $25 | $231.5 |
| 11 | significance | `python run_experiment_v2.py --phases significance --temperature 0.3 --n-runs 3` | $75 | $306.5 |
| 12 | analysis | `python scripts/analysis_v3.py && python scripts/latex_tables.py` | $0 | $306.5 |

**预算安排**: 全量跑 ~$307，可分阶段执行。先跑 main + baseline (步骤 3-4, ~$100) 看主效应，再决定后续实验。

## 已有实验结果 (Phase 1 & v2 main, 仅 S01-S02)

### Cost by model
```json
{
  "haiku": 0.2726,
  "sonnet": 0.6036,
  "opus": 3.6713
}
```

### Phase 1 nearmiss (18 runs)

| Model | Scenario | Condition | Pass | Cost |
|-------|----------|-----------|------|------|
| haiku | neuro_metadata | no_skill | 2/9 | $0.0166 |
| haiku | neuro_metadata | exact_skill | 9/9 | $0.0362 |
| haiku | spike_behavior | no_skill | 8/9 | $0.0303 |
| haiku | spike_behavior | exact_skill | 4/9 | $0.0385 |
| sonnet | neuro_metadata | no_skill | 9/9 | $0.0693 |
| sonnet | spike_behavior | no_skill | 0/8 | $0.0725 |
| sonnet | spike_behavior | exact_skill | 8/9 | $0.1255 |
| opus | neuro_metadata | no_skill | 9/9 | $0.2904 |
| opus | spike_behavior | no_skill | 0/8 | $0.3756 |
