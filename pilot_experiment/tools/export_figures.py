#!/usr/bin/env python3
"""
可视化工具：从 experiment_results.jsonl 生成论文图表。

图表:
1. RQ1 热力图: completeness_level × model, 颜色 = pass_rate
2. RQ2 error×model 矩阵: mutation_type × model, 值 = Δpass_rate
3. RQ3 失败模式分布: 堆积柱状图
4. RQ4 相关性散点图: 24-point score ↔ pass_rate

用法:
    python tools/export_figures.py [--input results/experiment_results.jsonl] [--output results/analysis/]
"""
import sys
import os
import json
import argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np


def load_results(path: Path) -> list[dict]:
    """加载 JSONL 结果"""
    results = []
    for line in path.read_text().strip().split("\n"):
        if line:
            results.append(json.loads(line))
    return results


def fig_rq1_heatmap(results: list[dict], output_dir: Path):
    """RQ1: 完整度级别 × 模型热力图"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按 (model, skill_level) 聚合 pass_rate
    data = defaultdict(list)
    for r in results:
        tc = r.get("trial_config", {})
        if not tc.get("skill_level"):
            continue
        key = (tc["model"], tc["skill_level"])
        pr = r.get("eval", {}).get("pass_rate", 0)
        data[key].append(pr)

    if not data:
        print("  RQ1: 无数据，跳过")
        return

    models = sorted(set(k[0] for k in data))
    levels = ["L0_none", "L1_skill_md", "L2_plus_scripts", "L3_no_assets", "L4_full"]
    levels = [l for l in levels if any((m, l) in data for m in models)]

    matrix = np.zeros((len(models), len(levels)))
    for i, m in enumerate(models):
        for j, l in enumerate(levels):
            vals = data.get((m, l), [])
            matrix[i, j] = np.mean(vals) if vals else 0

    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([l.replace("_", "\n") for l in levels], fontsize=9)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models)

    # 标注数值
    for i in range(len(models)):
        for j in range(len(levels)):
            ax.text(j, i, f"{matrix[i,j]:.0%}", ha="center", va="center",
                    color="white" if matrix[i,j] < 0.3 or matrix[i,j] > 0.7 else "black",
                    fontsize=10, fontweight="bold")

    plt.colorbar(im, label="Pass Rate")
    ax.set_title("RQ1: Skill Completeness Level × Model")
    ax.set_xlabel("Completeness Level")
    ax.set_ylabel("Model")
    plt.tight_layout()
    plt.savefig(output_dir / "rq1_heatmap.pdf", dpi=300)
    plt.savefig(output_dir / "rq1_heatmap.png", dpi=150)
    plt.close()
    print("  ✓ rq1_heatmap.pdf")


def fig_rq2_matrix(results: list[dict], output_dir: Path):
    """RQ2: error_type × model 矩阵"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 提取 clean baseline 和 mutated 的 pass_rate
    clean = defaultdict(list)
    mutated = defaultdict(lambda: defaultdict(list))

    for r in results:
        tc = r.get("trial_config", {})
        if tc.get("mutation_type") == "none" and "clean" in tc.get("condition", ""):
            key = (tc["scenario_id"], tc["model"])
            clean[key].append(r.get("eval", {}).get("pass_rate", 0))
        elif tc.get("mutation_type", "none") != "none":
            key = (tc["scenario_id"], tc["model"])
            mutated[tc["mutation_type"]][key].append(r.get("eval", {}).get("pass_rate", 0))

    if not mutated:
        print("  RQ2: 无数据，跳过")
        return

    models = sorted(set(k[1] for k in clean))
    mut_types = sorted(mutated.keys())

    delta_matrix = np.zeros((len(mut_types), len(models)))
    for i, mt in enumerate(mut_types):
        for j, m in enumerate(models):
            deltas = []
            for key in clean:
                if key[1] == m and key in mutated[mt]:
                    c_mean = np.mean(clean[key])
                    m_mean = np.mean(mutated[mt][key])
                    deltas.append(m_mean - c_mean)
            delta_matrix[i, j] = np.mean(deltas) if deltas else 0

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(delta_matrix, cmap="RdBu", vmin=-0.5, vmax=0.5, aspect="auto")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models)
    ax.set_yticks(range(len(mut_types)))
    ax.set_yticklabels(mut_types)

    for i in range(len(mut_types)):
        for j in range(len(models)):
            val = delta_matrix[i, j]
            ax.text(j, i, f"{val:+.0%}", ha="center", va="center",
                    color="white" if abs(val) > 0.25 else "black", fontsize=10)

    plt.colorbar(im, label="Δ Pass Rate (mutated - clean)")
    ax.set_title("RQ2: Error Tolerance — Mutation Type × Model")
    plt.tight_layout()
    plt.savefig(output_dir / "rq2_error_matrix.pdf", dpi=300)
    plt.savefig(output_dir / "rq2_error_matrix.png", dpi=150)
    plt.close()
    print("  ✓ rq2_error_matrix.pdf")


def fig_rq3_failure(results: list[dict], output_dir: Path):
    """RQ3: 失败模式分布（堆积柱状图）"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 统计每个 condition 的 error_type 分布
    counts = defaultdict(lambda: defaultdict(int))
    for r in results:
        tc = r.get("trial_config", {})
        cond = tc.get("condition", "unknown")
        if not cond.startswith("rq3_"):
            continue
        error_type = r.get("eval", {}).get("error_type", "unknown")
        counts[cond][error_type] += 1

    if not counts:
        print("  RQ3: 无数据，跳过")
        return

    conditions = sorted(counts.keys())
    error_types = sorted(set(et for c in counts.values() for et in c))

    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(conditions))
    bottom = np.zeros(len(conditions))

    colors = plt.cm.Set3(np.linspace(0, 1, len(error_types)))
    for i, et in enumerate(error_types):
        heights = [counts[c].get(et, 0) for c in conditions]
        ax.bar(x, heights, bottom=bottom, label=et, color=colors[i])
        bottom += heights

    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("rq3_", "") for c in conditions], rotation=30)
    ax.set_ylabel("Count")
    ax.set_title("RQ3: Error Type Distribution by Condition")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_dir / "rq3_failure_modes.pdf", dpi=300)
    plt.savefig(output_dir / "rq3_failure_modes.png", dpi=150)
    plt.close()
    print("  ✓ rq3_failure_modes.pdf")


def fig_rq4_correlation(results: list[dict], quality_scores_path: Path, output_dir: Path):
    """RQ4: 24-point score ↔ runtime pass_rate 相关性"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not quality_scores_path.exists():
        print("  RQ4: 无 quality_scores，跳过")
        return

    quality = json.loads(quality_scores_path.read_text())
    # quality 格式: {scenario_id: {method: {total: N, ...}}}
    # 匹配 results 中的 pass_rate

    xs, ys, labels = [], [], []
    for r in results:
        tc = r.get("trial_config", {})
        sid = tc.get("scenario_id", "")
        method = tc.get("skill_method", "")
        pr = r.get("eval", {}).get("pass_rate", 0)

        if sid in quality and method in quality[sid]:
            score = quality[sid][method].get("total", 0)
            xs.append(score)
            ys.append(pr)
            labels.append(f"{sid}/{method}")

    if not xs:
        print("  RQ4: 无匹配数据，跳过")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(xs, ys, alpha=0.6, s=40)

    # 回归线
    if len(xs) > 2:
        z = np.polyfit(xs, ys, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(xs), max(xs), 100)
        ax.plot(x_line, p(x_line), "r--", alpha=0.7,
                label=f"r={np.corrcoef(xs, ys)[0,1]:.3f}")
        ax.legend()

    ax.set_xlabel("Skill Quality Score (24-point rubric)")
    ax.set_ylabel("Runtime Pass Rate")
    ax.set_title("RQ4: Skill Quality vs. Task Performance")
    plt.tight_layout()
    plt.savefig(output_dir / "rq4_correlation.pdf", dpi=300)
    plt.savefig(output_dir / "rq4_correlation.png", dpi=150)
    plt.close()
    print("  ✓ rq4_correlation.pdf")


def main():
    parser = argparse.ArgumentParser(description="生成论文图表")
    parser.add_argument("--input", default=str(ROOT / "results" / "experiment_results.jsonl"))
    parser.add_argument("--output", default=str(ROOT / "results" / "analysis"))
    parser.add_argument("--quality-scores", default=str(ROOT / "results" / "quality_scores.json"))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"结果文件不存在: {input_path}")
        return 1

    results = load_results(input_path)
    print(f"加载 {len(results)} 条结果")

    fig_rq1_heatmap(results, output_dir)
    fig_rq2_matrix(results, output_dir)
    fig_rq3_failure(results, output_dir)
    fig_rq4_correlation(results, Path(args.quality_scores), output_dir)

    print(f"\n图表已保存到: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
