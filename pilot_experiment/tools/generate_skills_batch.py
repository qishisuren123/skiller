#!/usr/bin/env python3
"""
批量 Skill 生成工具：为场景生成 Agent Skills 标准格式的 skill 包。

支持两种方法:
A) pipeline: requirement-to-skill pipeline（模拟对话 → 提取 skill）
B) direct: 单次 LLM 调用直接生成完整 skill 包

用法:
    python tools/generate_skills_batch.py --scenarios S001,S002 --method direct --budget 10
    python tools/generate_skills_batch.py --scenarios all --method pipeline --budget 25
"""
import sys
import os
import json
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from config import (API_KEY, BASE_URL, MODELS, SKILLS_DIR,
                    log_cost, total_cost)
from lib.scenario_loader import load_all_scenarios

import anthropic

# ============ Direct 方法的 prompt ============

DIRECT_SKILL_PROMPT = """You are an expert at creating structured skill packages that guide AI assistants in completing specific coding tasks.

Given the following task description, create a complete skill package in the Agent Skills format.

Output format — respond with exactly these blocks:

```skill_md
# <Skill Title>

## Overview
<Brief description of what this skill helps accomplish>

## Workflow
<Step-by-step numbered instructions (5-7 steps)>

## Common Pitfalls
<3-5 pitfalls with solutions>

## Error Handling
<Key error handling strategies>

## Quick Reference
```python
<Key code snippet showing the critical algorithm>
```
```

```script_main
<A Python script (main.py) that implements the core algorithm for this task>
```

```reference_api
<API reference notes for key libraries used in this task>
```

```reference_examples
<1-2 complete code examples showing correct usage patterns>
```

IMPORTANT:
- Be specific to the task, not generic
- Include domain-specific knowledge and terminology
- Code snippets should be correct and runnable
- Pitfalls should address real issues a coder might face
- Only use standard scientific Python packages (numpy, pandas, scipy, h5py, PIL, matplotlib)

## Task Description:
{task}
"""

# ============ Pipeline 方法的 prompt ============

CONVERSATION_SIM_PROMPT = """Simulate a realistic conversation between a developer and an AI coding assistant working on the following task. The conversation should include:

1. Initial attempt with a subtle bug
2. Error discovery and debugging
3. A fix that introduces a new issue
4. Final correct solution
5. Discussion of edge cases and pitfalls

The conversation should be 10-15 exchanges (assistant responses should include code).

Task: {task}

Format each exchange as:
USER: <message>
ASSISTANT: <response>
"""

CONVERSATION_TO_SKILL_PROMPT = """Extract a structured skill package from the following conversation transcript. The skill should capture all the lessons learned, correct approaches, and pitfalls discovered.

Output format — respond with exactly these blocks:

```skill_md
# <Skill Title>

## Overview
<What this skill helps accomplish>

## Workflow
<Step-by-step instructions based on what worked>

## Common Pitfalls
<Pitfalls discovered during the conversation, with solutions>

## Error Handling
<Error handling insights from the debugging process>

## Quick Reference
```python
<Final correct code pattern>
```
```

```script_main
<Complete working script based on the final solution>
```

```reference_api
<API reference notes for libraries used>
```

```reference_examples
<Working code examples from the conversation>
```

## Conversation Transcript:
{conversation}
"""


def parse_skill_output(text: str) -> dict:
    """解析 LLM 输出为 skill 包文件内容"""
    files = {}

    # SKILL.md
    skill_md = re.search(r"```skill_md\s*\n(.*?)```", text, re.DOTALL)
    if skill_md:
        files["SKILL.md"] = skill_md.group(1).strip()

    # scripts/main.py
    script_main = re.search(r"```script_main\s*\n(.*?)```", text, re.DOTALL)
    if script_main:
        files["scripts/main.py"] = script_main.group(1).strip()

    # references/api_notes.md
    ref_api = re.search(r"```reference_api\s*\n(.*?)```", text, re.DOTALL)
    if ref_api:
        files["references/api_notes.md"] = ref_api.group(1).strip()

    # references/examples.md
    ref_examples = re.search(r"```reference_examples\s*\n(.*?)```", text, re.DOTALL)
    if ref_examples:
        files["references/examples.md"] = ref_examples.group(1).strip()

    return files


def save_skill_package(scenario_id: str, method: str, files: dict):
    """保存 skill 包到目录结构"""
    skill_dir = SKILLS_DIR / scenario_id / method
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "scripts").mkdir(exist_ok=True)
    (skill_dir / "references").mkdir(exist_ok=True)
    (skill_dir / "assets").mkdir(exist_ok=True)

    for rel_path, content in files.items():
        fp = skill_dir / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content + "\n")

    return skill_dir


def generate_direct(scenario_id: str, task: str, budget: float,
                    model: str = "sonnet") -> dict | None:
    """方法 B: 直接生成 skill 包"""
    if total_cost() >= budget:
        return None

    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    prompt = DIRECT_SKILL_PROMPT.format(task=task)

    try:
        resp = client.messages.create(
            model=MODELS[model],
            max_tokens=8192,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text
        cost = log_cost(model, resp.usage.input_tokens, resp.usage.output_tokens,
                        scenario_id, "skill_gen_direct")
        files = parse_skill_output(text)
        if "SKILL.md" not in files:
            return None
        return {"files": files, "cost": cost}
    except Exception as e:
        print(f"  ✗ API 错误: {e}")
        return None


def generate_pipeline(scenario_id: str, task: str, budget: float,
                      model: str = "sonnet") -> dict | None:
    """方法 A: pipeline 生成（模拟对话 → 提取 skill）"""
    if total_cost() >= budget:
        return None

    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    total_pipeline_cost = 0

    # 步骤 1: 生成模拟对话
    try:
        resp1 = client.messages.create(
            model=MODELS[model],
            max_tokens=8192,
            temperature=0.5,
            messages=[{"role": "user", "content": CONVERSATION_SIM_PROMPT.format(task=task)}],
        )
        conversation = resp1.content[0].text
        cost1 = log_cost(model, resp1.usage.input_tokens, resp1.usage.output_tokens,
                         scenario_id, "skill_gen_pipeline_conv")
        total_pipeline_cost += cost1
    except Exception as e:
        print(f"  ✗ 对话生成失败: {e}")
        return None

    # 步骤 2: 从对话提取 skill
    if total_cost() >= budget:
        return None

    try:
        resp2 = client.messages.create(
            model=MODELS[model],
            max_tokens=8192,
            temperature=0.2,
            messages=[{"role": "user", "content": CONVERSATION_TO_SKILL_PROMPT.format(conversation=conversation)}],
        )
        text = resp2.content[0].text
        cost2 = log_cost(model, resp2.usage.input_tokens, resp2.usage.output_tokens,
                         scenario_id, "skill_gen_pipeline_extract")
        total_pipeline_cost += cost2
    except Exception as e:
        print(f"  ✗ Skill 提取失败: {e}")
        return None

    files = parse_skill_output(text)
    if "SKILL.md" not in files:
        return None
    return {"files": files, "cost": total_pipeline_cost}


def main():
    parser = argparse.ArgumentParser(description="批量生成 skill 包")
    parser.add_argument("--scenarios", default="all", help="场景 ID 列表或 'all'")
    parser.add_argument("--method", default="direct", choices=["direct", "pipeline", "both"],
                        help="生成方法")
    parser.add_argument("--model", default="sonnet", help="生成模型")
    parser.add_argument("--budget", type=float, default=10.0, help="预算")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已有的 skill")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划")
    args = parser.parse_args()

    scenarios = load_all_scenarios()
    if args.scenarios != "all":
        keys = [k.strip() for k in args.scenarios.split(",")]
        scenarios = {k: v for k, v in scenarios.items() if k in keys}

    methods = ["direct", "pipeline"] if args.method == "both" else [args.method]

    print(f"场景数: {len(scenarios)}, 方法: {methods}, 模型: {args.model}")
    print(f"预算: ${args.budget}, 当前花费: ${total_cost():.4f}")

    if args.dry_run:
        for sid in sorted(scenarios):
            for m in methods:
                print(f"  {sid} / {m}")
        return

    generated = 0
    for sid in sorted(scenarios):
        task = scenarios[sid]["task"]
        for method in methods:
            skill_dir = SKILLS_DIR / sid / method
            if args.skip_existing and (skill_dir / "SKILL.md").exists():
                print(f"  跳过 {sid}/{method} (已存在)")
                continue

            print(f"\n[{sid}] {method} ...", end=" ", flush=True)

            if method == "direct":
                result = generate_direct(sid, task, args.budget, args.model)
            else:
                result = generate_pipeline(sid, task, args.budget, args.model)

            if result:
                save_skill_package(sid, method, result["files"])
                n_files = len(result["files"])
                print(f"✓ {n_files} files, ${result['cost']:.4f}")
                generated += 1
            else:
                print("✗")

    print(f"\n{'='*50}")
    print(f"生成完成: {generated} 个 skill 包")
    print(f"总花费: ${total_cost():.4f}")


if __name__ == "__main__":
    main()
