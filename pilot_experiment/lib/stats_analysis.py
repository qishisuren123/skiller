#!/usr/bin/env python3
"""
统计分析模块：显著性检验、效应量、置信区间
用于多次重复实验数据分析。
"""
import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from scipy import stats as sp_stats


def paired_ttest(group_a: list[float], group_b: list[float]) -> dict:
    """配对 t 检验"""
    if len(group_a) != len(group_b) or len(group_a) < 2:
        return {"t_stat": None, "p_value": None, "significant": False}
    t_stat, p_val = sp_stats.ttest_rel(group_a, group_b)
    return {
        "t_stat": round(float(t_stat), 4),
        "p_value": round(float(p_val), 6),
        "significant": p_val < 0.05,
    }


def independent_ttest(group_a: list[float], group_b: list[float]) -> dict:
    """独立样本 t 检验"""
    if len(group_a) < 2 or len(group_b) < 2:
        return {"t_stat": None, "p_value": None, "significant": False}
    t_stat, p_val = sp_stats.ttest_ind(group_a, group_b, equal_var=False)
    return {
        "t_stat": round(float(t_stat), 4),
        "p_value": round(float(p_val), 6),
        "significant": p_val < 0.05,
    }


def cohens_d(group_a: list[float], group_b: list[float]) -> float:
    """Cohen's d 效应量"""
    na, nb = np.array(group_a), np.array(group_b)
    if len(na) < 2 or len(nb) < 2:
        return 0.0
    pooled_std = np.sqrt((na.std(ddof=1)**2 + nb.std(ddof=1)**2) / 2)
    if pooled_std == 0:
        return 0.0
    return round(float((na.mean() - nb.mean()) / pooled_std), 4)


def bootstrap_ci(data: list[float], n_bootstrap: int = 10000,
                 ci: float = 0.95, stat_func=np.mean) -> dict:
    """Bootstrap 置信区间"""
    data = np.array(data)
    if len(data) < 2:
        return {"lower": None, "upper": None, "mean": float(data[0]) if len(data) else None}
    boot_stats = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        sample = rng.choice(data, size=len(data), replace=True)
        boot_stats.append(stat_func(sample))
    alpha = (1 - ci) / 2
    lower = float(np.percentile(boot_stats, alpha * 100))
    upper = float(np.percentile(boot_stats, (1 - alpha) * 100))
    return {
        "mean": round(float(stat_func(data)), 4),
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "ci": ci,
    }


def one_way_anova(*groups) -> dict:
    """单因素 ANOVA"""
    valid = [g for g in groups if len(g) >= 2]
    if len(valid) < 2:
        return {"f_stat": None, "p_value": None, "significant": False}
    f_stat, p_val = sp_stats.f_oneway(*valid)
    return {
        "f_stat": round(float(f_stat), 4),
        "p_value": round(float(p_val), 6),
        "significant": p_val < 0.05,
        "n_groups": len(valid),
    }


def effect_size_interpretation(d: float) -> str:
    """解释 Cohen's d"""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    elif d < 0.5:
        return "small"
    elif d < 0.8:
        return "medium"
    else:
        return "large"


def analyze_repeated_runs(results: list[dict]) -> dict:
    """
    分析多次重复实验的结果。
    输入：结果列表，每个 dict 包含 scenario, model, condition, eval.pass_rate 等。
    输出：每个 (scenario, model) 对比不同 condition 的统计检验结果。
    """
    grouped = defaultdict(list)
    for r in results:
        key = (r.get("scenario", ""), r.get("model", ""), r.get("condition", ""))
        pr = r.get("eval", {}).get("pass_rate", 0)
        grouped[key].append(pr)

    analysis = {}
    sm_pairs = set()
    for (s, m, c), vals in grouped.items():
        sm_pairs.add((s, m))

    for s, m in sorted(sm_pairs):
        conditions = {}
        for (s2, m2, c), vals in grouped.items():
            if s2 == s and m2 == m:
                conditions[c] = vals

        key = f"{s}__{m}"
        analysis[key] = {"conditions": {}}

        for cond, vals in conditions.items():
            analysis[key]["conditions"][cond] = {
                "n_runs": len(vals),
                "mean": round(np.mean(vals), 4),
                "std": round(np.std(vals, ddof=1), 4) if len(vals) > 1 else 0,
                "bootstrap_ci": bootstrap_ci(vals),
            }

        # 两两对比
        cond_list = sorted(conditions.keys())
        comparisons = []
        for i in range(len(cond_list)):
            for j in range(i + 1, len(cond_list)):
                c1, c2 = cond_list[i], cond_list[j]
                v1, v2 = conditions[c1], conditions[c2]
                comp = {
                    "condition_a": c1,
                    "condition_b": c2,
                    "ttest": independent_ttest(v1, v2),
                    "cohens_d": cohens_d(v1, v2),
                    "effect_size": effect_size_interpretation(cohens_d(v1, v2)),
                }
                comparisons.append(comp)

        analysis[key]["comparisons"] = comparisons

        if len(conditions) >= 3:
            analysis[key]["anova"] = one_way_anova(*conditions.values())

    return analysis


def format_significance(p_value: float | None) -> str:
    """格式化显著性星号"""
    if p_value is None:
        return ""
    if p_value < 0.001:
        return "***"
    elif p_value < 0.01:
        return "**"
    elif p_value < 0.05:
        return "*"
    return "n.s."


def run_analysis(results_path: Path, output_path: Path = None):
    """从结果文件运行完整分析"""
    results = json.loads(results_path.read_text())
    analysis = analyze_repeated_runs(results)

    if output_path is None:
        output_path = results_path.parent / "stats_analysis.json"
    output_path.write_text(json.dumps(analysis, indent=2, default=str))

    print("=" * 70)
    print("STATISTICAL ANALYSIS SUMMARY")
    print("=" * 70)

    for key, data in sorted(analysis.items()):
        print(f"\n{key}:")
        for cond, stats in data.get("conditions", {}).items():
            ci = stats.get("bootstrap_ci", {})
            print(f"  {cond:25s}: mean={stats['mean']:.3f} ±{stats['std']:.3f} "
                  f"CI=[{ci.get('lower', '?')}, {ci.get('upper', '?')}] (n={stats['n_runs']})")

        for comp in data.get("comparisons", []):
            p = comp["ttest"].get("p_value")
            sig = format_significance(p)
            d = comp["cohens_d"]
            print(f"  {comp['condition_a']} vs {comp['condition_b']}: "
                  f"p={p} {sig}, d={d} ({comp['effect_size']})")

        if "anova" in data:
            anova = data["anova"]
            print(f"  ANOVA: F={anova['f_stat']}, p={anova['p_value']} "
                  f"{format_significance(anova.get('p_value'))}")

    return analysis


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_analysis(Path(sys.argv[1]))
    else:
        print("Usage: python -m lib.stats_analysis <results.json>")
