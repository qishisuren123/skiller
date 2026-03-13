# Three-System Skill Generator Comparison Report

## Overview

This report compares three skill generation systems on the same task: generating a neuroscience data metadata scanning tool (from question.csv #1).

| System | Approach | Source |
|--------|----------|--------|
| **A: conversation-to-skill** | Extract skill from conversation log | skill_v4/generated_skills/neuro-metadata-gen/ |
| **B: requirement-to-skill** | Generate skill from plain-language requirement | comparison_test/system_b_output/neuro-metadata-gen-b/ |
| **C: official skill-creator** | Anthropic's interactive skill-creation framework | comparison_test/system_c_output/neuro-metadata-gen-c/ |

---

## 1. skill-metric Static Scoring (24-point rubric)

| Dimension | Max | System A | System B | System C |
|-----------|-----|----------|----------|----------|
| **Format** | 8 | 8 | 8 | 8 |
| **Completeness** | 8 | 8 | 8 | 5 |
| **Writing** | 8 | 8 | 8 | 6 |
| **Total** | **24** | **24** | **24** | **19** |

### System C Deductions (-5 points)
- No `license` field (-1 completeness, -1 writing)
- No `compatibility` field (-1 completeness)
- No `metadata` block (-1 completeness)
- No explicit trigger phrase in description (-1 writing)

**Analysis**: Systems A and B both achieve perfect 24/24 because they were designed with the rubric in mind. System C (official skill-creator) does not target the skill-metric rubric — it focuses on practical effectiveness and eval-driven iteration. The 5-point gap reflects a philosophical difference: the skill-creator considers `license` and `compatibility` optional metadata, not quality indicators.

---

## 2. Practical Usability Testing (7 assertions × 3 evals)

### Test Setup
- **Test data**: 8 synthetic files (3 subjects × TimeSeries.h5 + data_full.mat + 2 additional .mat files)
- **E1 (Basic)**: Standard scan, default settings
- **E2 (Boundary)**: v7.3 fallback + merge enabled
- **E3 (Real-world)**: Full pipeline with verbose logging

### Assertion Results

| Assertion | System A | System B | System C | Baseline |
|-----------|----------|----------|----------|----------|
| A1: Valid JSON | 3/3 | 3/3 | 3/3 | 3/3 |
| A2: All 8 files listed | 3/3 | 3/3 | 3/3 | 3/3 |
| A3: HDF5 shape/dtype recorded | 3/3 | 3/3 | 3/3 | 0/3 |
| A4: v7.3 MAT detected | 3/3 | 3/3 | 3/3 | 0/3 |
| A5: Wildcard merge exists | 3/3 | 3/3 | 3/3 | 0/3 |
| A6: No unhandled errors | 3/3 | 3/3 | 3/3 | 0/3 |
| A7: Expected keys present | 3/3 | 3/3 | 3/3 | 3/3 |
| **Total** | **21/21** | **21/21** | **21/21** | **9/21** |
| **Pass Rate** | **100%** | **100%** | **100%** | **43%** |

**Analysis**: All three skill-generated systems achieve perfect practical scores. The baseline fails on 4 assertions because it:
- Doesn't record dataset shapes (only lists keys)
- Doesn't handle v7.3 format (error left in output)
- Doesn't implement wildcard merging
- Has 1 unhandled error (v7.3 file)

This confirms that **skills are genuinely useful** — they improve task completion from 43% to 100%.

---

## 3. Baseline Improvement

| Metric | With Skill (avg) | Without Skill | Improvement |
|--------|-----------------|---------------|-------------|
| Assertions passed | 21/21 (100%) | 9/21 (43%) | **+57 percentage points** |
| v7.3 handling | Yes | No | Critical feature gap |
| Wildcard merging | Yes | No | Critical feature gap |
| Shape/dtype metadata | Yes | No | Critical feature gap |
| Error count | 0 | 1 | One file unprocessable |

---

## 4. Code/Script Quality

| Metric | System A | System B | System C |
|--------|----------|----------|----------|
| main.py lines | 708 | 262 | 207 |
| --help works | Yes | Yes | Yes |
| End-to-end test | Pass | Pass | Pass |
| Dependencies documented | requirements.txt | requirements.txt | In SKILL.md |
| Logging | Python logging | Python logging | Python logging |
| CLI framework | argparse (full) | argparse (full) | argparse (full) |
| Shape comparison modes | 3 (exact/flexible/ndim_only) | 3 (exact/flex/ndim) | 3 (exact/flexible/ndim_only) |
| Subject pattern regex | Configurable | Configurable | Configurable |
| Large file handling | Depth-limited | Depth-limited | Depth-limited |

**Analysis**: System A is the most verbose (708 lines) with extensive docstrings and the most feature-complete implementation. System B (262 lines) is well-structured and concise. System C (207 lines) is the most compact. All three produce functionally equivalent output on the test data.

---

## 5. Process Efficiency

| Metric | System A | System B | System C |
|--------|----------|----------|----------|
| **Generation input** | Real conversation log | Plain-text requirement | Interactive interview |
| **Generation time** | Already complete | ~30 min (5-phase pipeline) | ~45 min (interview + eval loop) |
| **API calls (estimated)** | ~6 Sonnet calls | ~5-8 calls | ~15-30 calls (interview + evals + grading) |
| **Human intervention** | None (fully automated) | Minimal (provide requirement) | Significant (answer questions, review evals, provide feedback) |
| **Reproducibility** | High (deterministic pipeline) | High (same requirement → similar output) | Low (depends on interactive choices) |
| **Iteration capability** | None built-in | Phase 4-5 validation loop | Full eval-driven iteration loop |
| **Rubric awareness** | Embedded (targets 24/24) | Embedded (targets 24/24) | None (doesn't know about rubric) |

---

## 6. Weighted Final Scores

| Dimension | Weight | System A | System B | System C |
|-----------|--------|----------|----------|----------|
| skill-metric (/24) | 20% | 24 → 4.80 | 24 → 4.80 | 19 → 3.80 |
| Practical tests (/21) | 40% | 21 → 8.40 | 21 → 8.40 | 21 → 8.40 |
| Baseline improvement | 15% | +57pp → 1.50 | +57pp → 1.50 | +57pp → 1.50 |
| Code quality (/10) | 10% | 9 → 0.90 | 8 → 0.80 | 7 → 0.70 |
| Process efficiency (/10) | 15% | 9 → 1.35 | 8 → 1.20 | 5 → 0.75 |
| **Weighted Total** | **100%** | **16.95** | **16.70** | **15.15** |

### Code Quality Breakdown (/10)
- System A: 9/10 — Most complete, extensive docs, full CLI, but verbose
- System B: 8/10 — Clean, well-structured, concise
- System C: 7/10 — Compact but minimal docs, no requirements.txt

### Process Efficiency Breakdown (/10)
- System A: 9/10 — Fully automated, no intervention, fast, reproducible
- System B: 8/10 — Near-automated, minimal input, reproducible
- System C: 5/10 — Interactive, requires significant human time, low reproducibility

---

## 7. Key Findings

### All Three Systems
1. **Functionally equivalent**: All produce correct meta.json with 100% assertion pass rate
2. **Skills are genuinely useful**: 43% → 100% improvement over baseline
3. **Core features complete**: v7.3 fallback, wildcard merging, shape recording

### System A (conversation-to-skill)
- **Strengths**: Most mature code, extensive documentation, fully automated
- **Weaknesses**: Requires real conversation as input (bootstrapping problem)
- **Best for**: Capturing existing expertise from conversation logs

### System B (requirement-to-skill)
- **Strengths**: Rubric-aware, clean code, minimal input required
- **Weaknesses**: Generated conversation may be less realistic than real one
- **Best for**: Generating skills from specifications without needing prior conversations

### System C (official skill-creator)
- **Strengths**: Eval-driven iteration, "pushy" description for better triggering, industry-standard approach
- **Weaknesses**: Doesn't target skill-metric rubric, requires significant human interaction, lower reproducibility
- **Best for**: Interactive skill development with user feedback loops

### The Rubric Gap
System C's 19/24 score is **not a quality failure** — it reflects a different design philosophy. The skill-creator prioritizes practical effectiveness (which it achieves at 100%) over structural metadata completeness. The missing fields (license, compatibility, metadata) are documentation metadata, not functional requirements.

---

## 8. File Inventory

```
comparison_test/
├── COMPARISON_REPORT.md          ← this file
├── common_requirement.md          ← shared requirement text
├── create_test_data.py            ← synthetic data generator
├── baseline_scan.py               ← no-skill baseline script
├── grade_results.py               ← 7-assertion automated grader
├── test_data/                     ← 8 synthetic neuroscience files
│   ├── Additional_mat_files/
│   │   ├── CustomColormaps.mat
│   │   └── FishOutline.mat
│   └── Subjects/
│       ├── subject_01/ (TimeSeries.h5 + data_full.mat v5)
│       ├── subject_02/ (TimeSeries.h5 + data_full.mat v7.3)
│       └── subject_03/ (TimeSeries.h5 + data_full.mat v5)
├── system_b_output/
│   └── neuro-metadata-gen-b/      ← System B skill package (24/24)
├── system_c_output/
│   └── neuro-metadata-gen-c/      ← System C skill package (19/24)
├── scores/
│   └── comparison.csv             ← skill-metric scores
└── eval_results/
    ├── system_a/{e1,e2,e3}/       ← 3 eval runs (21/21)
    ├── system_b/{e1,e2,e3}/       ← 3 eval runs (21/21)
    ├── system_c/{e1,e2,e3}/       ← 3 eval runs (21/21)
    ├── baseline/{e1,e2,e3}/       ← 3 baseline runs (9/21)
    └── grading_results.json
```

---

*Generated: 2026-03-07 | Test task: question.csv #1 (Researcher A, 神经科学数据元数据生成)*
