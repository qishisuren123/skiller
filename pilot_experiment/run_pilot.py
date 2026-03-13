#!/usr/bin/env python3
"""
Pilot 实验主脚本
按假设优先级逐步跑，每个阶段完成后输出中间结果。

用法:
  python run_pilot.py [--phase 1|2|3|4|all] [--budget 200]
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path

# 添加 scripts 目录到 path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from config import MODELS, total_cost, cost_summary, RESULTS_DIR, ROOT
from runner import call_model, extract_python_code
from evaluator import run_generated_code

# 加载场景
sys.path.insert(0, str(ROOT / "scenarios/neuro_metadata"))
sys.path.insert(0, str(ROOT / "scenarios/spike_behavior"))
import scenarios.neuro_metadata.scenario as s1
import scenarios.spike_behavior.scenario as s2

SCENARIOS = {
    "neuro_metadata": {"task": s1.TASK_DESC, "test": s1.TEST_SCRIPT},
    "spike_behavior": {"task": s2.TASK_DESC, "test": s2.TEST_SCRIPT},
}

# Skill 内容
SKILLS_DIR = Path("generated_skills")


def load_skill(skill_name: str) -> str:
    """加载 SKILL.md 的完整内容"""
    path = SKILLS_DIR / skill_name / "SKILL.md"
    return path.read_text() if path.exists() else ""


def load_full_skill(skill_name: str) -> str:
    """加载 SKILL.md + references/workflow.md + references/pitfalls.md"""
    parts = [load_skill(skill_name)]
    for ref in ["references/workflow.md", "references/pitfalls.md"]:
        p = SKILLS_DIR / skill_name / ref
        if p.exists():
            parts.append(f"\n\n---\n# {ref}\n\n{p.read_text()}")
    return "\n".join(parts)


def load_ablated_skill(skill_name: str, exclude: list[str]) -> str:
    """加载 skill 但排除指定成分"""
    parts = [load_skill(skill_name)]
    all_refs = {
        "workflow": "references/workflow.md",
        "pitfalls": "references/pitfalls.md",
    }
    for key, ref in all_refs.items():
        if key not in exclude:
            p = SKILLS_DIR / skill_name / ref
            if p.exists():
                parts.append(f"\n\n---\n# {ref}\n\n{p.read_text()}")
    # 如果排除 code，不附加 scripts 引用；否则附加 main.py 的代码
    if "code" not in exclude:
        code_path = SKILLS_DIR / skill_name / "scripts/main.py"
        if code_path.exists():
            code = code_path.read_text()
            # 截取前 200 行以免太长
            lines = code.split("\n")[:200]
            parts.append(f"\n\n---\n# Reference implementation (first 200 lines)\n\n```python\n{chr(10).join(lines)}\n```")
    return "\n".join(parts)


def run_single(model_key: str, scenario: str, condition: str,
               skill_content: str | None, budget: float) -> dict:
    """跑一个实验条件，检查预算"""
    current = total_cost()
    if current >= budget:
        print(f"  [SKIP] Budget exhausted: ${current:.2f} >= ${budget:.2f}")
        return {"skipped": True, "reason": "budget"}

    print(f"  [{model_key}] {scenario} / {condition} ... ", end="", flush=True)
    t0 = time.time()

    # 调 API
    result = call_model(model_key, SCENARIOS[scenario]["task"],
                        skill_content, scenario, condition)

    # 提取代码
    code = extract_python_code(result["response"])
    if not code:
        print(f"NO CODE (cost: ${result['cost_usd']:.4f})")
        return {**result, "eval": {"passed": False, "n_pass": 0, "n_total": 0,
                                   "error": "No code block extracted"}}

    # 运行评测
    eval_result = run_generated_code(code, SCENARIOS[scenario]["test"], timeout=60)
    elapsed = time.time() - t0
    print(f"{eval_result['n_pass']}/{eval_result['n_total']} "
          f"(${result['cost_usd']:.4f}, {elapsed:.1f}s)")

    return {**result, "eval": eval_result, "code_length": len(code)}


def save_results(phase: str, data: list[dict]):
    """保存阶段结果"""
    out = RESULTS_DIR / f"phase_{phase}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    print(f"\n  Results saved to {out}")


def print_phase_summary(phase: str, data: list[dict]):
    """打印阶段汇总表"""
    print(f"\n{'='*60}")
    print(f"Phase {phase} Summary")
    print(f"{'='*60}")
    print(f"{'Model':<10} {'Scenario':<18} {'Condition':<20} {'Pass':>6} {'Cost':>8}")
    print("-" * 60)
    for d in data:
        if d.get("skipped"):
            continue
        ev = d.get("eval", {})
        score = f"{ev.get('n_pass',0)}/{ev.get('n_total',0)}"
        print(f"{d['model']:<10} {d['scenario']:<18} {d['condition']:<20} {score:>6} ${d['cost_usd']:>7.4f}")
    print(f"\nTotal cost so far: ${total_cost():.4f}")


# ==========================================================================
# Phase 1: F1 验证 — Near-miss skill 是否比 no skill 更危险
# ==========================================================================
def phase1(budget: float) -> list[dict]:
    print("\n" + "=" * 60)
    print("Phase 1: F1 — Near-miss skill vs No skill vs Exact skill")
    print("=" * 60)

    exact_skills = {
        "neuro_metadata": load_full_skill("neuro-metadata-gen"),
        "spike_behavior": load_full_skill("spike-behavior-organize"),
    }
    # Near-miss：给错的 skill（互换）
    nearmiss_skills = {
        "neuro_metadata": load_full_skill("spike-behavior-organize"),
        "spike_behavior": load_full_skill("neuro-metadata-gen"),
    }

    results = []
    for model in ["haiku", "sonnet", "opus"]:
        for scenario in ["neuro_metadata", "spike_behavior"]:
            # 条件 1：No skill
            r = run_single(model, scenario, "no_skill", None, budget)
            results.append(r)
            # 条件 2：Exact-match skill
            r = run_single(model, scenario, "exact_skill", exact_skills[scenario], budget)
            results.append(r)
            # 条件 3：Near-miss skill
            r = run_single(model, scenario, "nearmiss_skill", nearmiss_skills[scenario], budget)
            results.append(r)

    save_results("1_nearmiss", results)
    print_phase_summary("1", results)
    return results


# ==========================================================================
# Phase 2: F2 — 弱模型是否从 skill 中获益更多
# ==========================================================================
def phase2(budget: float) -> list[dict]:
    print("\n" + "=" * 60)
    print("Phase 2: F2 — Weak model benefits more from skills?")
    print("=" * 60)
    # 数据来自 phase 1（no_skill vs exact_skill），只需分析即可
    # 如果 phase 1 已跑，直接加载
    p1_file = RESULTS_DIR / "phase_1_nearmiss.json"
    if p1_file.exists():
        data = json.loads(p1_file.read_text())
        print("  Loaded Phase 1 data for analysis")

        # 计算每个模型的 Δ score
        print(f"\n{'Model':<10} {'Scenario':<18} {'No Skill':>10} {'With Skill':>12} {'Delta':>8}")
        print("-" * 60)
        for model in ["haiku", "sonnet", "opus"]:
            for scenario in ["neuro_metadata", "spike_behavior"]:
                no_skill = [d for d in data if d.get("model") == model
                            and d.get("scenario") == scenario
                            and d.get("condition") == "no_skill"
                            and not d.get("skipped")]
                exact = [d for d in data if d.get("model") == model
                         and d.get("scenario") == scenario
                         and d.get("condition") == "exact_skill"
                         and not d.get("skipped")]
                if no_skill and exact:
                    ns = no_skill[0]["eval"]["n_pass"]
                    nt = no_skill[0]["eval"]["n_total"]
                    es = exact[0]["eval"]["n_pass"]
                    et = exact[0]["eval"]["n_total"]
                    delta = es - ns
                    print(f"{model:<10} {scenario:<18} {ns}/{nt:>5}      {es}/{et:>5}    {delta:>+4}")
        return data
    else:
        print("  Phase 1 not yet run, skipping analysis")
        return []


# ==========================================================================
# Phase 3: F3 — 跨模型 skill 迁移（Opus 写 → Haiku 用 vs Haiku 写 → Opus 用）
# ==========================================================================
def phase3(budget: float) -> list[dict]:
    print("\n" + "=" * 60)
    print("Phase 3: F3 — Cross-model skill authoring")
    print("=" * 60)
    print("  Generating skills with Haiku for each scenario...")

    results = []
    for scenario in ["neuro_metadata"]:  # 先只做 1 个场景省钱
        # 让 Haiku 生成一个 skill（模拟 Haiku 作者）
        haiku_skill_prompt = f"""Based on the following task, write a concise SKILL.md document that another AI could use as a guide. Include: workflow steps, common pitfalls with solutions, and error handling tips.

Task: {SCENARIOS[scenario]['task']}

Write the SKILL.md content directly, in markdown format."""

        print("  Generating Haiku-authored skill...")
        skill_result = call_model("haiku", haiku_skill_prompt, None, scenario, "haiku_author_gen")
        haiku_skill = skill_result["response"]

        # Opus-authored skill 就用已有的
        opus_skill = load_full_skill("neuro-metadata-gen")

        # 测试组合
        combos = [
            ("haiku", "haiku_authored_skill", haiku_skill),    # Haiku → Haiku
            ("opus", "haiku_authored_skill", haiku_skill),     # Haiku → Opus
            ("haiku", "opus_authored_skill", opus_skill),      # Opus → Haiku
            ("opus", "opus_authored_skill", opus_skill),       # Opus → Opus
        ]
        for user_model, condition, skill in combos:
            r = run_single(user_model, scenario, condition, skill, budget)
            results.append(r)

    save_results("3_crossmodel", results)
    print_phase_summary("3", results)
    return results


# ==========================================================================
# Phase 4: F4 — 消融实验（哪个 skill 成分在起作用）
# ==========================================================================
def phase4(budget: float) -> list[dict]:
    print("\n" + "=" * 60)
    print("Phase 4: F4 — Component ablation")
    print("=" * 60)

    scenario = "neuro_metadata"  # 只做 1 个场景
    results = []

    ablations = {
        "full_skill": load_ablated_skill("neuro-metadata-gen", exclude=[]),
        "no_pitfalls": load_ablated_skill("neuro-metadata-gen", exclude=["pitfalls"]),
        "no_code": load_ablated_skill("neuro-metadata-gen", exclude=["code"]),
        "no_workflow": load_ablated_skill("neuro-metadata-gen", exclude=["workflow"]),
        "only_pitfalls": load_ablated_skill("neuro-metadata-gen", exclude=["workflow", "code"]),
        "only_code": load_ablated_skill("neuro-metadata-gen", exclude=["workflow", "pitfalls"]),
        "skillmd_only": load_skill("neuro-metadata-gen"),  # 只有 SKILL.md，不附加任何 reference
    }

    for model in ["haiku", "sonnet"]:  # 省钱先不跑 Opus
        for cond_name, skill_content in ablations.items():
            r = run_single(model, scenario, f"ablation_{cond_name}", skill_content, budget)
            results.append(r)

    save_results("4_ablation", results)
    print_phase_summary("4", results)
    return results


def update_progress():
    """更新 PROGRESS.md"""
    summary = cost_summary()
    # 加载所有阶段结果
    phases = {}
    for f in RESULTS_DIR.glob("phase_*.json"):
        data = json.loads(f.read_text())
        phases[f.stem] = data

    progress = f"""# Pilot Experiment Progress

**Last updated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total cost**: ${summary.get('total_usd', 0):.4f}
**Total API calls**: {summary.get('n_calls', 0)}

## Cost by model
{json.dumps(summary.get('by_model', {}), indent=2)}

## Cost by scenario
{json.dumps(summary.get('by_scenario', {}), indent=2)}

## Phase Results Summary
"""

    for phase_name, data in sorted(phases.items()):
        valid = [d for d in data if not d.get("skipped")]
        progress += f"\n### {phase_name}\n"
        progress += f"Runs: {len(valid)}\n\n"
        progress += f"| Model | Scenario | Condition | Pass | Cost |\n"
        progress += f"|-------|----------|-----------|------|------|\n"
        for d in valid:
            ev = d.get("eval", {})
            progress += (f"| {d['model']} | {d['scenario']} | {d['condition']} | "
                        f"{ev.get('n_pass',0)}/{ev.get('n_total',0)} | "
                        f"${d['cost_usd']:.4f} |\n")

    (ROOT / "PROGRESS.md").write_text(progress)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="all", help="Phase to run: 1,2,3,4,all")
    parser.add_argument("--budget", type=float, default=200.0, help="Max budget in USD")
    args = parser.parse_args()

    os.makedirs(RESULTS_DIR / "raw", exist_ok=True)

    phases_to_run = args.phase.split(",") if args.phase != "all" else ["1", "2", "3", "4"]

    if "1" in phases_to_run:
        phase1(args.budget)
        update_progress()

    if "2" in phases_to_run:
        phase2(args.budget)

    if "3" in phases_to_run:
        phase3(args.budget)
        update_progress()

    if "4" in phases_to_run:
        phase4(args.budget)
        update_progress()

    print(f"\n{'='*60}")
    print(f"All phases complete. Total cost: ${total_cost():.4f}")
    print(json.dumps(cost_summary(), indent=2))


if __name__ == "__main__":
    main()
