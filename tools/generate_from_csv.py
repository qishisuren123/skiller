#!/usr/bin/env python3
"""
从CSV需求表中筛选合理需求，使用 requirement-to-skill pipeline 生成 skill 包。

流程（遵循 requirement-to-skill 的 5 阶段方法论）：
  Phase 1: 需求分析 → 结构化分解
  Phase 2: 模拟对话构建（含 error→fix 迭代）
  Phase 3: 从对话提取 skill 包
  Phase 4: 质量验证
  Phase 5: 代码可用性测试

用法:
    python generate_from_csv.py --dry-run          # 只显示计划
    python generate_from_csv.py --budget 20        # 实际运行
    python generate_from_csv.py --ids 3,11,13      # 指定编号
"""
import sys
import os
import json
import re
import ast
import argparse
import textwrap
import subprocess
from pathlib import Path

# 添加 pilot_experiment 到路径
PILOT_ROOT = Path(__file__).parent.parent / "pilot_experiment"
sys.path.insert(0, str(PILOT_ROOT))
from config import API_KEY, BASE_URL, MODELS, log_cost, total_cost

import anthropic

# ============ 配置 ============
OUTPUT_DIR = Path(__file__).parent  # generated_skills/
CSV_PATH = PILOT_ROOT / "科学数据处理需求整理_数据表_表格.csv"

# 筛选出的合理需求（排除已有skill和24-28号）
SELECTED_REQUIREMENTS = {
    3: {
        "name": "spatial-transcriptomics-preprocess",
        "submitter": "Researcher C",
        "domain": "生命科学",
        "requirement": (
            "对DLPFC空转数据集进行标准化预处理。数据由.csv, .h5, .txt等格式组成，"
            "需要经过整合、质量控制、归一化、高变基因选择、降维聚类等操作。"
            "使用scanpy和STAGATE_pyG工具包。数据来源: https://github.com/LieberInstitute/HumanPilot"
        ),
        "libraries": "scanpy, anndata, STAGATE_pyG, pandas, numpy, matplotlib",
    },
    11: {
        "name": "swissprot-protein-parser",
        "submitter": "Researcher D",
        "domain": "生命科学",
        "requirement": (
            "解析SwissProt数据库的JSON格式蛋白质描述数据。SwissProt包含大量自然语言描述的"
            "蛋白质功能信息，格式复杂、信息杂乱。需要提取蛋白质ID、名称、功能描述、"
            "GO注释、亚细胞定位、序列信息等结构化字段，输出为标准化的CSV/JSON格式。"
            "工具: mmseqs/foldseek可用于后续序列搜索。"
        ),
        "libraries": "json, pandas, numpy, re",
    },
    13: {
        "name": "proteomics-enrichment-analysis",
        "submitter": "Researcher E",
        "domain": "生命科学",
        "requirement": (
            "对差异蛋白原始实验数据进行富集分析和数据处理。包括：读取差异蛋白表达矩阵，"
            "进行统计检验(t-test/limma)筛选差异蛋白，对差异蛋白进行GO富集分析和KEGG通路分析，"
            "生成富集结果表格和可视化（气泡图、柱状图）。同样适用于多组学数据输入。"
            "工具: limma, KEGG API, STRING API, numpy, pandas, scipy, matplotlib。"
        ),
        "libraries": "pandas, numpy, scipy, matplotlib, requests, goatools",
    },
    15: {
        "name": "pride-proteomics-downloader",
        "submitter": "Researcher F",
        "domain": "生命科学",
        "requirement": (
            "从PRIDE数据库(https://www.ebi.ac.uk/pride/)下载符合条件的蛋白质组学项目数据。"
            "筛选条件：项目已有发表论文(Publication字段)，Data Processing Protocol包含Fragpipe。"
            "需要使用PRIDE REST API搜索项目、获取项目详情、筛选符合条件的项目，"
            "下载项目中的原始数据文件(.raw/.mzML)，并下载关联的论文PDF。"
            "API文档: https://www.ebi.ac.uk/pride/markdownpage/prideapi"
        ),
        "libraries": "requests, pandas, tqdm, pathlib",
    },
    17: {
        "name": "fits-aperture-photometry",
        "submitter": "Researcher G",
        "domain": "天文科学",
        "requirement": (
            "对天文FITS图像数据执行孔径测光(Aperture Photometry)。"
            "功能：支持固定孔径、FWHM自适应孔径、椭圆孔径；支持局部天光环估计与坏像元掩膜；"
            "批量输出目标星+比较星+检验星的测光结果。"
            "数据需求：每帧需有EXPTIME、滤光片、增益/读噪、WCS信息。"
            "质量：同一夜同一目标在不同孔径策略下结果可追溯；给出孔径修正(curve of growth)。"
            "验收：亮星区与参考星表零点偏差可控；与PSF测光差异在0.02-0.03 mag内。"
            "工具: Photutils.aperture, SEP, astropy.io.fits, astropy.wcs"
        ),
        "libraries": "astropy, photutils, sep, numpy, matplotlib",
    },
}

# ============ Phase 2: 对话模拟 Prompt ============
CONVERSATION_PROMPT = """You are simulating a realistic multi-turn conversation between a domain scientist (user) and an AI coding assistant. The scientist needs help with the following data processing task.

TASK: {requirement}

LIBRARIES: {libraries}

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

# ============ Phase 3: Skill 提取 Prompt ============
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
description: "{description} Use this skill when {trigger}."
license: MIT
compatibility: "{compatibility}"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# {title}

[Full SKILL.md body here with all required sections]
```

```script_main
[Complete Python script with imports, argparse, logging, main function]
```

```script_requirements
[requirements.txt content]
```

```reference_workflow
[Detailed workflow steps]
```

```reference_pitfalls
[One section per error→fix from conversation, with Error/Root Cause/Fix format]
```

```asset_example_output
[Example output showing what the tool produces]
```

## Conversation Transcript:
{conversation}
"""


def parse_skill_output_v2(text: str) -> dict:
    """解析 LLM 输出为 skill 包文件"""
    files = {}

    # SKILL.md
    m = re.search(r"```skill_md\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["SKILL.md"] = m.group(1).strip()

    # scripts/main.py
    m = re.search(r"```script_main\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["scripts/main.py"] = m.group(1).strip()

    # scripts/requirements.txt
    m = re.search(r"```script_requirements\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["scripts/requirements.txt"] = m.group(1).strip()

    # references/workflow.md
    m = re.search(r"```reference_workflow\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["references/workflow.md"] = m.group(1).strip()

    # references/pitfalls.md
    m = re.search(r"```reference_pitfalls\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["references/pitfalls.md"] = m.group(1).strip()

    # assets/example_output.md
    m = re.search(r"```asset_example_output\s*\n(.*?)```", text, re.DOTALL)
    if m:
        files["assets/example_output.md"] = m.group(1).strip()

    return files


def save_skill(name: str, files: dict) -> Path:
    """保存 skill 包到目录"""
    skill_dir = OUTPUT_DIR / name
    for subdir in ["scripts", "references", "assets"]:
        (skill_dir / subdir).mkdir(parents=True, exist_ok=True)

    for rel_path, content in files.items():
        fp = skill_dir / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content + "\n", encoding="utf-8")

    return skill_dir


def validate_skill(skill_dir: Path) -> dict:
    """简化版质量验证（基于 validate_skills.py 的 rubric）"""
    results = {"score": 0, "max": 24, "details": []}

    # 检查 SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        results["details"].append(("SKILL.md exists", False, "文件不存在"))
        return results

    text = skill_md.read_text(encoding="utf-8")
    text_lower = text.lower()
    words = text.split()

    checks = [
        # SKILL.md 结构 (12分)
        ("has_title", text.strip().startswith("#") or text.strip().startswith("---")),
        ("has_overview", any(kw in text_lower for kw in ["overview", "description", "purpose"])),
        ("has_workflow", any(kw in text_lower for kw in ["workflow", "step", "procedure"]) or "1." in text),
        ("has_pitfalls", any(kw in text_lower for kw in ["pitfall", "common issue", "warning", "caveat"])),
        ("has_error_handling", "error" in text_lower and any(kw in text_lower for kw in ["handle", "troubleshoot", "fallback", "catch"])),
        ("has_code_snippet", text.count("```") >= 2),
        ("correct_markdown", text.count("#") >= 3),
        ("reasonable_length", 100 <= len(words) <= 5000),
        ("no_todo_placeholder", "[TODO" not in text),
        ("domain_specific", len(words) > 50),
        ("references_scripts", "scripts/" in text or "main.py" in text),
        ("references_refs", "references/" in text or "pitfalls" in text_lower),
    ]

    for name, passed in checks:
        results["details"].append((name, passed))
        if passed:
            results["score"] += 1

    # 检查 scripts/ (6分)
    scripts_dir = skill_dir / "scripts"
    main_py = scripts_dir / "main.py"
    script_checks = [
        ("scripts_exist", scripts_dir.exists() and any(scripts_dir.iterdir())),
        ("main_py_exists", main_py.exists()),
        ("main_py_parseable", False),  # 默认失败
        ("main_py_has_argparse", False),
        ("main_py_has_main", False),
        ("requirements_exist", (scripts_dir / "requirements.txt").exists()),
    ]

    if main_py.exists():
        code = main_py.read_text(encoding="utf-8")
        try:
            ast.parse(code)
            script_checks[2] = ("main_py_parseable", True)
        except SyntaxError:
            pass
        script_checks[3] = ("main_py_has_argparse", "argparse" in code or "ArgumentParser" in code)
        script_checks[4] = ("main_py_has_main", "__name__" in code or "def main" in code)

    for name, passed in script_checks:
        results["details"].append((name, passed))
        if passed:
            results["score"] += 1

    # 检查 references/ (4分)
    refs_dir = skill_dir / "references"
    ref_checks = [
        ("refs_exist", refs_dir.exists() and any(refs_dir.iterdir()) if refs_dir.exists() else False),
        ("workflow_exists", (refs_dir / "workflow.md").exists()),
        ("pitfalls_exists", (refs_dir / "pitfalls.md").exists()),
        ("refs_nonempty", any(f.stat().st_size > 50 for f in refs_dir.iterdir()) if refs_dir.exists() and any(refs_dir.iterdir()) else False),
    ]
    for name, passed in ref_checks:
        results["details"].append((name, passed))
        if passed:
            results["score"] += 1

    # 检查 assets/ (2分)
    assets_dir = skill_dir / "assets"
    asset_checks = [
        ("assets_exist", assets_dir.exists()),
        ("example_output_exists", (assets_dir / "example_output.md").exists()),
    ]
    for name, passed in asset_checks:
        results["details"].append((name, passed))
        if passed:
            results["score"] += 1

    return results


def test_skill_code(skill_dir: Path) -> dict:
    """测试 scripts/main.py 的可用性"""
    main_py = skill_dir / "scripts" / "main.py"
    results = {"help_test": False, "import_test": False, "errors": []}

    if not main_py.exists():
        results["errors"].append("scripts/main.py 不存在")
        return results

    # Test 1: --help
    try:
        r = subprocess.run(
            [sys.executable, str(main_py), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        results["help_test"] = r.returncode == 0
        if r.returncode != 0:
            results["errors"].append(f"--help 失败: {r.stderr[:300]}")
    except Exception as e:
        results["errors"].append(f"--help 异常: {e}")

    # Test 2: 语法/导入检查
    try:
        code = main_py.read_text(encoding="utf-8")
        ast.parse(code)
        results["import_test"] = True
    except SyntaxError as e:
        results["errors"].append(f"语法错误: {e}")

    return results


def generate_skill_pipeline(req_id: int, req: dict, model: str = "sonnet",
                            budget: float = 50.0) -> dict | None:
    """使用 requirement-to-skill pipeline 生成一个 skill"""
    name = req["name"]
    print(f"\n{'='*60}")
    print(f"[#{req_id}] {name} ({req['submitter']}, {req['domain']})")
    print(f"{'='*60}")

    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    total_pipeline_cost = 0

    # Phase 2: 生成模拟对话
    print("  Phase 2: 生成对话...", end=" ", flush=True)
    try:
        resp1 = client.messages.create(
            model=MODELS[model],
            max_tokens=12000,
            temperature=0.5,
            messages=[{"role": "user", "content": CONVERSATION_PROMPT.format(
                requirement=req["requirement"],
                libraries=req["libraries"],
            )}],
        )
        conversation = resp1.content[0].text
        cost1 = log_cost(model, resp1.usage.input_tokens, resp1.usage.output_tokens,
                         f"csv_{req_id}", "skill_gen_conversation")
        total_pipeline_cost += cost1
        print(f"✓ ({len(conversation)} chars, ${cost1:.4f})")
    except Exception as e:
        print(f"✗ {e}")
        return None

    # Phase 3: 从对话提取 skill
    print("  Phase 3: 提取 skill...", end=" ", flush=True)
    title = name.replace("-", " ").title()
    try:
        resp2 = client.messages.create(
            model=MODELS[model],
            max_tokens=12000,
            temperature=0.2,
            messages=[{"role": "user", "content": SKILL_EXTRACTION_PROMPT.format(
                name=name,
                description=req["requirement"][:200],
                trigger=f"the user needs to {req['requirement'][:100].lower()}",
                compatibility=f"Python >=3.9; {req['libraries']}",
                title=title,
                conversation=conversation,
            )}],
        )
        text = resp2.content[0].text
        cost2 = log_cost(model, resp2.usage.input_tokens, resp2.usage.output_tokens,
                         f"csv_{req_id}", "skill_gen_extraction")
        total_pipeline_cost += cost2
        print(f"✓ (${cost2:.4f})")
    except Exception as e:
        print(f"✗ {e}")
        return None

    # 解析输出
    files = parse_skill_output_v2(text)
    if "SKILL.md" not in files:
        print("  ✗ 解析失败：未找到 SKILL.md")
        return None

    # 保存
    skill_dir = save_skill(name, files)
    print(f"  Phase 3: 保存到 {skill_dir}/  ({len(files)} 个文件)")

    # Phase 4: 验证
    print("  Phase 4: 质量验证...", end=" ", flush=True)
    validation = validate_skill(skill_dir)
    score = validation["score"]
    max_score = validation["max"]
    print(f"{score}/{max_score}")

    failed = [(n, p) for n, p in validation["details"] if not p]
    if failed:
        print(f"    失败项: {', '.join(n for n, _ in failed)}")

    # Phase 5: 代码测试
    print("  Phase 5: 代码测试...", end=" ", flush=True)
    code_test = test_skill_code(skill_dir)
    help_ok = "✓" if code_test["help_test"] else "✗"
    import_ok = "✓" if code_test["import_test"] else "✗"
    print(f"--help {help_ok}, syntax {import_ok}")
    if code_test["errors"]:
        for err in code_test["errors"]:
            print(f"    {err}")

    return {
        "id": req_id,
        "name": name,
        "skill_dir": str(skill_dir),
        "files": list(files.keys()),
        "cost": total_pipeline_cost,
        "validation_score": f"{score}/{max_score}",
        "help_test": code_test["help_test"],
        "import_test": code_test["import_test"],
        "errors": code_test["errors"],
    }


def main():
    parser = argparse.ArgumentParser(description="从CSV需求生成skill包")
    parser.add_argument("--ids", default=None, help="指定需求编号(逗号分隔)，默认全部")
    parser.add_argument("--model", default="sonnet", help="生成模型 (default: sonnet)")
    parser.add_argument("--budget", type=float, default=20.0, help="预算上限(美元)")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划")
    parser.add_argument("--skip-existing", action="store_true", help="跳过已有skill")
    args = parser.parse_args()

    # 筛选需求
    if args.ids:
        ids = [int(x.strip()) for x in args.ids.split(",")]
        reqs = {k: v for k, v in SELECTED_REQUIREMENTS.items() if k in ids}
    else:
        reqs = SELECTED_REQUIREMENTS

    print(f"需求数: {len(reqs)}, 模型: {args.model}, 预算: ${args.budget}")
    print(f"当前花费: ${total_cost():.4f}")
    print()

    for rid, req in sorted(reqs.items()):
        print(f"  #{rid:2d} [{req['domain']:4s}] {req['name']} ({req['submitter']})")

    if args.dry_run:
        print("\n[DRY RUN] 不执行实际生成")
        return

    print(f"\n开始生成...\n")
    results = []

    for rid, req in sorted(reqs.items()):
        if args.skip_existing and (OUTPUT_DIR / req["name"] / "SKILL.md").exists():
            print(f"  跳过 #{rid} {req['name']} (已存在)")
            continue

        if total_cost() >= args.budget:
            print(f"\n⚠ 预算已达上限 (${total_cost():.4f} >= ${args.budget})")
            break

        result = generate_skill_pipeline(rid, req, model=args.model, budget=args.budget)
        if result:
            results.append(result)

    # 汇总
    print(f"\n{'='*60}")
    print(f"生成汇总")
    print(f"{'='*60}")
    print(f"成功: {len(results)}/{len(reqs)}")
    print(f"总花费: ${sum(r['cost'] for r in results):.4f}")
    print()

    for r in results:
        score_emoji = "✓" if r["validation_score"].startswith("24") or int(r["validation_score"].split("/")[0]) >= 20 else "△"
        help_emoji = "✓" if r["help_test"] else "✗"
        print(f"  #{r['id']:2d} {r['name']:40s} 质量:{r['validation_score']} {score_emoji}  --help:{help_emoji}  ${r['cost']:.4f}")

    # 保存结果
    report_path = OUTPUT_DIR / "csv_generation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    main()
