#!/usr/bin/env python3
"""
用增强后的测试脚本重跑所有 results/raw/S*__*.json 中的代码。
零 API 花费，获得更丰富的评估数据（更多测试项 + SCORE 连续指标）。
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from evaluator_v2 import run_generated_code, compute_code_metrics
from scenarios_v2 import SCENARIOS
from config import RESULTS_DIR, RAW_DIR


def extract_python_code(text: str) -> str:
    """从 LLM 回复中提取 Python 代码"""
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        blocks = re.findall(r"```\s*\n(.*?)```", text, re.DOTALL)
    return max(blocks, key=len).strip() if blocks else ""


def re_evaluate_all(raw_dir: Path = RAW_DIR, output_path: Path = None):
    """
    重新评估所有原始结果。
    对每个 raw JSON:
      1. 提取代码
      2. 用增强后的测试脚本重跑
      3. 保存新的评估结果（包含 SCORE 指标和 error_type）
    """
    if output_path is None:
        output_path = RESULTS_DIR / "re_evaluated_results.json"

    results = []
    files = sorted(raw_dir.glob("S*__*.json"))
    print(f"Found {len(files)} raw result files to re-evaluate")
    print("=" * 70)

    for i, f in enumerate(files):
        data = json.loads(f.read_text())
        scenario_key = data.get("scenario", "")
        condition = data.get("condition", "")
        model = data.get("model", "")
        response = data.get("response", "")

        # 跳过 skill_gen 条目（这些是生成 skill 的，不是代码生成）
        if "skill_gen" in condition:
            continue

        if scenario_key not in SCENARIOS:
            print(f"  [{i+1}/{len(files)}] SKIP {f.name} - unknown scenario")
            continue

        code = extract_python_code(response) if response else ""
        if not code:
            print(f"  [{i+1}/{len(files)}] SKIP {f.name} - no code extracted")
            result = {
                "file": f.name,
                "scenario": scenario_key,
                "condition": condition,
                "model": model,
                "eval": {"passed": False, "n_pass": 0, "n_total": 0, "pass_rate": 0,
                         "error_type": "format_error", "scores": {}},
                "code_metrics": {},
                "code_length": 0,
            }
            results.append(result)
            continue

        # 用增强后的测试重跑
        test_script = SCENARIOS[scenario_key]["test"]
        t0 = time.time()
        ev = run_generated_code(code, test_script, timeout=90)
        metrics = compute_code_metrics(code)
        elapsed = time.time() - t0

        print(f"  [{i+1}/{len(files)}] {f.name:60s} "
              f"{ev['n_pass']}/{ev['n_total']} ({ev['pass_rate']:.0%}) "
              f"type={ev.get('error_type', '?'):15s} "
              f"scores={len(ev.get('scores', {}))} "
              f"{elapsed:.0f}s")

        result = {
            "file": f.name,
            "scenario": scenario_key,
            "condition": condition,
            "model": model,
            "eval": ev,
            "code_metrics": metrics,
            "code_length": len(code),
        }
        results.append(result)

    # 保存
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    print(f"\n{'=' * 70}")
    print(f"Re-evaluation complete: {len(results)} results")
    print(f"Saved to {output_path}")

    # 打印汇总
    print(f"\n--- Summary ---")
    from collections import Counter
    error_types = Counter(r["eval"].get("error_type", "unknown") for r in results)
    print(f"Error type distribution:")
    for etype, count in error_types.most_common():
        print(f"  {etype:20s}: {count:3d} ({count/len(results):.0%})")

    # SCORE 指标汇总
    all_scores = {}
    for r in results:
        for k, v in r["eval"].get("scores", {}).items():
            if isinstance(v, (int, float)):
                all_scores.setdefault(k, []).append(v)
    if all_scores:
        print(f"\nSCORE metrics summary:")
        for k, vals in sorted(all_scores.items()):
            import numpy as np
            print(f"  {k:30s}: mean={np.mean(vals):.3f} std={np.std(vals):.3f} n={len(vals)}")

    return results


if __name__ == "__main__":
    re_evaluate_all()
