# 进展汇报（二）：v4 产出物——3 个生产级 Skill + 元技能体系

## 总览

v4 版本在修复 YAML 兼容性和关键词匹配问题后，基于 question.csv 中的真实科学数据处理需求，生产了 **3 个通过 skill-metric 24/24 满分验证的 skill 包**：2 个面向神经科学数据处理的工具 skill（neuro-metadata-gen, spike-behavior-organize），以及 1 个 **"元技能" requirement-to-skill**——它能从纯文本需求描述直接生成满分 skill 包，形成了从"对话→技能"到"需求→技能"的完整技能生产体系。每个 skill 都经过了 `--help` 测试和合成数据端到端测试验证。

---

## 一、v4 skill 生产流程

```
question.csv 科学数据需求
        │
        ▼
  构造多轮对话（10-20 轮，含 ≥5 次 error→fix 迭代）
        │
        ▼
  conversation-to-skill v4 提取（6 步 API 流水线）
        │
        ├── SKILL.md       (body < 5000 字符，单行 YAML)
        ├── scripts/main.py (完整 CLI 工具)
        ├── scripts/requirements.txt
        ├── references/workflow.md + pitfalls.md
        └── assets/example_output.md
        │
        ▼
  skill-metric 验证 → 24/24 ✓
        │
        ▼
  代码可用性测试（--help + 合成数据端到端）
```

## 二、Skill 1：neuro-metadata-gen

### 基本信息

| 属性 | 说明 |
|------|------|
| 来源需求 | question.csv #1（Researcher A，神经科学） |
| 对话文件 | `conversations/01_neuro_metadata_gen.json`（14 轮） |
| 功能 | 递归扫描 HDF5/MAT 目录，提取内部结构元数据，生成 meta.json |
| 代码量 | `scripts/main.py` 708 行 |
| 依赖 | h5py ≥3.9, scipy ≥1.11, numpy ≥1.24, tqdm (optional) |
| 评分 | **24/24** |

### 核心功能

1. **HDF5 递归检查**：使用 h5py 递归遍历 group/dataset 层级，记录每个 dataset 的完整路径（如 `recording/eeg/data`）、shape、dtype、字节数。不同于朴素实现只读 top-level keys。

2. **MATLAB v7.3 自动 fallback**：MATLAB 的 `-v7.3` 保存选项生成的文件实际是 HDF5 格式，scipy.io.loadmat 会抛出 `ValueError: Unknown mat file type` 或 `NotImplementedError`。main.py 捕获这些异常并自动切换到 h5py 读取，对用户完全透明。

3. **通配符模式合并**：多个被试目录（`subject_01/`, `subject_02/` ...）中结构相同的文件被合并为一个条目（如 `subject_*/TimeSeries.h5`），记录合并数量和 dim-0 范围。

4. **灵活 shape 比较**：三种模式——`exact`（完全匹配）、`flexible`（忽略第一维度差异）、`ndim_only`（只比较维度数）。神经科学数据中，第一维度（神经元数量）因被试而异，`flexible` 模式允许合并。

5. **大文件保护**：超过 2GB 的文件限制 HDF5 递归深度为 2 层，避免长时间扫描。

### 对话中的关键 error→fix 迭代

| 轮次 | 用户报告的问题 | 修复方案 |
|------|--------------|---------|
| Turn 3 | 只扫描了顶层目录，子目录下的文件全部遗漏 | 改用 `pathlib.rglob` 递归发现文件 |
| Turn 5 | `ValueError: Unknown mat file type` 读取 v7.3 文件 | 添加 try/except 捕获，fallback 到 h5py |
| Turn 7 | 扫描 3GB 的 HDF5 文件时脚本卡住 | 添加文件大小阈值，超过则限制递归深度 |
| Turn 9 | 15 个被试产生 30 条重复条目，输出冗余 | 实现 `merge_by_pattern`：计算结构签名，合并一致条目 |
| Turn 11 | 合并失败——subject 间神经元数量不同导致 shape 不匹配 | 实现 `flexible` 模式：比较时忽略 dim-0 |
| Turn 13 | 输出的 JSON 缺少汇总信息 | 添加 `summary` 段（total_files, format_counts, errors） |

### 代码可用性验证

```bash
# --help 测试
$ python3 scripts/main.py --help
usage: neuro-metadata-gen [-h] [-o OUTPUT] [--merge | --no-merge]
                          [--subject-pattern SUBJECT_PATTERN]
                          [--shape-mode {exact,flexible,ndim_only}] [-v]
                          root_dir

# 合成数据测试
$ python3 scripts/main.py test_data/ -o meta.json -v
[INFO] Scanning directory: test_data/
[INFO] Discovered 6 files.
[INFO] Summary: 6 files, 8.83 MB total, 12 datasets, 0 errors.
```

输出 meta.json 中 TimeSeries.h5 文件成功合并为 `subject_*/TimeSeries.h5`（count=3），v7.3 格式的 data_full.mat 标记为 `mat-v7.3 (hdf5)`。

---

## 三、Skill 2：spike-behavior-organize

### 基本信息

| 属性 | 说明 |
|------|------|
| 来源需求 | question.csv #6（Researcher B，神经科学） |
| 对话文件 | `conversations/06_spike_behavior_organize.json`（20 轮） |
| 功能 | 多格式神经 spike/behavior 数据标准化为统一 trial-based HDF5 |
| 代码量 | `scripts/main.py` ~900 行 |
| 依赖 | h5py, scipy, numpy, pynwb, pandas |
| 评分 | **24/24** |

### 核心功能

1. **多格式输入支持**：
   - **XDS (Dryad)**: MATLAB struct 格式，需 `[0,0]` 解包 + 字段名映射
   - **PyalData**: MATLAB struct array，需迭代每个 trial + 多脑区 spike 字段自动检测
   - **NWB (DANDI)**: pynwb 格式，需 VectorIndex spike 提取（不能直接索引）
   - **PyalData (Dryad)**: Trial-based 组织格式

2. **统一输出格式**：
   ```
   output.h5
   └── <dataset>/<session>/
       └── trial_0000/
           ├── timestamps   (N_bins,)      float64
           ├── spikes       (N_bins, N_units) int32
           └── behavior     (N_bins, N_dims)  float64
   ```

3. **Spike binning**：使用 `np.histogram` 将不规则 spike timestamps 转为固定时间窗口的 bin counts

4. **行为数据重采样**：不同格式的采样率不同（1ms/4ms/10ms），通过 `scipy.interpolate.interp1d` 统一到目标 bin size

5. **运动学统一**：有的数据只有 position，有的只有 velocity，有的只有 EMG。通过 `compute_kinematics` 统一为 position + velocity + acceleration 三通道

6. **质量检查**：每个 trial 计算 bitmask QC flags——发放率异常、NaN 值、长度不匹配、零单元等

### 对话中的关键 error→fix 迭代

| 轮次 | 问题 | 修复 |
|------|------|------|
| Turn 3 | MATLAB struct KeyError | `[0,0]` 解包后才能访问字段 |
| Turn 5 | NWB spike 获取失败 | 改用 `units.get_unit_spike_times(idx)` |
| Turn 7 | Trial outcome 字段名不一致 | 统一 SUCCESS_MARKERS 映射表 |
| Turn 9 | 不同格式采样率不同 | `interp1d` 重采样 + `histogram` binning |
| Turn 11 | 有的数据只有 velocity 没有 position | `compute_kinematics` 互转 |
| Turn 13 | PyalData struct array 遍历方式错误 | `load_pyaldata` + `np.hstack` |
| Turn 17 | behavior 数据被 in-place 修改，后续 trial 数据错误 | 每个 trial 创建独立的 `trial_behavior` dict |
| Turn 19 | 无法识别低质量 trial | `quality_check_trial` bitmask 质量标记 |

### 代码可用性验证

```bash
$ python3 scripts/main.py --help
usage: spike-behavior-organize [-h] [-o OUTPUT] [--bin-ms BIN_MS]
                                [--format {xds,pyaldata,nwb,auto}]
                                [--verify] input_paths [input_paths ...]

$ python3 scripts/main.py demo_data/ -o demo_output.h5 --verify
[INFO] Writing HDF5 to: demo_output.h5
[INFO] trial_0000  spikes=(75, 8)  behavior=(75, 6)  qc_flags=0
[INFO] Verification PASSED
```

---

## 四、Skill 3：requirement-to-skill（元技能）

### 基本信息

| 属性 | 说明 |
|------|------|
| 来源 | 无对话文件，从工作流经验总结而成 |
| 功能 | 将纯文本需求描述 → 完整 skill 包（不需要真实对话） |
| 代码量 | `scripts/main.py` ~490 行（4 个子命令） |
| 评分 | **24/24**（首次 23/24，修复连字符问题后满分） |

### 核心洞察

真实对话中的 error→fix 迭代是 skill 质量的关键来源——它产生了真实的 pitfalls、鲁棒的代码和有价值的文档。**requirement-to-skill** 的核心思路是：如果我们能**构造**这样的对话，就能从纯需求描述出发生成高质量 skill，无需等待真实对话发生。

### 5 阶段流水线

```
Phase 1: 需求分析
  ├── 核心任务（1-2 句话）
  ├── 输入/输出
  ├── 技术挑战
  └── 领域陷阱
        │
Phase 2: 对话构造（10-20 轮）
  ├── Turn 1-2: 用户提需求 → 助手给初版（故意不完美）
  ├── Turn 3-6: 错误1 → 修复 → 错误2 → 修复
  ├── Turn 7-10: 边界情况 → 深层修复 → 功能增强
  └── Turn 11-14: 最终集成 → 生产级脚本
  规则：≥5 次 error→fix，错误必须真实（非 Q&A）
        │
Phase 3: Skill 提取
  └── 使用 conversation-to-skill v4 生成多文件包
        │
Phase 4: 验证 → skill-metric 24/24
        │
Phase 5: 代码测试 → --help + 合成数据
```

### 4 个子命令

```bash
$ python3 scripts/main.py scaffold --name my-skill   # 创建 skill 骨架目录
$ python3 scripts/main.py analyze --requirement "..."  # 生成需求分析模板
$ python3 scripts/main.py validate --skill-dir my-skill/  # 运行 skill-metric
$ python3 scripts/main.py test --skill-dir my-skill/      # 代码可用性测试
```

### 意义

这个元技能解决了 conversation-to-skill 的**冷启动问题**：当没有现成的对话日志时，requirement-to-skill 可以从需求描述出发，先合成对话再提取 skill，形成完整的技能生产流水线。

---

## 五、三个 skill 的评分对比

| Skill | Format (8) | Completeness (8) | Writing (8) | Total | --help | 端到端测试 |
|-------|-----------|------------------|-------------|-------|--------|-----------|
| neuro-metadata-gen | 8 | 8 | 8 | **24/24** | ✓ 通过 | ✓ 6 files → 2 merged |
| spike-behavior-organize | 8 | 8 | 8 | **24/24** | ✓ 通过 | ✓ 50 bins × 10 units |
| requirement-to-skill | 8 | 8 | 8 | **24/24** | ✓ 通过 | ✓ 4 子命令全部正常 |

---

## 六、skill 体系的整体架构

```
┌─────────────────────────────────┐
│  输入方式 A: 真实对话日志        │
│  conversations/*.json            │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  conversation-to-skill v4       │  ← 核心生成器
│  (6 步 API 流水线)              │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  输出: Skill 包 (24/24)         │
│  SKILL.md + scripts/ +          │
│  references/ + assets/          │
└─────────────────────────────────┘
           ▲
           │
┌──────────┴──────────────────────┐
│  输入方式 B: 纯文本需求          │
│  requirement-to-skill            │  ← 元技能（构造对话 → 提取 skill）
│  (5 阶段流水线)                  │
└─────────────────────────────────┘
           ▲
           │
┌──────────┴──────────────────────┐
│  质量保障: skill-metric          │  ← 24 分评分工具
│  (756 行，零依赖)               │
└─────────────────────────────────┘
```

---

## TODO

- 将 v4 模板推广到 question.csv 剩余 7 个场景的 skill 生成（目前只完成了 2 个神经科学场景）
- 为 spike-behavior-organize 补充真实数据测试（目前只用了合成数据）
- 探索 requirement-to-skill 在非神经科学领域（地球科学、材料科学等）的泛化能力
