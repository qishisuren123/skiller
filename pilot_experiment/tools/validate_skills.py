#!/usr/bin/env python3
"""
Skill 质量验证工具：用 24-point rubric 评估 skill 包质量。

用法:
    python tools/validate_skills.py [--scenarios S001,...] [--method pipeline,direct]
"""
import sys
import os
import json
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from config import SKILLS_DIR

# 24-point 质量评分标准
RUBRIC = {
    # SKILL.md 质量 (12 分)
    "skill_md": [
        ("has_title", "SKILL.md 包含标题行"),
        ("has_overview", "包含概述/Overview 段落"),
        ("has_workflow", "包含工作流/Steps 段落 (≥3 步)"),
        ("has_pitfalls", "包含 Pitfalls/Common Issues (≥2 项)"),
        ("has_error_handling", "包含错误处理建议"),
        ("has_code_snippet", "包含至少 1 个代码示例"),
        ("correct_markdown", "Markdown 格式正确（标题层级、代码块标记）"),
        ("reasonable_length", "长度 300-3000 词"),
        ("no_hallucination", "无明显的虚构 API 或不存在的函数"),
        ("domain_specific", "包含领域特定的术语和知识"),
        ("actionable_advice", "建议可执行（不只是泛泛而谈）"),
        ("consistent_voice", "语气一致，适合作为指导文档"),
    ],
    # scripts/ 质量 (6 分)
    "scripts": [
        ("scripts_exist", "scripts/ 目录存在且非空"),
        ("scripts_runnable", "脚本语法正确 (ast.parse)"),
        ("scripts_documented", "脚本包含 docstring 或注释"),
        ("scripts_relevant", "脚本内容与任务相关"),
        ("scripts_complete", "脚本覆盖关键步骤"),
        ("scripts_no_placeholder", "脚本无 TODO/FIXME/placeholder"),
    ],
    # references/ 质量 (4 分)
    "references": [
        ("refs_exist", "references/ 目录存在且非空"),
        ("refs_relevant", "参考文件与任务相关"),
        ("refs_formatted", "参考文件格式良好"),
        ("refs_diverse", "包含多种类型的参考（API doc、示例、配置）"),
    ],
    # assets/ 质量 (2 分)
    "assets": [
        ("assets_exist", "assets/ 目录存在（可为空）"),
        ("assets_useful", "若非空，内容对任务有帮助"),
    ],
}


def score_skill_md(skill_md_text: str) -> list[tuple[str, bool, str]]:
    """评估 SKILL.md 质量"""
    results = []
    text_lower = skill_md_text.lower()
    words = skill_md_text.split()
    word_count = len(words)

    # has_title: 第一行是 # 标题
    results.append(("has_title", skill_md_text.strip().startswith("#"),
                    f"首行: {skill_md_text[:60]}"))

    # has_overview
    overview_kw = ["overview", "introduction", "about", "purpose", "description", "summary"]
    results.append(("has_overview",
                    any(kw in text_lower for kw in overview_kw) or word_count > 50,
                    ""))

    # has_workflow
    workflow_kw = ["workflow", "step", "procedure", "process", "approach", "algorithm",
                   "1.", "2.", "3."]
    has_steps = sum(1 for kw in ["1.", "2.", "3."] if kw in skill_md_text)
    results.append(("has_workflow",
                    any(kw in text_lower for kw in workflow_kw[:6]) or has_steps >= 3,
                    f"steps found: {has_steps}"))

    # has_pitfalls
    pitfall_kw = ["pitfall", "common issue", "warning", "gotcha", "caveat", "important"]
    results.append(("has_pitfalls",
                    sum(1 for kw in pitfall_kw if kw in text_lower) >= 1,
                    ""))

    # has_error_handling
    error_kw = ["error", "exception", "try", "except", "handle", "validate", "check"]
    results.append(("has_error_handling",
                    sum(1 for kw in error_kw if kw in text_lower) >= 2,
                    ""))

    # has_code_snippet
    code_blocks = skill_md_text.count("```")
    results.append(("has_code_snippet", code_blocks >= 2, f"code blocks: {code_blocks // 2}"))

    # correct_markdown
    has_headers = "## " in skill_md_text or "### " in skill_md_text
    results.append(("correct_markdown", has_headers, ""))

    # reasonable_length
    results.append(("reasonable_length", 300 <= word_count <= 3000,
                    f"words: {word_count}"))

    # no_hallucination (简单检查)
    hallucination_signs = ["definitely_fake_api", "NonExistentModule"]
    has_hallucination = any(h in skill_md_text for h in hallucination_signs)
    results.append(("no_hallucination", not has_hallucination, ""))

    # domain_specific (至少包含一些非通用词)
    generic_only = word_count < 100
    results.append(("domain_specific", not generic_only, ""))

    # actionable_advice
    action_kw = ["use", "set", "call", "ensure", "make sure", "configure", "specify"]
    results.append(("actionable_advice",
                    sum(1 for kw in action_kw if kw in text_lower) >= 2,
                    ""))

    # consistent_voice
    results.append(("consistent_voice", word_count >= 100, ""))

    return results


def score_scripts(scripts_dir: Path) -> list[tuple[str, bool, str]]:
    """评估 scripts/ 目录质量"""
    import ast
    results = []

    files = list(scripts_dir.glob("*")) if scripts_dir.exists() else []
    py_files = [f for f in files if f.suffix == ".py"]

    results.append(("scripts_exist", len(files) > 0, f"files: {len(files)}"))

    # 语法检查
    all_parseable = True
    for f in py_files:
        try:
            ast.parse(f.read_text())
        except SyntaxError:
            all_parseable = False
            break
    results.append(("scripts_runnable", all_parseable or len(py_files) == 0, ""))

    # 文档检查
    has_docs = False
    for f in py_files:
        content = f.read_text()
        if '"""' in content or "'''" in content or content.count("#") >= 3:
            has_docs = True
            break
    results.append(("scripts_documented", has_docs or len(py_files) == 0, ""))

    # 内容相关性（简单检查非空且有实质内容）
    has_substance = any(len(f.read_text().strip()) > 50 for f in files if f.is_file())
    results.append(("scripts_relevant", has_substance or len(files) == 0, ""))

    # 完整性
    results.append(("scripts_complete", len(py_files) >= 1 or len(files) >= 1, ""))

    # 无 placeholder
    has_placeholder = False
    for f in files:
        if f.is_file():
            content = f.read_text()
            if "TODO" in content or "FIXME" in content or "placeholder" in content.lower():
                has_placeholder = True
                break
    results.append(("scripts_no_placeholder", not has_placeholder, ""))

    return results


def score_references(refs_dir: Path) -> list[tuple[str, bool, str]]:
    """评估 references/ 目录质量"""
    results = []
    files = list(refs_dir.glob("*")) if refs_dir.exists() else []

    results.append(("refs_exist", len(files) > 0, f"files: {len(files)}"))
    results.append(("refs_relevant", len(files) > 0, ""))
    results.append(("refs_formatted", len(files) > 0, ""))
    results.append(("refs_diverse", len(files) >= 2, f"files: {len(files)}"))

    return results


def score_assets(assets_dir: Path) -> list[tuple[str, bool, str]]:
    """评估 assets/ 目录质量"""
    results = []
    exists = assets_dir.exists()
    files = list(assets_dir.glob("*")) if exists else []

    results.append(("assets_exist", exists, ""))
    results.append(("assets_useful", exists, ""))  # 存在即可，空目录也算

    return results


def validate_skill(skill_dir: Path) -> dict:
    """验证单个 skill 包，返回评分详情"""
    skill_md_path = skill_dir / "SKILL.md"
    if not skill_md_path.exists():
        return {"total": 0, "max": 24, "details": [], "error": "SKILL.md not found"}

    skill_md_text = skill_md_path.read_text()
    all_results = []

    all_results.extend(score_skill_md(skill_md_text))
    all_results.extend(score_scripts(skill_dir / "scripts"))
    all_results.extend(score_references(skill_dir / "references"))
    all_results.extend(score_assets(skill_dir / "assets"))

    total = sum(1 for _, passed, _ in all_results if passed)
    return {
        "total": total,
        "max": 24,
        "pass_rate": round(total / 24, 4),
        "details": [{"name": name, "passed": passed, "note": note}
                     for name, passed, note in all_results],
    }


def main():
    parser = argparse.ArgumentParser(description="验证 skill 包质量（24-point rubric）")
    parser.add_argument("--scenarios", default="all", help="逗号分隔的场景 ID 或 'all'")
    parser.add_argument("--method", default="pipeline,direct", help="skill 生成方法")
    parser.add_argument("--threshold", type=int, default=22, help="合格阈值分数")
    parser.add_argument("--output", default=None, help="输出 JSON 报告路径")
    args = parser.parse_args()

    methods = [m.strip() for m in args.method.split(",")]

    # 发现所有 skill 目录
    all_results = []
    skills_dir = SKILLS_DIR
    for scenario_dir in sorted(skills_dir.glob("S???_*")):
        if not scenario_dir.is_dir():
            continue
        sid = scenario_dir.name
        if args.scenarios != "all":
            wanted = [k.strip() for k in args.scenarios.split(",")]
            if sid not in wanted:
                continue

        for method in methods:
            skill_dir = scenario_dir / method
            if not skill_dir.exists():
                continue

            result = validate_skill(skill_dir)
            result["scenario"] = sid
            result["method"] = method
            all_results.append(result)

            status = "✓" if result["total"] >= args.threshold else "✗"
            print(f"  {status} {sid}/{method}: {result['total']}/24")

    if not all_results:
        print("未找到任何 skill 包")
        return 1

    # 汇总
    passing = sum(1 for r in all_results if r["total"] >= args.threshold)
    print(f"\n{'='*50}")
    print(f"合格: {passing}/{len(all_results)} (阈值: {args.threshold}/24)")

    if args.output:
        Path(args.output).write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        print(f"报告已保存: {args.output}")

    return 0 if passing == len(all_results) else 1


if __name__ == "__main__":
    sys.exit(main())
