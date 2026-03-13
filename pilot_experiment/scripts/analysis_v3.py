#!/usr/bin/env python3
"""
分析与可视化 v3 — 生成论文图表
Figure 1: Skill Effect Heatmap（模型 × 场景，红绿色编码 Δpass_rate）
Figure 2: Error Taxonomy 堆叠柱状图（error_type 分布 per model）
Figure 3: Baseline Comparison 柱状图（no_skill, cot, few_shot, doc, skill, human_skill）
Figure 4: Self-skill vs Exact-skill 散点图
Figure 5: Vaccination Before/After 对比
Figure 6: Code vs Text 消融分组柱状图
Figure 7: SCORE 连续指标 box plot
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent))
from config import RESULTS_DIR, ROOT

FIGURES_DIR = ROOT / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# 颜色方案
MODEL_COLORS = {
    "haiku": "#4CAF50", "sonnet": "#2196F3", "opus": "#9C27B0",
    "gpt4o": "#FF9800", "gpt4o_mini": "#FFCC80", "gpt41": "#F44336",
    "gpt41_mini": "#EF9A9A", "gemini_pro": "#009688", "gemini_flash": "#80CBC4",
}

SCENARIO_SHORT = {
    "S01_neuro_metadata": "S01", "S02_spike_behavior": "S02",
    "S03_spatial_tx": "S03", "S04_satellite": "S04",
    "S05_protein_parse": "S05", "S06_gene_expression": "S06",
    "S07_data_viz": "S07", "S08_materials_qa": "S08",
    "S09_earth_obs": "S09", "S10_multimodal": "S10",
}


def load_results(filename="re_evaluated_results.json"):
    path = RESULTS_DIR / filename
    if path.exists():
        return json.loads(path.read_text())
    # 回退到主结果
    path = RESULTS_DIR / "experiment_v2_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return []


def figure1_skill_effect_heatmap(results=None):
    """Figure 1: Skill Effect Heatmap — Δpass_rate (exact_skill - no_skill)"""
    if results is None:
        results = load_results()

    # 收集 pass_rate
    data = {}
    for r in results:
        s = r.get("scenario", "")
        m = r.get("model", "")
        c = r.get("condition", "")
        pr = r.get("eval", {}).get("pass_rate", 0)
        data[(s, m, c)] = pr

    scenarios = sorted(set(s for s, m, c in data.keys()))
    models = sorted(set(m for s, m, c in data.keys()))

    # 计算 Δ
    matrix = np.full((len(models), len(scenarios)), np.nan)
    for i, m in enumerate(models):
        for j, s in enumerate(scenarios):
            no = data.get((s, m, "no_skill"), None)
            ex = data.get((s, m, "exact_skill"), None)
            if no is not None and ex is not None:
                matrix[i, j] = ex - no

    fig, ax = plt.subplots(figsize=(12, 6))
    cmap = mcolors.LinearSegmentedColormap.from_list("rg", ["#d32f2f", "#ffffff", "#388e3c"])
    im = ax.imshow(matrix, cmap=cmap, vmin=-0.5, vmax=0.5, aspect="auto")

    ax.set_xticks(range(len(scenarios)))
    ax.set_xticklabels([SCENARIO_SHORT.get(s, s) for s in scenarios], rotation=45, ha="right")
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)

    # 标注数值
    for i in range(len(models)):
        for j in range(len(scenarios)):
            val = matrix[i, j]
            if not np.isnan(val):
                color = "white" if abs(val) > 0.3 else "black"
                ax.text(j, i, f"{val:+.0%}", ha="center", va="center", color=color, fontsize=8)

    plt.colorbar(im, label="Δ Pass Rate (exact_skill − no_skill)")
    ax.set_title("Figure 1: Skill Effect Heatmap")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig1_skill_effect_heatmap.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig1_skill_effect_heatmap.png", dpi=150)
    plt.close(fig)
    print("  Figure 1 saved")


def figure2_error_taxonomy(results=None):
    """Figure 2: Error Taxonomy 堆叠柱状图"""
    if results is None:
        results = load_results()

    error_counts = defaultdict(lambda: defaultdict(int))
    for r in results:
        m = r.get("model", "unknown")
        et = r.get("eval", {}).get("error_type", "unknown")
        error_counts[m][et] += 1

    models = sorted(error_counts.keys())
    error_types = ["success", "logic_error", "runtime_error", "syntax_error",
                   "import_error", "timeout", "format_error"]
    colors = ["#4CAF50", "#FF9800", "#F44336", "#9C27B0", "#2196F3", "#607D8B", "#795548"]

    fig, ax = plt.subplots(figsize=(10, 6))
    bottom = np.zeros(len(models))
    for et, color in zip(error_types, colors):
        vals = [error_counts[m].get(et, 0) for m in models]
        ax.bar(models, vals, bottom=bottom, label=et, color=color)
        bottom += vals

    ax.set_ylabel("Number of Runs")
    ax.set_title("Figure 2: Error Type Distribution by Model")
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig2_error_taxonomy.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig2_error_taxonomy.png", dpi=150)
    plt.close(fig)
    print("  Figure 2 saved")


def figure3_baseline_comparison(results=None):
    """Figure 3: Baseline Comparison 柱状图"""
    if results is None:
        results = load_results()

    conditions = ["no_skill", "cot", "few_shot_1", "few_shot_3", "doc_only",
                  "exact_skill", "human_expert_skill"]
    # 按 condition 收集 mean pass_rate
    cond_rates = defaultdict(list)
    for r in results:
        c = r.get("condition", "")
        if c in conditions:
            pr = r.get("eval", {}).get("pass_rate", 0)
            cond_rates[c].append(pr)

    # 只画有数据的条件
    active_conds = [c for c in conditions if c in cond_rates]
    means = [np.mean(cond_rates[c]) for c in active_conds]
    stds = [np.std(cond_rates[c]) / max(np.sqrt(len(cond_rates[c])), 1) for c in active_conds]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.Set2(np.linspace(0, 1, len(active_conds)))
    bars = ax.bar(active_conds, means, yerr=stds, capsize=3, color=colors)
    ax.set_ylabel("Mean Pass Rate")
    ax.set_title("Figure 3: Baseline Comparison")
    ax.set_ylim(0, 1.05)
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{m:.0%}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig3_baseline_comparison.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig3_baseline_comparison.png", dpi=150)
    plt.close(fig)
    print("  Figure 3 saved")


def figure4_self_skill_scatter(results=None):
    """Figure 4: Self-skill vs Exact-skill 散点图"""
    if results is None:
        results = load_results()

    data = {}
    for r in results:
        s, m, c = r.get("scenario",""), r.get("model",""), r.get("condition","")
        pr = r.get("eval", {}).get("pass_rate", 0)
        data[(s, m, c)] = pr

    x_vals, y_vals, labels = [], [], []
    for (s, m, c), pr in data.items():
        if c == "exact_skill":
            self_pr = data.get((s, m, "self_skill"), None)
            if self_pr is not None:
                x_vals.append(pr)
                y_vals.append(self_pr)
                labels.append(m)

    if not x_vals:
        print("  Figure 4 skipped (no self-skill data)")
        return

    fig, ax = plt.subplots(figsize=(7, 7))
    for m in set(labels):
        mask = [l == m for l in labels]
        mx = [x for x, b in zip(x_vals, mask) if b]
        my = [y for y, b in zip(y_vals, mask) if b]
        ax.scatter(mx, my, label=m, color=MODEL_COLORS.get(m, "#333"), s=60, alpha=0.7)

    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="y=x")
    ax.set_xlabel("Exact Skill Pass Rate")
    ax.set_ylabel("Self-Skill Pass Rate")
    ax.set_title("Figure 4: Self-Skill vs Exact-Skill")
    ax.legend()
    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig4_self_skill_scatter.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig4_self_skill_scatter.png", dpi=150)
    plt.close(fig)
    print("  Figure 4 saved")


def figure5_vaccination(results=None):
    """Figure 5: Vaccination Before/After 对比"""
    if results is None:
        results = load_results()

    data = defaultdict(lambda: {})
    for r in results:
        s, m, c = r.get("scenario",""), r.get("model",""), r.get("condition","")
        pr = r.get("eval", {}).get("pass_rate", 0)
        if c in ("exact_skill", "vaccinated"):
            data[(s, m)][c] = pr

    pairs = [(k, v) for k, v in data.items() if "exact_skill" in v and "vaccinated" in v]
    if not pairs:
        print("  Figure 5 skipped (no vaccination data)")
        return

    fig, ax = plt.subplots(figsize=(10, 6))
    scenarios = sorted(set(k[0] for k, v in pairs))
    models = sorted(set(k[1] for k, v in pairs))

    x = np.arange(len(scenarios))
    width = 0.35
    for i, m in enumerate(models):
        before = [data.get((s, m), {}).get("exact_skill", 0) for s in scenarios]
        after = [data.get((s, m), {}).get("vaccinated", 0) for s in scenarios]
        offset = (i - len(models)/2 + 0.5) * width / len(models) * 2
        ax.bar(x + offset - width/4, before, width/len(models), label=f"{m} (before)", alpha=0.6,
               color=MODEL_COLORS.get(m, "#333"))
        ax.bar(x + offset + width/4, after, width/len(models), label=f"{m} (after)", alpha=0.9,
               color=MODEL_COLORS.get(m, "#333"), hatch="//")

    ax.set_xticks(x)
    ax.set_xticklabels([SCENARIO_SHORT.get(s, s) for s in scenarios], rotation=45)
    ax.set_ylabel("Pass Rate")
    ax.set_title("Figure 5: Vaccination Effect (Before vs After)")
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig5_vaccination.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig5_vaccination.png", dpi=150)
    plt.close(fig)
    print("  Figure 5 saved")


def figure6_code_text_ablation(results=None):
    """Figure 6: Code vs Text 消融分组柱状图"""
    if results is None:
        results = load_results()

    conditions = ["code_only", "text_only", "pitfalls_only", "workflow_only"]
    cond_model_rates = defaultdict(lambda: defaultdict(list))
    for r in results:
        c = r.get("condition", "")
        m = r.get("model", "")
        if c in conditions:
            pr = r.get("eval", {}).get("pass_rate", 0)
            cond_model_rates[c][m].append(pr)

    if not any(cond_model_rates.values()):
        print("  Figure 6 skipped (no code/text ablation data)")
        return

    active_conds = [c for c in conditions if c in cond_model_rates]
    models = sorted(set(m for rates in cond_model_rates.values() for m in rates))

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(active_conds))
    n_models = len(models)
    width = 0.8 / max(n_models, 1)

    for i, m in enumerate(models):
        means = [np.mean(cond_model_rates[c].get(m, [0])) for c in active_conds]
        offset = (i - n_models/2 + 0.5) * width
        ax.bar(x + offset, means, width, label=m, color=MODEL_COLORS.get(m, "#333"))

    ax.set_xticks(x)
    ax.set_xticklabels(active_conds, rotation=30)
    ax.set_ylabel("Pass Rate")
    ax.set_title("Figure 6: Code vs Text Ablation")
    ax.legend()
    ax.set_ylim(0, 1.05)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig6_code_text_ablation.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig6_code_text_ablation.png", dpi=150)
    plt.close(fig)
    print("  Figure 6 saved")


def figure7_score_boxplot(results=None):
    """Figure 7: SCORE 连续指标 box plot"""
    if results is None:
        results = load_results()

    # 收集所有 SCORE 指标
    score_data = defaultdict(lambda: defaultdict(list))
    for r in results:
        c = r.get("condition", "")
        scores = r.get("eval", {}).get("scores", {})
        for metric, val in scores.items():
            if isinstance(val, (int, float)):
                score_data[metric][c].append(val)

    if not score_data:
        print("  Figure 7 skipped (no SCORE data)")
        return

    metrics = sorted(score_data.keys())
    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, min(n_metrics, 6), figsize=(4 * min(n_metrics, 6), 5),
                              squeeze=False)

    for idx, metric in enumerate(metrics[:6]):
        ax = axes[0][idx]
        conds = sorted(score_data[metric].keys())
        data_list = [score_data[metric][c] for c in conds]
        bp = ax.boxplot(data_list, labels=conds, patch_artist=True)
        for patch in bp["boxes"]:
            patch.set_facecolor("#81D4FA")
        ax.set_title(metric, fontsize=9)
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        ax.set_ylim(-0.05, 1.1)

    fig.suptitle("Figure 7: Continuous SCORE Metrics Distribution", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig7_score_boxplot.pdf", dpi=150)
    fig.savefig(FIGURES_DIR / "fig7_score_boxplot.png", dpi=150)
    plt.close(fig)
    print("  Figure 7 saved")


def generate_all():
    """生成所有图表"""
    print("=" * 70)
    print("Generating figures...")
    print("=" * 70)
    results = load_results()
    if not results:
        print("WARNING: No results found. Trying experiment_v2_results.json...")
        results = load_results("experiment_v2_results.json")

    print(f"Loaded {len(results)} results")
    figure1_skill_effect_heatmap(results)
    figure2_error_taxonomy(results)
    figure3_baseline_comparison(results)
    figure4_self_skill_scatter(results)
    figure5_vaccination(results)
    figure6_code_text_ablation(results)
    figure7_score_boxplot(results)
    print(f"\nAll figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    generate_all()
