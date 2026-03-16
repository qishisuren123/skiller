#!/usr/bin/env python3
"""
Step 3: L0 vs L4 验证实验。
对 50 个场景，跑 4 个模型 × 2 个条件 = 400 次试验。

用法:
    python -m skiller.validate --dry-run
    python -m skiller.validate --budget 30
    python -m skiller.validate --budget 30 --models haiku,gpt4o_mini
    python -m skiller.validate --budget 30 --ids S011,S012
"""
import sys
import json
import time
import argparse
import subprocess
import tempfile
import re
from pathlib import Path
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from skiller.utils import (
    call_llm, extract_python_code, serialize_skill_package,
    estimate_tokens, total_cost, log_cost, COST_PER_M
)

PROJECT_ROOT = Path(__file__).parent.parent
SELECTED_PATH = PROJECT_ROOT / "selected_scenarios.json"
SKILLS_DIR = PROJECT_ROOT / "skills"
RESULTS_DIR = PROJECT_ROOT / "data"
RESULTS_FILE = RESULTS_DIR / "experiment_results.jsonl"
RAW_DIR = RESULTS_DIR / "raw"

# 实验模型（4 个，平衡成本和代表性）
DEFAULT_MODELS = ["haiku", "gpt4o_mini", "gpt4o", "sonnet"]


@dataclass
class Trial:
    scenario_id: str
    model: str
    condition: str  # "L0_none" or "L4_full"
    skill_level: str  # "L0_none" or "L4_full"

    @property
    def trial_key(self) -> str:
        return f"{self.scenario_id}__{self.model}__{self.condition}"


def load_completed() -> set:
    """加载已完成的 trial keys"""
    if not RESULTS_FILE.exists():
        return set()
    completed = set()
    for line in RESULTS_FILE.read_text().strip().split("\n"):
        if line:
            try:
                entry = json.loads(line)
                completed.add(entry.get("trial_key", ""))
            except json.JSONDecodeError:
                continue
    return completed


def append_result(result: dict):
    """追加结果到 JSONL"""
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "a") as f:
        f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")


def classify_error(returncode, stdout, stderr, n_pass, n_total):
    """错误分类"""
    if stderr == "TIMEOUT":
        return "timeout"
    if n_pass == n_total and n_total > 0:
        return "success"
    stderr_lower = stderr.lower() if stderr else ""
    if "syntaxerror" in stderr_lower or "indentationerror" in stderr_lower:
        return "syntax_error"
    if "modulenotfounderror" in stderr_lower or "importerror" in stderr_lower:
        return "import_error"
    runtime_kw = ["traceback", "error", "exception", "typeerror", "valueerror",
                  "keyerror", "indexerror", "attributeerror"]
    if returncode != 0 and any(kw in stderr_lower for kw in runtime_kw):
        return "runtime_error"
    if n_total == 0 and returncode == 0:
        return "format_error"
    if n_total > 0 and n_pass < n_total:
        return "logic_error"
    if returncode != 0:
        return "runtime_error"
    return "format_error"


def run_generated_code(code: str, test_script: str, timeout: int = 90) -> dict:
    """执行生成的代码并用测试脚本验证"""
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = Path(tmpdir) / "generated.py"
        code_path.write_text(code)
        test_path = Path(tmpdir) / "test_check.py"
        test_path.write_text(test_script)

        try:
            result = subprocess.run(
                ["python", str(test_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
                env={
                    "PATH": "/usr/local/bin:/usr/bin:/bin:/root/miniconda3/bin",
                    "HOME": tmpdir,
                    "PYTHONPATH": tmpdir,
                    "TMPDIR": tmpdir,
                    "HDF5_USE_FILE_LOCKING": "FALSE",
                }
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            details = []
            scores = {}
            n_pass = n_total = 0
            for line in stdout.split("\n"):
                line = line.strip()
                if line.startswith("PASS:"):
                    details.append({"test": line[5:].strip(), "pass": True})
                    n_pass += 1
                    n_total += 1
                elif line.startswith("FAIL:"):
                    details.append({"test": line[5:].strip(), "pass": False})
                    n_total += 1
                elif line.startswith("SCORE:"):
                    kv = line[6:].strip()
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        try:
                            scores[k.strip()] = float(v.strip())
                        except ValueError:
                            scores[k.strip()] = v.strip()

            error_type = classify_error(result.returncode, stdout, stderr, n_pass, n_total)
            return {
                "passed": n_pass == n_total and n_total > 0,
                "n_pass": n_pass,
                "n_total": n_total,
                "pass_rate": round(n_pass / n_total, 4) if n_total > 0 else 0,
                "details": details,
                "scores": scores,
                "error_type": error_type,
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False, "n_pass": 0, "n_total": 0, "pass_rate": 0,
                "details": [], "scores": {}, "error_type": "timeout",
            }
        except Exception as e:
            return {
                "passed": False, "n_pass": 0, "n_total": 0, "pass_rate": 0,
                "details": [], "scores": {}, "error_type": "runtime_error",
            }


def find_skill_dir(scenario: dict) -> Path | None:
    """找到场景对应的 skill 目录"""
    domain = scenario["domain_group"]
    sid = scenario["id"]
    skill_dir = SKILLS_DIR / domain / sid
    if skill_dir.exists() and (skill_dir / "SKILL.md").exists():
        return skill_dir
    # 搜索所有领域目录
    for d in SKILLS_DIR.glob(f"*/{sid}"):
        if (d / "SKILL.md").exists():
            return d
    return None


def run_trial(trial: Trial, scenario: dict) -> dict:
    """执行单个试验"""
    t0 = time.time()

    # 读取任务和测试脚本
    task_text = Path(scenario["task_path"]).read_text()
    test_text = Path(scenario["test_path"]).read_text()

    # 准备 skill 内容
    skill_content = None
    skill_tokens = 0
    if trial.skill_level != "L0_none":
        skill_dir = find_skill_dir(scenario)
        if skill_dir:
            skill_content = serialize_skill_package(skill_dir, trial.skill_level)
            skill_tokens = estimate_tokens(skill_content)

    print(f"  [{trial.model:12s}] {trial.scenario_id:30s} {trial.condition:10s} ", end="", flush=True)

    # 构造 prompt
    system = ""
    if skill_content:
        system = ("You are given the following skill package to guide your work. "
                  "Follow its instructions carefully.\n\n"
                  f"<skill-package>\n{skill_content}\n</skill-package>")

    # 调用 LLM
    try:
        resp = call_llm(
            trial.model,
            [{"role": "user", "content": task_text}],
            system=system,
            max_tokens=8192,
            temperature=0.0,
            scenario=trial.scenario_id,
            condition=trial.condition,
        )
    except Exception as e:
        elapsed = time.time() - t0
        print(f"API ERROR (${0:.4f} {elapsed:.0f}s)")
        result = {
            "trial_key": trial.trial_key,
            "trial": asdict(trial),
            "domain": scenario["domain_group"],
            "difficulty": scenario["difficulty"],
            "skill_tokens": skill_tokens,
            "cost_usd": 0,
            "eval": {"passed": False, "n_pass": 0, "n_total": 0,
                     "pass_rate": 0, "error_type": "api_error"},
            "error": str(e),
        }
        append_result(result)
        return result

    # 提取代码
    code = extract_python_code(resp["text"])
    if not code:
        elapsed = time.time() - t0
        print(f"NO CODE (${resp['cost_usd']:.4f} {elapsed:.0f}s)")
        result = {
            "trial_key": trial.trial_key,
            "trial": asdict(trial),
            "domain": scenario["domain_group"],
            "difficulty": scenario["difficulty"],
            "skill_tokens": skill_tokens,
            "input_tokens": resp["input_tokens"],
            "output_tokens": resp["output_tokens"],
            "cost_usd": resp["cost_usd"],
            "eval": {"passed": False, "n_pass": 0, "n_total": 0,
                     "pass_rate": 0, "error_type": "format_error"},
        }
        append_result(result)
        return result

    # 执行评估
    ev = run_generated_code(code, test_text, timeout=90)
    elapsed = time.time() - t0

    print(f"{ev['n_pass']}/{ev['n_total']} ({ev['pass_rate']:.0%}) "
          f"${resp['cost_usd']:.4f} {elapsed:.0f}s "
          f"[err={ev.get('error_type', '?')}]")

    # 保存原始回复到 raw 目录
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIR / f"{trial.trial_key}.json"
    raw_file.write_text(json.dumps({
        "trial_key": trial.trial_key,
        "response": resp["text"],
        "code": code,
    }, ensure_ascii=False, indent=2))

    result = {
        "trial_key": trial.trial_key,
        "trial": asdict(trial),
        "domain": scenario["domain_group"],
        "difficulty": scenario["difficulty"],
        "skill_tokens": skill_tokens,
        "input_tokens": resp["input_tokens"],
        "output_tokens": resp["output_tokens"],
        "cost_usd": resp["cost_usd"],
        "eval": ev,
        "code_length": len(code),
    }
    append_result(result)
    return result


def main():
    parser = argparse.ArgumentParser(description="L0 vs L4 验证实验")
    parser.add_argument("--budget", type=float, default=30.0, help="预算上限")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS), help="模型列表")
    parser.add_argument("--ids", default=None, help="指定场景 ID")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划")
    args = parser.parse_args()

    # 加载场景
    data = json.loads(SELECTED_PATH.read_text())
    scenarios = {s["id"]: s for s in data["scenarios"]}

    # 筛选
    if args.ids:
        ids = set(s.strip() for s in args.ids.split(","))
        scenarios = {k: v for k, v in scenarios.items() if k in ids}

    models = [m.strip() for m in args.models.split(",")]

    # 构建 trials
    trials = []
    for sid, scenario in sorted(scenarios.items()):
        for model in models:
            # L0: 无 skill
            trials.append(Trial(sid, model, "L0_none", "L0_none"))
            # L4: 完整 skill
            skill_dir = find_skill_dir(scenario)
            if skill_dir:
                trials.append(Trial(sid, model, "L4_full", "L4_full"))

    # 跳过已完成的
    completed = load_completed()
    remaining = [t for t in trials if t.trial_key not in completed]

    # 预算估算
    est_cost = 0
    for t in remaining:
        rates = COST_PER_M.get(t.model, {"input": 3, "output": 15})
        est_cost += (3000 * rates["input"] + 3000 * rates["output"]) / 1_000_000

    print(f"场景数: {len(scenarios)}")
    print(f"模型: {models}")
    print(f"总 trials: {len(trials)}")
    print(f"已完成: {len(trials) - len(remaining)}")
    print(f"待运行: {len(remaining)}")
    print(f"预算: ${args.budget}")
    print(f"预估成本: ~${est_cost:.2f}")
    print(f"当前花费: ${total_cost():.4f}")

    # 统计 skill 覆盖
    n_with_skill = sum(1 for sid, s in scenarios.items() if find_skill_dir(s))
    print(f"有 skill 的场景: {n_with_skill}/{len(scenarios)}")

    if args.dry_run:
        print("\n[DRY RUN] 不执行")
        # 分模型显示
        for model in models:
            model_trials = [t for t in remaining if t.model == model]
            rates = COST_PER_M.get(model, {"input": 3, "output": 15})
            model_est = len(model_trials) * (3000 * rates["input"] + 3000 * rates["output"]) / 1_000_000
            print(f"  {model:15s}: {len(model_trials)} trials, ~${model_est:.2f}")
        return

    print(f"\n开始实验...\n")
    results = []

    for i, trial in enumerate(remaining):
        if total_cost() >= args.budget:
            print(f"\n预算已达上限 (${total_cost():.4f} >= ${args.budget})")
            break

        scenario = scenarios[trial.scenario_id]
        result = run_trial(trial, scenario)
        results.append(result)

    # 汇总
    valid = [r for r in results if r.get("eval")]
    gen_cost = sum(r.get("cost_usd", 0) for r in results)

    print(f"\n{'='*60}")
    print(f"实验汇总")
    print(f"{'='*60}")
    print(f"运行: {len(results)} trials")
    print(f"本次花费: ${gen_cost:.4f}")
    print(f"总花费: ${total_cost():.4f}")

    if valid:
        # 按条件统计
        for cond in ["L0_none", "L4_full"]:
            cond_results = [r for r in valid if r["trial"]["condition"] == cond]
            if cond_results:
                avg_pr = sum(r["eval"]["pass_rate"] for r in cond_results) / len(cond_results)
                print(f"  {cond}: {len(cond_results)} trials, avg pass_rate={avg_pr:.2%}")


if __name__ == "__main__":
    main()
