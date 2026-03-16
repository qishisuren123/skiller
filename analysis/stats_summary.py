#!/usr/bin/env python3
"""
统计摘要脚本：从实验结果生成详细统计分析。
"""
import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "data" / "experiment_results.jsonl"


def load_results():
    results = []
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line:
            results.append(json.loads(line))
    return results


def compute_effect_size(group1, group2):
    """计算 Cohen's d"""
    if not group1 or not group2:
        return 0
    n1, n2 = len(group1), len(group2)
    m1, m2 = np.mean(group1), np.mean(group2)
    s1, s2 = np.std(group1, ddof=1) if n1 > 1 else 0, np.std(group2, ddof=1) if n2 > 1 else 0
    pooled_std = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / max(n1+n2-2, 1))
    return (m2 - m1) / pooled_std if pooled_std > 0 else 0


def main():
    results = load_results()
    print(f"Total trials: {len(results)}")

    # 分组
    l0 = [r for r in results if r["trial"]["condition"] == "L0_none"]
    l4 = [r for r in results if r["trial"]["condition"] == "L4_full"]

    l0_pr = [r["eval"]["pass_rate"] for r in l0]
    l4_pr = [r["eval"]["pass_rate"] for r in l4]

    print(f"\n=== Overall ===")
    print(f"L0: mean={np.mean(l0_pr):.3f} std={np.std(l0_pr):.3f} n={len(l0_pr)}")
    print(f"L4: mean={np.mean(l4_pr):.3f} std={np.std(l4_pr):.3f} n={len(l4_pr)}")
    print(f"Delta: {np.mean(l4_pr)-np.mean(l0_pr):+.3f}")
    print(f"Cohen's d: {compute_effect_size(l0_pr, l4_pr):.3f}")

    # 按模型
    print(f"\n=== By Model ===")
    by_model = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        m = r["trial"]["model"]
        c = "L0" if r["trial"]["condition"] == "L0_none" else "L4"
        by_model[m][c].append(r["eval"]["pass_rate"])

    for model in sorted(by_model):
        d = by_model[model]
        l0m = np.mean(d["L0"]) if d["L0"] else 0
        l4m = np.mean(d["L4"]) if d["L4"] else 0
        cd = compute_effect_size(d["L0"], d["L4"])
        print(f"  {model:15s}: L0={l0m:.3f} L4={l4m:.3f} Δ={l4m-l0m:+.3f} d={cd:.2f}")

    # 按领域
    print(f"\n=== By Domain ===")
    by_domain = defaultdict(lambda: {"L0": [], "L4": []})
    for r in results:
        dom = r.get("domain", "unknown")
        c = "L0" if r["trial"]["condition"] == "L0_none" else "L4"
        by_domain[dom][c].append(r["eval"]["pass_rate"])

    for dom in sorted(by_domain):
        d = by_domain[dom]
        l0m = np.mean(d["L0"]) if d["L0"] else 0
        l4m = np.mean(d["L4"]) if d["L4"] else 0
        cd = compute_effect_size(d["L0"], d["L4"])
        print(f"  {dom:20s}: L0={l0m:.3f} L4={l4m:.3f} Δ={l4m-l0m:+.3f} d={cd:.2f}")

    # 错误类型分布
    print(f"\n=== Error Types ===")
    for cond in ["L0_none", "L4_full"]:
        cond_r = [r for r in results if r["trial"]["condition"] == cond]
        err_counts = defaultdict(int)
        for r in cond_r:
            err_counts[r["eval"]["error_type"]] += 1
        print(f"  {cond}:")
        for err, cnt in sorted(err_counts.items(), key=lambda x: -x[1]):
            print(f"    {err:20s}: {cnt:3d} ({cnt/len(cond_r)*100:.0f}%)")


if __name__ == "__main__":
    main()
