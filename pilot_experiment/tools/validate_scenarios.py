#!/usr/bin/env python3
"""
场景验证工具：验证所有 scenarios/S???_*/ 下的 test_script.py 可独立运行。

用法:
    python tools/validate_scenarios.py [--scenarios S001,S002,...] [--timeout 90]
"""
import sys
import os
import argparse
import subprocess
import tempfile
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from lib.scenario_loader import load_all_scenarios

# 测试脚本用的 Python 解释器（需要 numpy, pandas, scipy 等）
PYTHON_EXE = "/home/renyiming/.conda/envs/pilot_exp/bin/python"


def validate_scenario(scenario_id: str, scenario: dict, timeout: int = 90, verbose: bool = False) -> dict:
    """
    验证单个场景的 test_script.py 可以独立运行。
    创建一个空的 generated.py（模拟 LLM 未生成代码的情况），
    确认 test_script 至少能运行并输出 PASS/FAIL 行。
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入空的 generated.py（测试脚本需要它存在）
        (Path(tmpdir) / "generated.py").write_text("# empty placeholder\n")
        # 写入测试脚本
        test_path = Path(tmpdir) / "test_check.py"
        test_path.write_text(scenario["test"])

        try:
            result = subprocess.run(
                [PYTHON_EXE, str(test_path)],
                capture_output=True, text=True, timeout=timeout,
                cwd=tmpdir,
                env={
                    "PATH": "/home/renyiming/.conda/envs/pilot_exp/bin:"
                            "/root/miniconda3/envs/pilot_exp/bin:/usr/bin:/bin",
                    "HOME": tmpdir,
                    "PYTHONPATH": tmpdir,
                    "TMPDIR": tmpdir,
                    "HDF5_USE_FILE_LOCKING": "FALSE",
                }
            )
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            # 解析输出
            n_pass = stdout.count("PASS:")
            n_fail = stdout.count("FAIL:")
            n_score = stdout.count("SCORE:")
            n_total = n_pass + n_fail

            status = "ok" if n_total > 0 else "no_output"
            if result.returncode != 0 and n_total == 0:
                status = "crash"

            info = {
                "scenario_id": scenario_id,
                "status": status,
                "returncode": result.returncode,
                "n_pass": n_pass,
                "n_fail": n_fail,
                "n_score": n_score,
                "n_total": n_total,
            }
            if verbose or status != "ok":
                info["stderr_tail"] = stderr[-500:] if stderr else ""

            return info

        except subprocess.TimeoutExpired:
            return {
                "scenario_id": scenario_id,
                "status": "timeout",
                "returncode": -1,
                "n_total": 0,
            }
        except Exception as e:
            return {
                "scenario_id": scenario_id,
                "status": "error",
                "returncode": -1,
                "error": str(e),
                "n_total": 0,
            }


def main():
    parser = argparse.ArgumentParser(description="验证所有场景 test_script 可独立运行")
    parser.add_argument("--scenarios", default="all", help="逗号分隔的场景 ID 或 'all'")
    parser.add_argument("--timeout", type=int, default=90, help="单场景超时（秒）")
    parser.add_argument("--verbose", action="store_true", help="显示详细输出")
    parser.add_argument("--output", default=None, help="输出 JSON 报告路径")
    args = parser.parse_args()

    all_scenarios = load_all_scenarios()
    if args.scenarios != "all":
        keys = [k.strip() for k in args.scenarios.split(",")]
        all_scenarios = {k: v for k, v in all_scenarios.items() if k in keys}

    print(f"验证 {len(all_scenarios)} 个场景...")
    print(f"超时: {args.timeout}s")
    print()

    results = []
    ok_count = 0
    for sid, scenario in sorted(all_scenarios.items()):
        print(f"  [{sid}] ", end="", flush=True)
        r = validate_scenario(sid, scenario, args.timeout, args.verbose)
        results.append(r)

        if r["status"] == "ok":
            print(f"✓ {r['n_fail']}/{r['n_total']} FAIL, {r['n_score']} SCORE")
            ok_count += 1
        else:
            print(f"✗ {r['status']}")
            if "stderr_tail" in r:
                for line in r["stderr_tail"].split("\n")[-3:]:
                    print(f"    {line}")

    print(f"\n{'='*50}")
    print(f"结果: {ok_count}/{len(results)} 场景可运行")

    # 按状态汇总
    from collections import Counter
    status_counts = Counter(r["status"] for r in results)
    for s, c in status_counts.most_common():
        print(f"  {s}: {c}")

    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False))
        print(f"\n报告已保存: {args.output}")

    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
