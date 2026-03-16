#!/usr/bin/env python3
"""
Step 4: 分析与可视化。
从 experiment_results.jsonl 读取结果，生成 4-5 张图表 + 统计结论。

用法:
    python analysis/generate_figures.py
"""
import json
import csv
import sys
from pathlib import Path
from collections import defaultdict

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "data" / "experiment_results.jsonl"
SCORES_FILE = PROJECT_ROOT / "data" / "skill_scores.csv"
FIGURES_DIR = PROJECT_ROOT / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)


def load_results():
    """加载实验结果"""
    results = []
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line:
            results.append(json.loads(line))
    return results


def load_scores():
    """加载 skill 评分"""
    scores = {}
    if not SCORES_FILE.exists():
        return scores
    with open(SCORES_FILE) as f:
        reader = csv.DictReader(f)
        for row in reader:
            scores[row["scenario_id"]] = {
                "score": int(row["score"]),
                "max_score": int(row["max_score"]),
                "domain": row["domain"],
            }
    return scores


def figure1_domain_heatmap(results):
    """图 1: 域内提升热力图 — domain × model → Δpass_rate"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按 (domain, model, condition) 聚合 pass_rate
    agg = defaultdict(list)
    for r in results:
        domain = r.get("domain", "unknown")
        model = r["trial"]["model"]
        condition = r["trial"]["condition"]
        pr = r["eval"]["pass_rate"]
        agg[(domain, model, condition)].append(pr)

    # 计算 Δ = L4 - L0
    domains = sorted(set(d for d, _, _ in agg.keys()))
    models = sorted(set(m for _, m, _ in agg.keys()))

    delta = np.zeros((len(domains), len(models)))
    for i, d in enumerate(domains):
        for j, m in enumerate(models):
            l0 = agg.get((d, m, "L0_none"), [])
            l4 = agg.get((d, m, "L4_full"), [])
            l0_mean = np.mean(l0) if l0 else 0
            l4_mean = np.mean(l4) if l4 else 0
            delta[i, j] = l4_mean - l0_mean

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(delta, cmap="RdYlGn", vmin=-0.5, vmax=0.5, aspect="auto")

    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=45, ha="right")
    ax.set_yticks(range(len(domains)))
    ax.set_yticklabels(domains)

    # 标注数值
    for i in range(len(domains)):
        for j in range(len(models)):
            val = delta[i, j]
            color = "white" if abs(val) > 0.3 else "black"
            ax.text(j, i, f"{val:+.2f}", ha="center", va="center", color=color, fontsize=9)

    ax.set_title("Skill Impact: Pass Rate Change (L4 - L0) by Domain × Model", fontsize=13)
    ax.set_xlabel("Model")
    ax.set_ylabel("Domain")
    plt.colorbar(im, ax=ax, label="Δ Pass Rate")
    plt.tight_layout()
    path = FIGURES_DIR / "domain_heatmap.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")
    return delta, domains, models


def figure2_quality_vs_effect(results, scores):
    """图 2: Skill 质量 vs 实际提升散点图"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按 scenario 计算 L4-L0 平均提升
    by_scenario = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        sid = r["trial"]["scenario_id"]
        cond = r["trial"]["condition"]
        pr = r["eval"]["pass_rate"]
        if cond == "L0_none":
            by_scenario[sid]["L0"].append(pr)
        elif cond == "L4_full":
            by_scenario[sid]["L4"].append(pr)

    x_scores = []
    y_deltas = []
    labels = []
    colors = []

    # 领域颜色
    domain_colors = {
        "earth_science": "#8B4513", "biology": "#228B22", "physics": "#4169E1",
        "chemistry": "#FF6347", "astronomy": "#9370DB", "engineering": "#FF8C00",
        "environmental": "#2E8B57", "medical": "#DC143C", "social_science": "#DAA520",
        "neuroscience": "#FF69B4", "ecology": "#32CD32", "oceanography": "#00CED1",
        "atmospheric": "#87CEEB", "materials": "#A0522D",
    }

    for sid, data in by_scenario.items():
        if data["L0"] and data["L4"] and sid in scores:
            l0_mean = np.mean(data["L0"])
            l4_mean = np.mean(data["L4"])
            delta = l4_mean - l0_mean
            score = scores[sid]["score"]
            domain = scores[sid]["domain"]
            x_scores.append(score)
            y_deltas.append(delta)
            labels.append(sid)
            colors.append(domain_colors.get(domain, "#808080"))

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(x_scores, y_deltas, c=colors, s=80, alpha=0.7, edgecolors="black", linewidth=0.5)

    # 标注极值
    if y_deltas:
        for i in range(len(labels)):
            if y_deltas[i] > 0.3 or y_deltas[i] < -0.2:
                ax.annotate(labels[i].replace("S0", "S"), (x_scores[i], y_deltas[i]),
                           fontsize=7, alpha=0.8)

    ax.axhline(y=0, color="gray", linestyle="--", alpha=0.5)
    ax.set_xlabel("Skill Quality Score (out of 24)", fontsize=12)
    ax.set_ylabel("Δ Pass Rate (L4 - L0)", fontsize=12)
    ax.set_title("Skill Quality vs Actual Effectiveness", fontsize=13)

    # 简易图例
    used_domains = set()
    for sid in labels:
        if sid in scores:
            used_domains.add(scores[sid]["domain"])
    legend_handles = []
    for d in sorted(used_domains):
        c = domain_colors.get(d, "#808080")
        h = plt.scatter([], [], c=c, s=50, label=d)
        legend_handles.append(h)
    ax.legend(handles=legend_handles, loc="upper left", fontsize=8, ncol=2)

    plt.tight_layout()
    path = FIGURES_DIR / "quality_vs_effect.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def figure3_model_response(results):
    """图 3: 模型响应曲线 — 不同模型对 skill 的响应"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按模型聚合
    by_model = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        model = r["trial"]["model"]
        cond = r["trial"]["condition"]
        pr = r["eval"]["pass_rate"]
        if cond == "L0_none":
            by_model[model]["L0"].append(pr)
        elif cond == "L4_full":
            by_model[model]["L4"].append(pr)

    models = sorted(by_model.keys())
    l0_means = [np.mean(by_model[m]["L0"]) if by_model[m]["L0"] else 0 for m in models]
    l4_means = [np.mean(by_model[m]["L4"]) if by_model[m]["L4"] else 0 for m in models]
    l0_stds = [np.std(by_model[m]["L0"]) if len(by_model[m]["L0"]) > 1 else 0 for m in models]
    l4_stds = [np.std(by_model[m]["L4"]) if len(by_model[m]["L4"]) > 1 else 0 for m in models]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width/2, l0_means, width, label="L0 (No Skill)",
                   color="#E74C3C", alpha=0.8, yerr=l0_stds, capsize=4)
    bars2 = ax.bar(x + width/2, l4_means, width, label="L4 (Full Skill)",
                   color="#2ECC71", alpha=0.8, yerr=l4_stds, capsize=4)

    # 标注提升
    for i, m in enumerate(models):
        delta = l4_means[i] - l0_means[i]
        color = "#27AE60" if delta > 0 else "#C0392B"
        ax.annotate(f"{delta:+.1%}", xy=(i + width/2, l4_means[i]),
                   xytext=(0, 8), textcoords="offset points",
                   ha="center", fontsize=10, fontweight="bold", color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11)
    ax.set_ylabel("Average Pass Rate", fontsize=12)
    ax.set_title("Model Response to Skill Injection (L0 vs L4)", fontsize=13)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = FIGURES_DIR / "model_response.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"  Saved: {path}")


def figure4_domain_difficulty(results):
    """图 4: 领域难度分布 — baseline pass_rate + skill 提升"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按 domain 聚合
    by_domain = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        domain = r.get("domain", "unknown")
        cond = r["trial"]["condition"]
        pr = r["eval"]["pass_rate"]
        if cond == "L0_none":
            by_domain[domain]["L0"].append(pr)
        elif cond == "L4_full":
            by_domain[domain]["L4"].append(pr)

    domains = sorted(by_domain.keys())
    l0_means = [np.mean(by_domain[d]["L0"]) if by_domain[d]["L0"] else 0 for d in domains]
    l4_means = [np.mean(by_domain[d]["L4"]) if by_domain[d]["L4"] else 0 for d in domains]
    deltas = [l4 - l0 for l0, l4 in zip(l0_means, l4_means)]

    # 按 baseline 排序
    order = np.argsort(l0_means)
    domains = [domains[i] for i in order]
    l0_means = [l0_means[i] for i in order]
    l4_means = [l4_means[i] for i in order]
    deltas = [deltas[i] for i in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7))

    # 左图: baseline + with skill
    y = range(len(domains))
    ax1.barh(y, l0_means, height=0.4, label="L0 (Baseline)", color="#E74C3C", alpha=0.7, align="edge")
    ax1.barh([yi + 0.4 for yi in y], l4_means, height=0.4, label="L4 (With Skill)",
             color="#2ECC71", alpha=0.7, align="edge")
    ax1.set_yticks([yi + 0.4 for yi in y])
    ax1.set_yticklabels(domains, fontsize=10)
    ax1.set_xlabel("Average Pass Rate")
    ax1.set_title("Baseline vs Skill-Augmented")
    ax1.legend(fontsize=10)
    ax1.set_xlim(0, 1.05)

    # 右图: 提升柱状图
    colors = ["#2ECC71" if d > 0 else "#E74C3C" for d in deltas]
    ax2.barh(y, deltas, color=colors, alpha=0.8)
    ax2.set_yticks(y)
    ax2.set_yticklabels(domains, fontsize=10)
    ax2.axvline(x=0, color="gray", linestyle="--")
    ax2.set_xlabel("Δ Pass Rate (L4 - L0)")
    ax2.set_title("Skill Impact by Domain")

    plt.suptitle("Domain Difficulty Distribution", fontsize=14, y=1.02)
    plt.tight_layout()
    path = FIGURES_DIR / "domain_difficulty.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def figure5_case_analysis(results):
    """图 5: Top-5 提升 vs 下降案例"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 按 scenario 计算平均提升
    by_scenario = defaultdict(lambda: {"L0": [], "L4": [], "domain": ""})
    for r in results:
        sid = r["trial"]["scenario_id"]
        cond = r["trial"]["condition"]
        pr = r["eval"]["pass_rate"]
        by_scenario[sid]["domain"] = r.get("domain", "")
        if cond == "L0_none":
            by_scenario[sid]["L0"].append(pr)
        elif cond == "L4_full":
            by_scenario[sid]["L4"].append(pr)

    deltas = []
    for sid, data in by_scenario.items():
        if data["L0"] and data["L4"]:
            l0 = np.mean(data["L0"])
            l4 = np.mean(data["L4"])
            deltas.append((sid, l4 - l0, l0, l4, data["domain"]))

    deltas.sort(key=lambda x: x[1], reverse=True)

    top5 = deltas[:5]
    bottom5 = deltas[-5:]
    cases = top5 + list(reversed(bottom5))

    fig, ax = plt.subplots(figsize=(12, 6))

    labels = [f"{c[0]}\n({c[4]})" for c in cases]
    values = [c[1] for c in cases]
    colors = ["#2ECC71" if v > 0 else "#E74C3C" for v in values]

    bars = ax.barh(range(len(cases)), values, color=colors, alpha=0.8)

    # 标注具体数值
    for i, (bar, val) in enumerate(zip(bars, values)):
        l0, l4 = cases[i][2], cases[i][3]
        ax.text(val + (0.01 if val > 0 else -0.01), i,
               f"{val:+.1%} ({l0:.0%}→{l4:.0%})",
               va="center", ha="left" if val > 0 else "right", fontsize=9)

    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels(labels, fontsize=9)
    ax.axvline(x=0, color="gray", linestyle="--")
    ax.set_xlabel("Δ Pass Rate")
    ax.set_title("Top-5 Improved vs Top-5 Declined Scenarios", fontsize=13)

    # 分隔线
    ax.axhline(y=4.5, color="gray", linestyle=":", alpha=0.5)
    ax.text(-0.05, 2, "Most Improved →", transform=ax.get_yaxis_transform(),
           fontsize=10, color="#27AE60", va="center", ha="right")
    ax.text(-0.05, 7, "← Most Declined", transform=ax.get_yaxis_transform(),
           fontsize=10, color="#C0392B", va="center", ha="right")

    plt.tight_layout()
    path = FIGURES_DIR / "case_analysis.png"
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def generate_stats_summary(results, scores):
    """生成统计摘要"""
    # 总体统计
    l0_results = [r for r in results if r["trial"]["condition"] == "L0_none"]
    l4_results = [r for r in results if r["trial"]["condition"] == "L4_full"]

    l0_rates = [r["eval"]["pass_rate"] for r in l0_results]
    l4_rates = [r["eval"]["pass_rate"] for r in l4_results]

    summary = {
        "total_trials": len(results),
        "l0_trials": len(l0_results),
        "l4_trials": len(l4_results),
        "l0_mean_pass_rate": round(np.mean(l0_rates), 4) if l0_rates else 0,
        "l4_mean_pass_rate": round(np.mean(l4_rates), 4) if l4_rates else 0,
        "overall_delta": round(np.mean(l4_rates) - np.mean(l0_rates), 4) if l0_rates and l4_rates else 0,
        "l0_std": round(np.std(l0_rates), 4) if l0_rates else 0,
        "l4_std": round(np.std(l4_rates), 4) if l4_rates else 0,
    }

    # 按模型统计
    by_model = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        model = r["trial"]["model"]
        cond = r["trial"]["condition"]
        by_model[model][cond.split("_")[0]].append(r["eval"]["pass_rate"])

    summary["by_model"] = {}
    for model, data in sorted(by_model.items()):
        l0 = np.mean(data["L0"]) if data["L0"] else 0
        l4 = np.mean(data["L4"]) if data["L4"] else 0
        summary["by_model"][model] = {
            "l0_mean": round(l0, 4),
            "l4_mean": round(l4, 4),
            "delta": round(l4 - l0, 4),
            "n_l0": len(data["L0"]),
            "n_l4": len(data["L4"]),
        }

    # 按领域统计
    by_domain = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        domain = r.get("domain", "unknown")
        cond = r["trial"]["condition"]
        by_domain[domain][cond.split("_")[0]].append(r["eval"]["pass_rate"])

    summary["by_domain"] = {}
    for domain, data in sorted(by_domain.items()):
        l0 = np.mean(data["L0"]) if data["L0"] else 0
        l4 = np.mean(data["L4"]) if data["L4"] else 0
        summary["by_domain"][domain] = {
            "l0_mean": round(l0, 4),
            "l4_mean": round(l4, 4),
            "delta": round(l4 - l0, 4),
        }

    # 成本统计
    total_cost = sum(r.get("cost_usd", 0) for r in results)
    summary["total_cost_usd"] = round(total_cost, 4)

    return summary


def main():
    print("加载数据...")
    if not RESULTS_FILE.exists():
        print(f"ERROR: {RESULTS_FILE} not found")
        sys.exit(1)

    results = load_results()
    scores = load_scores()
    print(f"  实验结果: {len(results)} trials")
    print(f"  Skill 评分: {len(scores)} skills")

    # 生成统计摘要
    print("\n生成统计摘要...")
    summary = generate_stats_summary(results, scores)
    summary_path = PROJECT_ROOT / "data" / "stats_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"  Saved: {summary_path}")

    # 打印关键发现
    print(f"\n{'='*60}")
    print("KEY FINDINGS")
    print(f"{'='*60}")
    print(f"  Overall: L0={summary['l0_mean_pass_rate']:.1%} → L4={summary['l4_mean_pass_rate']:.1%} "
          f"(Δ={summary['overall_delta']:+.1%})")
    print(f"  Total cost: ${summary['total_cost_usd']:.2f}")
    print()

    if summary.get("by_model"):
        print("  By Model:")
        for model, data in summary["by_model"].items():
            print(f"    {model:15s}: L0={data['l0_mean']:.1%} → L4={data['l4_mean']:.1%} "
                  f"(Δ={data['delta']:+.1%}, n={data['n_l0']}+{data['n_l4']})")
        print()

    if summary.get("by_domain"):
        print("  By Domain:")
        for domain, data in summary["by_domain"].items():
            marker = "+" if data["delta"] > 0 else "-" if data["delta"] < 0 else "="
            print(f"    {domain:20s}: L0={data['l0_mean']:.1%} → L4={data['l4_mean']:.1%} "
                  f"({data['delta']:+.1%}) {marker}")

    # 生成图表
    print(f"\n生成图表...")
    try:
        figure1_domain_heatmap(results)
    except Exception as e:
        print(f"  Figure 1 failed: {e}")

    try:
        figure2_quality_vs_effect(results, scores)
    except Exception as e:
        print(f"  Figure 2 failed: {e}")

    try:
        figure3_model_response(results)
    except Exception as e:
        print(f"  Figure 3 failed: {e}")

    try:
        figure4_domain_difficulty(results)
    except Exception as e:
        print(f"  Figure 4 failed: {e}")

    try:
        figure5_case_analysis(results)
    except Exception as e:
        print(f"  Figure 5 failed: {e}")

    print(f"\n完成! 图表保存在: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
