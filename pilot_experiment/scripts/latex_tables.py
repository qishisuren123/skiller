#!/usr/bin/env python3
"""
从 JSON 结果自动生成 LaTeX 表格
Table 1: Main Results (模型 × 场景，pass_rate + error bars + significance stars)
Table 2: Baseline Comparison
Table 3: Ablation Results
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import RESULTS_DIR, ROOT

TABLES_DIR = ROOT / "tables"
TABLES_DIR.mkdir(exist_ok=True)

SCENARIO_SHORT = {
    "S01_neuro_metadata": "S01", "S02_spike_behavior": "S02",
    "S03_spatial_tx": "S03", "S04_satellite": "S04",
    "S05_protein_parse": "S05", "S06_gene_expression": "S06",
    "S07_data_viz": "S07", "S08_materials_qa": "S08",
    "S09_earth_obs": "S09", "S10_multimodal": "S10",
}

MODEL_DISPLAY = {
    "haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus",
    "gpt4o": "GPT-4o", "gpt4o_mini": "GPT-4o-mini", "gpt41": "GPT-4.1",
    "gpt41_mini": "GPT-4.1-mini", "gemini_pro": "Gemini Pro", "gemini_flash": "Gemini Flash",
}


def load_results(filename="re_evaluated_results.json"):
    """加载结果"""
    path = RESULTS_DIR / filename
    if path.exists():
        return json.loads(path.read_text())
    path = RESULTS_DIR / "experiment_v2_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return []


def load_stats(filename="stats_analysis.json"):
    """加载统计分析"""
    path = RESULTS_DIR / filename
    if path.exists():
        return json.loads(path.read_text())
    return {}


def format_rate(rate, std=None, sig_stars=""):
    """格式化 pass_rate"""
    if rate is None:
        return "—"
    s = f"{rate:.0%}"
    if std is not None and std > 0:
        s += f"$\\pm${std:.0%}"
    if sig_stars:
        s += sig_stars
    return s


def significance_stars(p_value):
    """P 值转星号"""
    if p_value is None:
        return ""
    if p_value < 0.001:
        return "$^{***}$"
    elif p_value < 0.01:
        return "$^{**}$"
    elif p_value < 0.05:
        return "$^{*}$"
    return ""


def table1_main_results(results=None):
    """Table 1: Main Results — no_skill vs exact_skill 对比"""
    if results is None:
        results = load_results()

    # 收集数据
    data = defaultdict(dict)
    for r in results:
        s, m, c = r.get("scenario",""), r.get("model",""), r.get("condition","")
        pr = r.get("eval", {}).get("pass_rate", 0)
        if c in ("no_skill", "exact_skill"):
            data[(s, m)][c] = pr

    scenarios = sorted(set(s for (s, m) in data.keys()))
    models = sorted(set(m for (s, m) in data.keys()))

    # 生成 LaTeX
    n_scenarios = len(scenarios)
    col_spec = "l" + "cc" * n_scenarios
    lines = [
        "\\begin{table*}[t]",
        "\\centering",
        "\\caption{Main Results: Pass Rate (\\%) for No-Skill vs Exact-Skill conditions. "
        "Green indicates improvement, red indicates degradation.}",
        "\\label{tab:main_results}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
    ]

    # 头部
    header1 = "Model"
    header2 = ""
    for s in scenarios:
        short = SCENARIO_SHORT.get(s, s[:6])
        header1 += f" & \\multicolumn{{2}}{{c}}{{{short}}}"
        header2 += " & No-Skill & +Skill"
    lines.append(header1 + " \\\\")
    # cmidrule
    for i, s in enumerate(scenarios):
        col_start = 2 + i * 2
        lines.append(f"\\cmidrule(lr){{{col_start}-{col_start+1}}}")
    lines.append(header2 + " \\\\")
    lines.append("\\midrule")

    # 数据行
    for m in models:
        row = MODEL_DISPLAY.get(m, m)
        for s in scenarios:
            no_skill = data.get((s, m), {}).get("no_skill", None)
            exact = data.get((s, m), {}).get("exact_skill", None)
            row += f" & {format_rate(no_skill)} & {format_rate(exact)}"
        lines.append(row + " \\\\")

    # Delta 行
    lines.append("\\midrule")
    delta_row = "$\\Delta$"
    for s in scenarios:
        deltas = []
        for m in models:
            no_s = data.get((s, m), {}).get("no_skill")
            ex_s = data.get((s, m), {}).get("exact_skill")
            if no_s is not None and ex_s is not None:
                deltas.append(ex_s - no_s)
        avg_delta = np.mean(deltas) if deltas else 0
        color = "green" if avg_delta > 0 else "red" if avg_delta < 0 else "black"
        delta_row += f" & \\multicolumn{{2}}{{c}}{{\\textcolor{{{color}}}{{{avg_delta:+.0%}}}}}"
    lines.append(delta_row + " \\\\")

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table*}",
    ])

    tex = "\n".join(lines)
    (TABLES_DIR / "table1_main_results.tex").write_text(tex)
    print(f"  Table 1 saved ({len(models)} models × {len(scenarios)} scenarios)")
    return tex


def table2_baseline_comparison(results=None):
    """Table 2: Baseline Comparison"""
    if results is None:
        results = load_results()

    conditions = ["no_skill", "cot", "few_shot_1", "few_shot_3", "doc_only",
                  "exact_skill", "human_expert_skill"]
    cond_display = {
        "no_skill": "No Skill", "cot": "CoT", "few_shot_1": "1-Shot",
        "few_shot_3": "3-Shot", "doc_only": "Doc Only",
        "exact_skill": "Full Skill", "human_expert_skill": "Human Skill",
    }

    # 按 model × condition 汇总
    data = defaultdict(lambda: defaultdict(list))
    for r in results:
        m, c = r.get("model",""), r.get("condition","")
        if c in conditions:
            pr = r.get("eval", {}).get("pass_rate", 0)
            data[m][c].append(pr)

    models = sorted(data.keys())
    active_conds = [c for c in conditions if any(c in data[m] for m in models)]

    if not active_conds:
        print("  Table 2 skipped (no baseline data)")
        return ""

    col_spec = "l" + "c" * len(active_conds)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Baseline Comparison: Mean Pass Rate (\\%) across scenarios.}",
        "\\label{tab:baseline}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
    ]

    header = "Model & " + " & ".join(cond_display.get(c, c) for c in active_conds) + " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    for m in models:
        row = MODEL_DISPLAY.get(m, m)
        for c in active_conds:
            vals = data[m].get(c, [])
            if vals:
                mean = np.mean(vals)
                row += f" & {mean:.0%}"
            else:
                row += " & —"
        lines.append(row + " \\\\")

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])

    tex = "\n".join(lines)
    (TABLES_DIR / "table2_baseline.tex").write_text(tex)
    print(f"  Table 2 saved ({len(models)} models × {len(active_conds)} conditions)")
    return tex


def table3_ablation(results=None):
    """Table 3: Ablation Results"""
    if results is None:
        results = load_results()

    conditions = ["exact_skill", "code_only", "text_only", "pitfalls_only",
                  "workflow_only", "self_skill", "vaccinated"]
    cond_display = {
        "exact_skill": "Full Skill", "code_only": "Code Only",
        "text_only": "Text Only", "pitfalls_only": "Pitfalls",
        "workflow_only": "Workflow", "self_skill": "Self-Skill",
        "vaccinated": "Vaccinated",
    }

    data = defaultdict(lambda: defaultdict(list))
    for r in results:
        m, c = r.get("model",""), r.get("condition","")
        if c in conditions:
            pr = r.get("eval", {}).get("pass_rate", 0)
            data[m][c].append(pr)

    models = sorted(data.keys())
    active_conds = [c for c in conditions if any(c in data[m] for m in models)]

    if not active_conds:
        print("  Table 3 skipped (no ablation data)")
        return ""

    col_spec = "l" + "c" * len(active_conds)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Ablation Study: Mean Pass Rate (\\%) for different skill components.}",
        "\\label{tab:ablation}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\toprule",
    ]

    header = "Model & " + " & ".join(cond_display.get(c, c) for c in active_conds) + " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    for m in models:
        row = MODEL_DISPLAY.get(m, m)
        for c in active_conds:
            vals = data[m].get(c, [])
            if vals:
                mean = np.mean(vals)
                row += f" & {mean:.0%}"
            else:
                row += " & —"
        lines.append(row + " \\\\")

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])

    tex = "\n".join(lines)
    (TABLES_DIR / "table3_ablation.tex").write_text(tex)
    print(f"  Table 3 saved ({len(models)} models × {len(active_conds)} conditions)")
    return tex


def generate_all_tables():
    """生成所有 LaTeX 表格"""
    print("=" * 70)
    print("Generating LaTeX tables...")
    print("=" * 70)
    results = load_results()
    print(f"Loaded {len(results)} results")

    table1_main_results(results)
    table2_baseline_comparison(results)
    table3_ablation(results)
    print(f"\nAll tables saved to {TABLES_DIR}/")


if __name__ == "__main__":
    generate_all_tables()
