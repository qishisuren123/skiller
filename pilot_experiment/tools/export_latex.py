#!/usr/bin/env python3
"""
LaTeX 表格导出工具：从实验结果生成论文表格。

表格:
1. Main Results: model × completeness_level
2. Error Tolerance: mutation_type × model (Δpass_rate)
3. Per-RQ Summary: 关键发现汇总

用法:
    python tools/export_latex.py [--input results/experiment_results.jsonl]
"""
import sys
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


def table_rq1_main(results: list[dict]) -> str:
    """RQ1 主表: model × completeness_level → pass_rate"""
    # 聚合数据
    data = defaultdict(list)
    for r in results:
        tc = r.get("trial_config", {})
        level = tc.get("skill_level", "")
        model = tc.get("model", "")
        if level and model:
            data[(model, level)].append(r.get("eval", {}).get("pass_rate", 0))

    models = sorted(set(k[0] for k in data))
    levels = ["L0_none", "L1_skill_md", "L2_plus_scripts", "L3_no_assets", "L4_full"]
    levels = [l for l in levels if any((m, l) in data for m in models)]

    if not data:
        return "% RQ1: 无数据\n"

    # 生成 LaTeX
    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{RQ1: Pass rate (\\%) by model and skill completeness level.}")
    lines.append("\\label{tab:rq1_main}")
    lines.append("\\begin{tabular}{l" + "c" * len(levels) + "}")
    lines.append("\\toprule")

    # 表头
    header = "Model & " + " & ".join(l.replace("_", "\\_") for l in levels) + " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    # 数据行
    for m in models:
        row = m.replace("_", "\\_")
        for l in levels:
            vals = data.get((m, l), [])
            if vals:
                mean = np.mean(vals) * 100
                # 加粗最高值
                row += f" & {mean:.1f}"
            else:
                row += " & --"
        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def table_rq2_error(results: list[dict]) -> str:
    """RQ2 表: mutation_type × model → Δpass_rate"""
    clean = defaultdict(list)
    mutated = defaultdict(lambda: defaultdict(list))

    for r in results:
        tc = r.get("trial_config", {})
        mut = tc.get("mutation_type", "none")
        model = tc.get("model", "")
        pr = r.get("eval", {}).get("pass_rate", 0)

        if mut == "none" and "clean" in tc.get("condition", ""):
            clean[(tc.get("scenario_id", ""), model)].append(pr)
        elif mut != "none":
            mutated[mut][(tc.get("scenario_id", ""), model)].append(pr)

    if not mutated:
        return "% RQ2: 无数据\n"

    models = sorted(set(k[1] for k in clean))
    mut_types = sorted(mutated.keys())

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{RQ2: Impact of skill errors (\\textDelta pass rate, pp).}")
    lines.append("\\label{tab:rq2_error}")
    lines.append("\\begin{tabular}{l" + "c" * len(models) + "}")
    lines.append("\\toprule")

    header = "Mutation Type & " + " & ".join(m.replace("_", "\\_") for m in models) + " \\\\"
    lines.append(header)
    lines.append("\\midrule")

    for mt in mut_types:
        row = mt.replace("_", "\\_")
        for m in models:
            deltas = []
            for key in clean:
                if key[1] == m and key in mutated[mt]:
                    c_mean = np.mean(clean[key])
                    m_mean = np.mean(mutated[mt][key])
                    deltas.append((m_mean - c_mean) * 100)
            if deltas:
                delta = np.mean(deltas)
                sign = "+" if delta > 0 else ""
                row += f" & {sign}{delta:.1f}"
            else:
                row += " & --"
        row += " \\\\"
        lines.append(row)

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def table_summary(results: list[dict]) -> str:
    """总览表: 每个 RQ 的关键数字"""
    # 按实验名分组
    by_rq = defaultdict(list)
    for r in results:
        tc = r.get("trial_config", {})
        cond = tc.get("condition", "")
        if cond.startswith("L"):
            by_rq["RQ1"].append(r)
        elif "mutated" in cond or "clean" in cond:
            by_rq["RQ2"].append(r)
        elif cond.startswith("rq3"):
            by_rq["RQ3"].append(r)

    lines = []
    lines.append("\\begin{table}[t]")
    lines.append("\\centering")
    lines.append("\\caption{Summary of key findings across research questions.}")
    lines.append("\\label{tab:summary}")
    lines.append("\\begin{tabular}{llrr}")
    lines.append("\\toprule")
    lines.append("RQ & Key Metric & Value & N \\\\")
    lines.append("\\midrule")

    for rq_name, rq_results in sorted(by_rq.items()):
        pass_rates = [r.get("eval", {}).get("pass_rate", 0) for r in rq_results]
        if pass_rates:
            mean_pr = np.mean(pass_rates) * 100
            lines.append(f"{rq_name} & Mean pass rate & {mean_pr:.1f}\\% & {len(pass_rates)} \\\\")

    lines.append("\\bottomrule")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成 LaTeX 表格")
    parser.add_argument("--input", default=str(ROOT / "results" / "experiment_results.jsonl"))
    parser.add_argument("--output", default=str(ROOT / "results" / "analysis" / "tables.tex"))
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"结果文件不存在: {input_path}")
        return 1

    results = load_results(input_path)
    print(f"加载 {len(results)} 条结果")

    latex_parts = []
    latex_parts.append("% 自动生成的 LaTeX 表格")
    latex_parts.append("% Generated by tools/export_latex.py\n")

    t1 = table_rq1_main(results)
    latex_parts.append("% === RQ1: Main Results ===")
    latex_parts.append(t1)
    print("  ✓ RQ1 main table")

    t2 = table_rq2_error(results)
    latex_parts.append("\n% === RQ2: Error Tolerance ===")
    latex_parts.append(t2)
    print("  ✓ RQ2 error table")

    t3 = table_summary(results)
    latex_parts.append("\n% === Summary ===")
    latex_parts.append(t3)
    print("  ✓ Summary table")

    output_path.write_text("\n".join(latex_parts) + "\n")
    print(f"\nLaTeX 已保存: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
