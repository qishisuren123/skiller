#!/usr/bin/env python3
"""
24 分 Skill 质量评分 rubric。
"""
import ast
from pathlib import Path


def score_skill(skill_dir: Path) -> dict:
    """
    对 skill 包进行 24 分质量评分。

    返回: {"score": int, "max": 24, "details": [(name, passed, reason)]}
    """
    results = {"score": 0, "max": 24, "details": []}

    def check(name, passed, reason=""):
        results["details"].append((name, passed, reason))
        if passed:
            results["score"] += 1

    # === SKILL.md (12 分) ===
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        check("skill_md_exists", False, "SKILL.md not found")
        return results

    text = skill_md.read_text(encoding="utf-8")
    text_lower = text.lower()
    words = text.split()

    check("has_title", text.strip().startswith("#") or text.strip().startswith("---"))
    check("has_overview", any(kw in text_lower for kw in ["overview", "description", "purpose"]))
    check("has_workflow", any(kw in text_lower for kw in ["workflow", "step", "procedure"]) or "1." in text)
    check("has_pitfalls", any(kw in text_lower for kw in ["pitfall", "common issue", "warning", "caveat"]))
    check("has_error_handling",
          "error" in text_lower and any(kw in text_lower for kw in ["handle", "troubleshoot", "fallback", "catch"]))
    check("has_code_snippet", text.count("```") >= 2)
    check("correct_markdown", text.count("#") >= 3)
    check("reasonable_length", 100 <= len(words) <= 5000)
    check("no_placeholder", "[TODO" not in text and "FIXME" not in text)
    check("domain_specific", len(words) > 50)
    check("references_scripts", "scripts/" in text or "main.py" in text)
    check("references_refs", "references/" in text or "pitfalls" in text_lower)

    # === scripts/ (6 分) ===
    scripts_dir = skill_dir / "scripts"
    main_py = scripts_dir / "main.py"

    check("scripts_exist", scripts_dir.exists() and any(scripts_dir.iterdir()) if scripts_dir.exists() else False)
    check("main_py_exists", main_py.exists())

    parseable = False
    has_argparse = False
    has_main = False
    if main_py.exists():
        code = main_py.read_text(encoding="utf-8")
        try:
            ast.parse(code)
            parseable = True
        except SyntaxError:
            pass
        has_argparse = "argparse" in code or "ArgumentParser" in code
        has_main = "__name__" in code or "def main" in code

    check("main_py_parseable", parseable)
    check("main_py_has_argparse", has_argparse)
    check("main_py_has_main", has_main)
    check("requirements_exist", (scripts_dir / "requirements.txt").exists() if scripts_dir.exists() else False)

    # === references/ (4 分) ===
    refs_dir = skill_dir / "references"
    refs_exist = refs_dir.exists() and any(refs_dir.iterdir()) if refs_dir.exists() else False
    check("refs_exist", refs_exist)
    check("workflow_exists", (refs_dir / "workflow.md").exists() if refs_dir.exists() else False)
    check("pitfalls_exists", (refs_dir / "pitfalls.md").exists() if refs_dir.exists() else False)
    check("refs_nonempty",
          any(f.stat().st_size > 50 for f in refs_dir.iterdir())
          if refs_exist else False)

    # === assets/ (2 分) ===
    assets_dir = skill_dir / "assets"
    check("assets_exist", assets_dir.exists())
    check("example_output_exists",
          (assets_dir / "example_output.md").exists() if assets_dir.exists() else False)

    return results


def score_summary(result: dict) -> str:
    """格式化评分摘要"""
    lines = [f"Score: {result['score']}/{result['max']}"]
    failed = [(n, r) for n, p, r in result["details"] if not p]
    if failed:
        lines.append(f"Failed ({len(failed)}): {', '.join(n for n, _ in failed)}")
    return " | ".join(lines)
