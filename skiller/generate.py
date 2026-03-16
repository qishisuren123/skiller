#!/usr/bin/env python3
"""
Step 2: 批量生成 Skill 包。
对 selected_scenarios.json 中的 50 个场景，调用 Sonnet 生成完整 L4 skill 包。

用法:
    python -m skiller.generate --dry-run
    python -m skiller.generate --budget 20
    python -m skiller.generate --budget 20 --ids S011,S012
    python -m skiller.generate --budget 20 --skip-existing
"""
import sys
import json
import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent))
from skiller.utils import call_llm, parse_skill_output, save_skill_package, total_cost, log_cost
from skiller.score import score_skill, score_summary

PROJECT_ROOT = Path(__file__).parent.parent
SELECTED_PATH = PROJECT_ROOT / "selected_scenarios.json"
SKILLS_DIR = PROJECT_ROOT / "skills"

# ========== Prompts ==========

CONVERSATION_PROMPT = """You are simulating a realistic multi-turn conversation between a domain scientist (user) and an AI coding assistant. The scientist needs help with the following data processing task.

TASK:
{task}

RULES for the conversation:
1. The conversation must have 12-16 turns (6-8 user + 6-8 assistant)
2. Include at least 5 error→fix iterations where:
   - The assistant provides code with a subtle but realistic bug
   - The user reports the actual error traceback
   - The assistant diagnoses and fixes the root cause
3. Error categories must include at least 3 different types:
   - Format incompatibility (file format, data structure issues)
   - API misuse (wrong method, deprecated function)
   - Data edge case (NaN, empty arrays, mismatched dimensions)
   - Scale issue (memory, performance)
   - Integration bug (in-place mutation, wrong scope)
4. The user should sound like a domain scientist, NOT a prompt engineer
5. The user discovers problems AFTER running code, not by predicting them
6. The final code must be complete with: all imports, argparse CLI, logging, __main__ block
7. All content must be in English

Format each turn as:
USER: <message>
ASSISTANT: <response with code>

Start the conversation now."""

SKILL_EXTRACTION_PROMPT = """You are extracting a structured skill package from a conversation transcript. The skill captures all lessons learned, correct approaches, and pitfalls discovered.

IMPORTANT FORMAT RULES:
- SKILL.md body must be < 5000 characters
- SKILL.md must include: Overview, When to Use, Inputs, Workflow, Error Handling, Common Pitfalls, Output Format
- Error Handling section MUST contain both "error" AND "handle" keywords
- Workflow must reference at least one file from scripts/ and references/
- scripts/main.py must be the COMPLETE final working code with argparse CLI
- references/pitfalls.md must have one section per error→fix iteration from the conversation

Output format — respond with exactly these blocks:

```skill_md
---
name: {name}
description: "{description}"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: {domain}
---

# {title}

[Full SKILL.md body here with all required sections including Overview, When to Use, Inputs, Workflow, Error Handling, Common Pitfalls, and Output Format. Must reference scripts/main.py and references/ directory.]
```

```script_main
[Complete Python script with imports, argparse, logging, main function, if __name__ == '__main__']
```

```script_requirements
[requirements.txt content]
```

```reference_workflow
[Detailed workflow steps with numbered list]
```

```reference_pitfalls
[One section per error→fix from conversation, with Error/Root Cause/Fix format]
```

```asset_example_output
[Example output showing what the tool produces]
```

## Conversation Transcript:
{conversation}"""


def load_scenarios():
    """加载已选场景"""
    data = json.loads(SELECTED_PATH.read_text())
    return data["scenarios"]


def generate_one_skill(scenario: dict, model: str = "sonnet") -> dict:
    """为单个场景生成 skill 包"""
    sid = scenario["id"]
    name = scenario["name"]
    domain = scenario["domain_group"]

    # 读取任务描述
    task_text = Path(scenario["task_path"]).read_text()

    print(f"\n{'='*60}")
    print(f"[{sid}] {name} ({domain})")
    print(f"{'='*60}")

    pipeline_cost = 0

    # Phase 1: 生成模拟对话
    print("  Phase 1: 生成对话...", end=" ", flush=True)
    try:
        resp1 = call_llm(
            model, [{"role": "user", "content": CONVERSATION_PROMPT.format(task=task_text)}],
            max_tokens=12000, temperature=0.5,
            scenario=sid, condition="skill_gen_conv",
        )
        conversation = resp1["text"]
        pipeline_cost += resp1["cost_usd"]
        print(f"OK ({len(conversation)} chars, ${resp1['cost_usd']:.4f})")
    except Exception as e:
        print(f"FAIL: {e}")
        return {"id": sid, "name": name, "success": False, "error": str(e)}

    # Phase 2: 提取 skill 包
    print("  Phase 2: 提取 skill...", end=" ", flush=True)
    title = name.replace("_", " ").title()
    try:
        resp2 = call_llm(
            model,
            [{"role": "user", "content": SKILL_EXTRACTION_PROMPT.format(
                name=name,
                description=task_text[:200],
                domain=domain,
                title=title,
                conversation=conversation,
            )}],
            max_tokens=12000, temperature=0.2,
            scenario=sid, condition="skill_gen_extract",
        )
        pipeline_cost += resp2["cost_usd"]
        print(f"OK (${resp2['cost_usd']:.4f})")
    except Exception as e:
        print(f"FAIL: {e}")
        return {"id": sid, "name": name, "success": False, "error": str(e), "cost": pipeline_cost}

    # 解析输出
    files = parse_skill_output(resp2["text"])
    if "SKILL.md" not in files:
        print("  FAIL: SKILL.md not found in output")
        return {"id": sid, "name": name, "success": False, "error": "parse_fail", "cost": pipeline_cost}

    # 保存到 skills/<domain_group>/<scenario_id>/
    skill_dir = SKILLS_DIR / domain / sid
    save_skill_package(skill_dir, files)
    print(f"  Saved: {skill_dir}/ ({len(files)} files)")

    # Phase 3: 质量评分
    print("  Phase 3: 评分...", end=" ", flush=True)
    score_result = score_skill(skill_dir)
    print(f"{score_result['score']}/{score_result['max']}")
    failed = [(n, r) for n, p, r in score_result["details"] if not p]
    if failed:
        print(f"    Failed: {', '.join(n for n, _ in failed)}")

    return {
        "id": sid,
        "name": name,
        "domain": domain,
        "success": True,
        "skill_dir": str(skill_dir),
        "n_files": len(files),
        "cost": pipeline_cost,
        "score": score_result["score"],
        "max_score": score_result["max"],
        "failed_checks": [n for n, _ in failed],
    }


def main():
    parser = argparse.ArgumentParser(description="批量生成 Skill 包")
    parser.add_argument("--budget", type=float, default=20.0, help="预算上限(美元)")
    parser.add_argument("--model", default="sonnet", help="生成模型")
    parser.add_argument("--ids", default=None, help="指定场景 ID (逗号分隔)")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已有 skill")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划")
    parser.add_argument("--workers", type=int, default=1, help="并发数")
    args = parser.parse_args()

    scenarios = load_scenarios()

    # 按 ID 筛选
    if args.ids:
        ids = set(s.strip() for s in args.ids.split(","))
        scenarios = [s for s in scenarios if s["id"] in ids]

    print(f"场景数: {len(scenarios)}")
    print(f"模型: {args.model}")
    print(f"预算: ${args.budget}")
    print(f"当前花费: ${total_cost():.4f}")
    print()

    for s in scenarios:
        tag = ""
        skill_dir = SKILLS_DIR / s["domain_group"] / s["id"]
        if args.skip_existing and (skill_dir / "SKILL.md").exists():
            tag = " [SKIP]"
        print(f"  {s['id']:30s} [{s['domain_group']:15s}] {s['name']}{tag}")

    if args.dry_run:
        cost_est = len(scenarios) * 0.30  # ~$0.30/skill
        print(f"\n预估成本: ~${cost_est:.0f}")
        print("[DRY RUN] 不执行")
        return

    print(f"\n开始生成...\n")
    results = []

    for s in scenarios:
        # 检查预算
        if total_cost() >= args.budget:
            print(f"\n预算已达上限 (${total_cost():.4f} >= ${args.budget})")
            break

        # 跳过已有
        skill_dir = SKILLS_DIR / s["domain_group"] / s["id"]
        if args.skip_existing and (skill_dir / "SKILL.md").exists():
            print(f"  跳过 {s['id']} (已存在)")
            # 仍然记录评分
            score_result = score_skill(skill_dir)
            results.append({
                "id": s["id"], "name": s["name"], "domain": s["domain_group"],
                "success": True, "skill_dir": str(skill_dir),
                "cost": 0, "score": score_result["score"], "max_score": score_result["max"],
                "skipped": True,
            })
            continue

        result = generate_one_skill(s, model=args.model)
        results.append(result)

    # 汇总
    successful = [r for r in results if r.get("success")]
    total_gen_cost = sum(r.get("cost", 0) for r in results)

    print(f"\n{'='*60}")
    print(f"生成汇总")
    print(f"{'='*60}")
    print(f"成功: {len(successful)}/{len(results)}")
    print(f"生成花费: ${total_gen_cost:.4f}")
    print(f"总花费: ${total_cost():.4f}")
    print()

    for r in results:
        if r.get("success"):
            score = f"{r.get('score', '?')}/{r.get('max_score', 24)}"
            skip = " (cached)" if r.get("skipped") else ""
            print(f"  {r['id']:30s} [{r.get('domain',''):15s}] {score:6s} ${r.get('cost',0):.4f}{skip}")
        else:
            print(f"  {r['id']:30s} FAILED: {r.get('error', 'unknown')}")

    # 保存评分结果
    scores_path = PROJECT_ROOT / "data" / "skill_scores.csv"
    import csv
    with open(scores_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario_id", "name", "domain", "score", "max_score",
                        "cost_usd", "n_files", "failed_checks"])
        for r in successful:
            writer.writerow([
                r["id"], r["name"], r.get("domain", ""),
                r.get("score", 0), r.get("max_score", 24),
                r.get("cost", 0), r.get("n_files", 0),
                "|".join(r.get("failed_checks", [])),
            ])
    print(f"\n评分已保存: {scores_path}")

    # 保存详细结果
    report_path = PROJECT_ROOT / "data" / "generation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"报告已保存: {report_path}")


if __name__ == "__main__":
    main()
