#!/usr/bin/env python3
"""
实验主调度器：config-driven 实验运行。

支持 4 个 RQ:
- RQ1: Minimum Viable Skill（完整度级别 L0-L4 + SKILL.md 子级裁剪）
- RQ2: Error Tolerance（5 种错误注入 × 模型）
- RQ3: When Skills Don't Help（失败模式分析）
- RQ4: Evaluation Design（24-point score ↔ runtime pass_rate 相关性）

用法:
    python experiment_runner.py --rq rq1 --scenarios S001,S002 --models haiku,sonnet --budget 50
    python experiment_runner.py --rq all --sample 30 --budget 250
    python experiment_runner.py --dry-run --rq rq1
"""
import sys
import os
import json
import time
import argparse
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
from config import (API_KEY, BASE_URL, MODELS, MODEL_TIERS,
                    RESULTS_DIR, RAW_DIR, SKILLS_DIR,
                    total_cost, log_cost, VACCINATION_PREFIX)
from lib.api_client import call_model, extract_python_code
from lib.evaluator import run_generated_code, compute_code_metrics
from lib.skill_injector import serialize_skill_package, COMPLETENESS_LEVELS, estimate_tokens
from lib.skill_stripper import strip_skill, STRIP_MODES
from lib.skill_mutator import mutate_skill, MUTATION_TYPES
from lib.scenario_loader import load_all_scenarios, stratified_sample


# ============ 实验配置 ============

@dataclass
class TrialConfig:
    """单次实验 trial 的配置"""
    scenario_id: str
    model: str
    condition: str              # 描述性条件名
    skill_method: str = "none"  # none / direct / pipeline
    skill_level: str = "L0_none"  # L0_none ~ L4_full
    strip_mode: str = "full"    # SKILL.md 子级裁剪
    mutation_type: str = "none" # none / stale_api / wrong_default / ...
    mutation_seed: int = 42
    temperature: float = 0.0
    run_id: int = 0

    @property
    def trial_key(self) -> str:
        """唯一标识符，用于去重和崩溃恢复"""
        parts = [self.scenario_id, self.model, self.condition,
                 f"t{self.temperature}", f"r{self.run_id}"]
        return "__".join(parts)


@dataclass
class ExperimentConfig:
    """实验配置"""
    name: str
    trials: list[TrialConfig] = field(default_factory=list)
    budget: float = 500.0
    description: str = ""


# ============ 结果追踪 ============

EXPERIMENT_LOG = RESULTS_DIR / "experiment_results.jsonl"


def load_completed_trials() -> set[str]:
    """加载已完成的 trial keys（崩溃恢复）"""
    if not EXPERIMENT_LOG.exists():
        return set()
    completed = set()
    for line in EXPERIMENT_LOG.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            entry = json.loads(line)
            completed.add(entry.get("trial_key", ""))
        except json.JSONDecodeError:
            continue
    return completed


def append_result(result: dict):
    """追加单条结果到 JSONL"""
    EXPERIMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(EXPERIMENT_LOG, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")


# ============ Trial 执行 ============

def prepare_skill_content(trial: TrialConfig, scenarios: dict) -> str | None:
    """根据 trial 配置准备 skill 内容"""
    # RQ3 wrong_skill: 加载其他场景的 skill
    if trial.condition == "rq3_wrong_skill":
        return _prepare_wrong_skill(trial, scenarios)

    if trial.skill_level == "L0_none" and trial.skill_method == "none":
        return None

    # 查找 skill 目录
    skill_dir = SKILLS_DIR / trial.scenario_id / trial.skill_method
    if not skill_dir.exists() or not (skill_dir / "SKILL.md").exists():
        # 降级：如果指定方法不存在，尝试 direct
        skill_dir = SKILLS_DIR / trial.scenario_id / "direct"
        if not skill_dir.exists() or not (skill_dir / "SKILL.md").exists():
            return None

    # 序列化 skill 包到指定完整度级别
    serialized = serialize_skill_package(skill_dir, trial.skill_level)
    if not serialized:
        return None

    # SKILL.md 子级裁剪（仅在 L1 级别时有效）
    if trial.skill_level == "L1_skill_md" and trial.strip_mode != "full":
        serialized = strip_skill(serialized, trial.strip_mode)

    # 错误注入
    if trial.mutation_type != "none":
        serialized, changes = mutate_skill(serialized, trial.mutation_type,
                                           seed=trial.mutation_seed)

    # RQ3 vaccination: 加上免疫前缀
    if trial.condition == "rq3_vaccinated" and serialized:
        serialized = VACCINATION_PREFIX + "\n\n" + serialized

    return serialized if serialized.strip() else None


def _prepare_wrong_skill(trial: TrialConfig, scenarios: dict) -> str | None:
    """为 RQ3 wrong_skill 条件加载一个不同领域的 skill"""
    # 找与当前场景不同领域的场景
    all_sids = sorted(scenarios.keys())
    current_domain = scenarios.get(trial.scenario_id, {}).get("domain", "")

    # 优先选不同领域的场景
    for other_sid in all_sids:
        if other_sid == trial.scenario_id:
            continue
        other_domain = scenarios.get(other_sid, {}).get("domain", "")
        if other_domain != current_domain:
            skill_dir = SKILLS_DIR / other_sid / "direct"
            if skill_dir.exists() and (skill_dir / "SKILL.md").exists():
                return serialize_skill_package(skill_dir, "L4_full")

    # 降级：随便找一个有 skill 的不同场景
    for other_sid in all_sids:
        if other_sid != trial.scenario_id:
            skill_dir = SKILLS_DIR / other_sid / "direct"
            if skill_dir.exists() and (skill_dir / "SKILL.md").exists():
                return serialize_skill_package(skill_dir, "L4_full")

    return None


def run_trial(trial: TrialConfig, scenarios: dict) -> dict:
    """执行单个 trial"""
    scenario = scenarios[trial.scenario_id]
    t0 = time.time()

    # 准备 skill
    skill_content = prepare_skill_content(trial, scenarios)
    skill_tokens = estimate_tokens(skill_content) if skill_content else 0

    print(f"  [{trial.model:12s}] {trial.scenario_id:25s} / {trial.condition:30s} ", end="", flush=True)

    # 调用 LLM
    api_result = call_model(
        trial.model, scenario["task"], skill_content,
        trial.scenario_id, trial.condition,
        temperature=trial.temperature, run_id=trial.run_id
    )

    # 提取代码
    code = extract_python_code(api_result["response"])
    if not code:
        elapsed = time.time() - t0
        print(f"NO CODE (${api_result['cost_usd']:.4f} {elapsed:.0f}s)")
        result = {
            **api_result,
            "trial_key": trial.trial_key,
            "trial_config": asdict(trial),
            "skill_tokens": skill_tokens,
            "eval": {"passed": False, "n_pass": 0, "n_total": 0,
                     "pass_rate": 0, "error_type": "format_error",
                     "details": [], "scores": {}},
            "code_metrics": {},
            "code_length": 0,
        }
        append_result(result)
        return result

    # 执行评估
    ev = run_generated_code(code, scenario["test"], timeout=90)
    metrics = compute_code_metrics(code)
    elapsed = time.time() - t0

    print(f"{ev['n_pass']}/{ev['n_total']} ({ev['pass_rate']:.0%}) "
          f"${api_result['cost_usd']:.4f} {elapsed:.0f}s "
          f"[{metrics['non_empty_lines']}L err={ev.get('error_type', '?')}]")

    result = {
        **api_result,
        "trial_key": trial.trial_key,
        "trial_config": asdict(trial),
        "skill_tokens": skill_tokens,
        "eval": ev,
        "code_metrics": metrics,
        "code_length": len(code),
    }
    # 不在 JSONL 中保存完整 response（太大）
    result_slim = {k: v for k, v in result.items() if k != "response"}
    append_result(result_slim)
    return result


def run_experiment(config: ExperimentConfig, scenarios: dict):
    """运行整个实验"""
    completed = load_completed_trials()
    remaining = [t for t in config.trials if t.trial_key not in completed]

    print(f"\n{'='*70}")
    print(f"EXPERIMENT: {config.name}")
    print(f"{'='*70}")
    print(f"  {config.description}")
    print(f"  总 trials: {len(config.trials)}")
    print(f"  已完成: {len(completed & {t.trial_key for t in config.trials})}")
    print(f"  待运行: {len(remaining)}")
    print(f"  预算: ${config.budget}")
    print(f"  当前花费: ${total_cost():.4f}")
    print()

    results = []
    for i, trial in enumerate(remaining):
        if total_cost() >= config.budget:
            print(f"\n预算已用完: ${total_cost():.4f} >= ${config.budget}")
            break
        results.append(run_trial(trial, scenarios))

    return results


# ============ RQ 配置生成器 ============

def make_rq1_config(scenario_ids: list[str], models: list[str],
                    skill_methods: list[str] = None) -> ExperimentConfig:
    """
    RQ1: Minimum Viable Skill
    变量: 完整度级别 (L0-L4) × 模型 × 场景
    """
    if skill_methods is None:
        skill_methods = ["direct"]

    trials = []
    levels = list(COMPLETENESS_LEVELS.keys())

    for sid in scenario_ids:
        for model in models:
            # L0: no skill baseline
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="L0_none",
                skill_method="none", skill_level="L0_none",
            ))
            # L1-L4: 不同完整度
            for method in skill_methods:
                for level in levels[1:]:  # 跳过 L0
                    trials.append(TrialConfig(
                        scenario_id=sid, model=model,
                        condition=f"{level}__{method}",
                        skill_method=method, skill_level=level,
                    ))

    return ExperimentConfig(
        name="rq1_completeness",
        description="RQ1: What is the minimum viable skill? Testing 5 completeness levels.",
        trials=trials,
    )


def make_rq1_strip_config(scenario_ids: list[str], models: list[str]) -> ExperimentConfig:
    """
    RQ1 补充: SKILL.md 内部子级裁剪
    在 L1_skill_md 级别下测试不同裁剪方式
    """
    trials = []
    strip_modes = ["full", "overview_only", "text_only", "code_only",
                   "pitfalls_only", "workflow_only", "no_pitfalls",
                   "first_half", "second_half"]

    for sid in scenario_ids:
        for model in models:
            for mode in strip_modes:
                trials.append(TrialConfig(
                    scenario_id=sid, model=model,
                    condition=f"L1_strip_{mode}",
                    skill_method="direct", skill_level="L1_skill_md",
                    strip_mode=mode,
                ))

    return ExperimentConfig(
        name="rq1_strip",
        description="RQ1 supplement: SKILL.md sub-level stripping.",
        trials=trials,
    )


def make_rq2_config(scenario_ids: list[str], models: list[str]) -> ExperimentConfig:
    """
    RQ2: Error Tolerance
    变量: 5 种错误注入 × 模型 × 场景
    + clean baseline (L4_full without mutation)
    """
    trials = []

    for sid in scenario_ids:
        for model in models:
            # Clean baseline
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="clean_full",
                skill_method="direct", skill_level="L4_full",
                mutation_type="none",
            ))
            # 5 种错误注入
            for mut in MUTATION_TYPES:
                trials.append(TrialConfig(
                    scenario_id=sid, model=model,
                    condition=f"mutated_{mut}",
                    skill_method="direct", skill_level="L4_full",
                    mutation_type=mut,
                ))

    return ExperimentConfig(
        name="rq2_error_tolerance",
        description="RQ2: How tolerant are models to skill errors? 5 mutation types.",
        trials=trials,
    )


def make_rq3_config(scenario_ids: list[str], models: list[str]) -> ExperimentConfig:
    """
    RQ3: When Skills Don't Help
    比较: no_skill, full_skill, vaccination (skill + 免疫前缀), wrong_scenario_skill (不同领域的 skill)
    """
    trials = []

    for sid in scenario_ids:
        for model in models:
            # No skill baseline
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="rq3_no_skill",
                skill_method="none", skill_level="L0_none",
            ))
            # Full skill
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="rq3_full_skill",
                skill_method="direct", skill_level="L4_full",
            ))
            # Vaccination: skill + 免疫前缀（提醒 LLM 批判性使用 skill）
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="rq3_vaccinated",
                skill_method="direct", skill_level="L4_full",
            ))
            # Wrong skill: 使用不同领域场景的 skill（测试错误 skill 的影响）
            trials.append(TrialConfig(
                scenario_id=sid, model=model,
                condition="rq3_wrong_skill",
                skill_method="direct", skill_level="L4_full",  # _prepare_wrong_skill 处理
            ))

    return ExperimentConfig(
        name="rq3_when_skills_dont_help",
        description="RQ3: When do skills hurt? Failure mode analysis.",
        trials=trials,
    )


def make_significance_config(scenario_ids: list[str], models: list[str],
                             n_runs: int = 5) -> ExperimentConfig:
    """显著性检验: 关键条件的多次重复"""
    trials = []
    key_conditions = [
        ("sig_no_skill", "none", "L0_none"),
        ("sig_full_skill", "direct", "L4_full"),
    ]

    for run_id in range(n_runs):
        for sid in scenario_ids:
            for model in models:
                for cond_name, method, level in key_conditions:
                    trials.append(TrialConfig(
                        scenario_id=sid, model=model,
                        condition=cond_name,
                        skill_method=method, skill_level=level,
                        temperature=0.3, run_id=run_id,
                    ))

    return ExperimentConfig(
        name="significance",
        description=f"Significance test: {n_runs} runs with temp=0.3.",
        trials=trials,
    )


# ============ 预算估算 ============

def estimate_budget(config: ExperimentConfig) -> dict:
    """估算实验预算"""
    from config import COST_PER_M

    total_est = 0
    by_model = {}
    for trial in config.trials:
        # 粗略估算：input ~3k tokens, output ~2k tokens
        rates = COST_PER_M.get(trial.model, {"input": 3, "output": 15})
        est = (3000 * rates["input"] + 2000 * rates["output"]) / 1_000_000
        total_est += est
        by_model[trial.model] = by_model.get(trial.model, 0) + est

    return {
        "total_est_usd": round(total_est, 2),
        "n_trials": len(config.trials),
        "by_model": {k: round(v, 2) for k, v in by_model.items()},
    }


# ============ 主函数 ============

def main():
    parser = argparse.ArgumentParser(description="实验主调度器")
    parser.add_argument("--rq", default="rq1",
                        help="实验类型: rq1, rq1_strip, rq2, rq3, significance, all")
    parser.add_argument("--scenarios", default="all",
                        help="场景 ID 列表或 'all'")
    parser.add_argument("--sample", type=int, default=0,
                        help="分层抽样场景数（0=不抽样）")
    parser.add_argument("--models", default="haiku,sonnet,opus",
                        help="模型列表")
    parser.add_argument("--budget", type=float, default=500.0)
    parser.add_argument("--n-runs", type=int, default=5,
                        help="显著性重复次数")
    parser.add_argument("--dry-run", action="store_true",
                        help="只显示计划和预算估算")
    args = parser.parse_args()

    # 加载场景
    all_scenarios = load_all_scenarios()
    if args.scenarios == "all":
        scenario_ids = sorted(all_scenarios.keys())
    else:
        scenario_ids = [s.strip() for s in args.scenarios.split(",")]

    # 分层抽样
    if args.sample > 0:
        scenario_ids = stratified_sample(all_scenarios, args.sample)
        print(f"分层抽样 {args.sample} 个场景: {scenario_ids[:5]}...")

    models = [m.strip() for m in args.models.split(",")]

    # 构建实验配置
    rqs = [r.strip() for r in args.rq.split(",")]
    configs = []

    if "rq1" in rqs or "all" in rqs:
        configs.append(make_rq1_config(scenario_ids, models))
    if "rq1_strip" in rqs or "all" in rqs:
        configs.append(make_rq1_strip_config(scenario_ids, models))
    if "rq2" in rqs or "all" in rqs:
        # RQ2: 前 10 场景 × 全部模型 × 6 条件
        rq2_scenarios = scenario_ids[:10]
        configs.append(make_rq2_config(rq2_scenarios, models))
    if "rq3" in rqs or "all" in rqs:
        # RQ3: 前 15 场景 × 全部模型 × 4 条件
        rq3_scenarios = scenario_ids[:15]
        configs.append(make_rq3_config(rq3_scenarios, models))
    if "significance" in rqs or "all" in rqs:
        sig_scenarios = scenario_ids[:10]
        sig_models = [m for m in models if m in ["haiku", "sonnet", "opus"]]
        configs.append(make_significance_config(sig_scenarios, sig_models, args.n_runs))

    if not configs:
        print(f"未知 RQ: {args.rq}")
        return 1

    # 显示计划
    total_trials = sum(len(c.trials) for c in configs)
    print(f"\n场景: {len(scenario_ids)}")
    print(f"模型: {models}")
    print(f"总 trials: {total_trials}")
    print(f"预算: ${args.budget}")
    print(f"当前花费: ${total_cost():.4f}")

    for c in configs:
        est = estimate_budget(c)
        print(f"\n  {c.name}: {len(c.trials)} trials, ~${est['total_est_usd']}")
        print(f"    {c.description}")
        for m, cost in est["by_model"].items():
            print(f"      {m}: ~${cost}")

    if args.dry_run:
        print("\n[DRY RUN] 不执行实验")
        return 0

    # 执行实验
    all_results = []
    for c in configs:
        c.budget = args.budget
        results = run_experiment(c, all_scenarios)
        all_results.extend(results)

    # 汇总
    valid = [r for r in all_results if not r.get("skipped")]
    print(f"\n{'='*70}")
    print(f"实验完成: {len(valid)} trials")
    print(f"总花费: ${total_cost():.4f}")

    if valid:
        pass_rates = [r.get("eval", {}).get("pass_rate", 0) for r in valid]
        print(f"平均 pass_rate: {sum(pass_rates)/len(pass_rates):.2%}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
