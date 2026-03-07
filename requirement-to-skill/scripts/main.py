#!/usr/bin/env python3
"""
requirement-to-skill: Orchestrate the full pipeline from requirement to validated skill.

This script provides utilities for each phase of the pipeline:
  1. Requirement analysis template generation
  2. Conversation skeleton construction
  3. Skill package scaffolding
  4. Skill-metric validation
  5. Code usability testing

Usage:
    python main.py scaffold --name my-skill --requirement "Description of what the tool does"
    python main.py validate /path/to/skill-dir
    python main.py test /path/to/skill-dir
"""

import argparse
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path


# ─────────────────────── Phase 1: Requirement Analysis ───────────────────────

def generate_analysis_template(requirement: str, skill_name: str) -> dict:
    """Generate a structured analysis template from a plain-language requirement.

    Parameters
    ----------
    requirement : str
        Plain-language description of what the skill should do.
    skill_name : str
        kebab-case name for the skill.

    Returns
    -------
    dict with keys: core_task, inputs, outputs, libraries, edge_cases, planned_errors
    """
    template = {
        "skill_name": skill_name,
        "requirement": requirement,
        "core_task": "[TODO: 1-2 sentence summary of what the tool does]",
        "inputs": ["[TODO: list input files/formats]"],
        "outputs": ["[TODO: list output files/formats]"],
        "libraries": ["[TODO: list Python libraries with versions]"],
        "edge_cases": [
            "[TODO: format incompatibility]",
            "[TODO: scale/performance issue]",
            "[TODO: data edge case]",
        ],
        "planned_errors": [
            {
                "turn": 3,
                "category": "format",
                "error": "[TODO: exact error message]",
                "root_cause": "[TODO: why it happens]",
                "fix": "[TODO: how to fix]",
            },
            {
                "turn": 5,
                "category": "api_misuse",
                "error": "[TODO: exact error message]",
                "root_cause": "[TODO]",
                "fix": "[TODO]",
            },
            {
                "turn": 7,
                "category": "edge_case",
                "error": "[TODO]",
                "root_cause": "[TODO]",
                "fix": "[TODO]",
            },
            {
                "turn": 9,
                "category": "scale",
                "error": "[TODO]",
                "root_cause": "[TODO]",
                "fix": "[TODO]",
            },
            {
                "turn": 11,
                "category": "integration",
                "error": "[TODO]",
                "root_cause": "[TODO]",
                "fix": "[TODO]",
            },
        ],
    }
    return template


# ─────────────────────── Phase 2: Conversation Skeleton ──────────────────────

def generate_conversation_skeleton(analysis: dict) -> list:
    """Generate a conversation skeleton from the analysis template.

    Parameters
    ----------
    analysis : dict
        Output of generate_analysis_template with TODOs filled in.

    Returns
    -------
    list of {"role": str, "content": str} messages (skeleton with placeholders).
    """
    name = analysis["skill_name"]
    skeleton = [
        {
            "role": "user",
            "content": f"[PROBLEM] {analysis['requirement']}",
        },
        {
            "role": "assistant",
            "content": (
                f"[ATTEMPT] Here is an initial approach for {name}:\n"
                "```python\n# [TODO: initial imperfect code]\n```"
            ),
        },
    ]

    for i, err in enumerate(analysis.get("planned_errors", [])):
        turn_num = err.get("turn", 3 + i * 2)
        skeleton.append(
            {
                "role": "user",
                "content": (
                    f"[ERROR] I ran the code and got:\n```\n{err['error']}\n```\n"
                    f"[Category: {err['category']}]"
                ),
            }
        )
        skeleton.append(
            {
                "role": "assistant",
                "content": (
                    f"[FIX] Root cause: {err['root_cause']}\n\n"
                    f"Fix: {err['fix']}\n\n"
                    "```python\n# [TODO: corrected code]\n```"
                ),
            }
        )

    skeleton.append(
        {
            "role": "user",
            "content": (
                "[REFINEMENT] Can you integrate everything into a complete "
                "script with argparse CLI, logging, and error handling?"
            ),
        }
    )
    skeleton.append(
        {
            "role": "assistant",
            "content": (
                "[SUCCESS] Here is the complete production script:\n"
                "```python\n# [TODO: final integrated code]\n```"
            ),
        }
    )

    return skeleton


# ─────────────────────── Phase 3: Skill Scaffolding ──────────────────────────

SKILL_MD_TEMPLATE = textwrap.dedent('''\
    ---
    name: {name}
    description: "{description}"
    license: MIT
    compatibility: "{compatibility}"
    metadata:
      author: conversation-to-skill-generator
      version: "1.0"
    ---

    # {title}

    [TODO: 1 paragraph overview]

    ## When to Use This Skill

    - [TODO: 5-7 trigger phrases]

    ## Inputs

    - [TODO: input descriptions]

    ## Workflow

    1. [TODO: Step 1]. See `references/workflow.md` for details.
    2. [TODO: Step 2]. Run `scripts/main.py --help` for options.

    ## Error Handling

    1. **[TODO: Error 1]**: Description of error. Handle by [solution].
    2. **[TODO: Error 2]**: Description. Troubleshoot by [approach].

    ## Common Pitfalls

    1. [TODO: Pitfall 1]
    2. [TODO: Pitfall 2]

    See `references/pitfalls.md` for the full list.

    ## Output Format

    [TODO: Brief output description]

    See `assets/example_output.md` for examples.
''')


def scaffold_skill(name: str, output_dir: str, requirement: str = "") -> Path:
    """Create the directory structure and template files for a new skill.

    Parameters
    ----------
    name : str
        kebab-case skill name.
    output_dir : str
        Parent directory for the skill folder.
    requirement : str
        Optional requirement text to pre-fill templates.

    Returns
    -------
    Path to the created skill directory.
    """
    skill_dir = Path(output_dir) / name
    for subdir in ["scripts", "references", "assets"]:
        (skill_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Validate name format
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name):
        print(f"WARNING: '{name}' is not valid kebab-case. Use lowercase + hyphens only.")

    # SKILL.md
    title = name.replace("-", " ").title()
    desc_placeholder = requirement if requirement else "[TODO: 2-4 sentences. End with: Use this skill when...]"
    skill_md = SKILL_MD_TEMPLATE.format(
        name=name,
        description=desc_placeholder[:1000],
        compatibility="Python >=3.9; [TODO: add libraries]",
        title=title,
    )
    (skill_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # scripts/main.py
    main_py = textwrap.dedent(f'''\
        #!/usr/bin/env python3
        """
        {title} — main script.

        Usage:
            python main.py --help
        """

        import argparse
        import logging
        import sys

        logger = logging.getLogger("{name}")


        def main():
            parser = argparse.ArgumentParser(description="{title}")
            # [TODO: add arguments]
            parser.add_argument("input", help="Input path")
            parser.add_argument("-o", "--output", default="output.json", help="Output path")
            args = parser.parse_args()

            logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
            logger.info("Starting %s", "{name}")

            # [TODO: implement pipeline]
            print(f"Processing {{args.input}} -> {{args.output}}")


        if __name__ == "__main__":
            main()
    ''')
    (skill_dir / "scripts" / "main.py").write_text(main_py, encoding="utf-8")

    # scripts/requirements.txt
    (skill_dir / "scripts" / "requirements.txt").write_text(
        "# [TODO: add dependencies with version pins]\n", encoding="utf-8"
    )

    # references/workflow.md
    (skill_dir / "references" / "workflow.md").write_text(
        "# Detailed Workflow\n\n[TODO: Write detailed workflow steps]\n", encoding="utf-8"
    )

    # references/pitfalls.md
    (skill_dir / "references" / "pitfalls.md").write_text(
        "# Common Pitfalls and Solutions\n\n[TODO: Document errors from conversation]\n",
        encoding="utf-8",
    )

    # assets/example_output.md
    (skill_dir / "assets" / "example_output.md").write_text(
        "# Example Output\n\n[TODO: Show concrete output example]\n", encoding="utf-8"
    )

    print(f"Skill scaffolded at: {skill_dir}/")
    print(f"  SKILL.md, scripts/main.py, references/, assets/ created")
    print(f"  Fill in [TODO] placeholders to complete the skill.")
    return skill_dir


# ─────────────────────── Phase 4: Validation ─────────────────────────────────

def validate_skill(skill_dir: str, metric_script: str = None) -> dict:
    """Run skill-metric validation on a skill directory.

    Parameters
    ----------
    skill_dir : str
        Path to the skill directory.
    metric_script : str, optional
        Path to skill_quality_eval.py. If None, searches common locations.

    Returns
    -------
    dict with scoring results, or error info.
    """
    skill_path = Path(skill_dir).resolve()
    if not (skill_path / "SKILL.md").exists():
        return {"error": f"SKILL.md not found in {skill_path}"}

    # Find the metric script
    if metric_script is None:
        candidates = [
            Path("skill-metric/skill-metric/scripts/skill_quality_eval.py"),
            Path("skill-metric/scripts/skill_quality_eval.py"),
            Path("../skill-metric/scripts/skill_quality_eval.py"),
        ]
        for c in candidates:
            if c.exists():
                metric_script = str(c)
                break

    if metric_script is None or not Path(metric_script).exists():
        return {"error": "skill_quality_eval.py not found. Provide path with --metric-script."}

    result = subprocess.run(
        [sys.executable, metric_script, str(skill_path), "-j"],
        capture_output=True, text=True, timeout=30,
    )

    if result.returncode != 0:
        return {"error": f"Metric script failed: {result.stderr}"}

    try:
        scores = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"Could not parse JSON output: {result.stdout[:500]}"}

    total = scores.get("total_score", 0)
    print(f"\nScore: {total}/24")
    print(f"  Format:       {scores.get('format_score', '?')}/8")
    print(f"  Completeness: {scores.get('completeness_score', '?')}/8")
    print(f"  Writing:      {scores.get('writing_score', '?')}/8")

    if total < 24:
        print("\nFailed checks:")
        for section in ("format", "completeness", "writing"):
            for item in scores.get("details", {}).get(section, []):
                if not item.get("pass"):
                    print(f"  [FAIL] {item['item']}: {item['message']}")

    return scores


# ─────────────────────── Phase 5: Code Testing ───────────────────────────────

def test_skill_code(skill_dir: str) -> bool:
    """Run basic code usability tests on scripts/main.py.

    Parameters
    ----------
    skill_dir : str
        Path to the skill directory.

    Returns
    -------
    bool : True if all tests pass.
    """
    main_py = Path(skill_dir) / "scripts" / "main.py"
    if not main_py.exists():
        print(f"SKIP: {main_py} not found")
        return False

    # Test 1: --help
    print("Test 1: --help")
    result = subprocess.run(
        [sys.executable, str(main_py), "--help"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode == 0:
        print(f"  PASS: --help succeeded ({len(result.stdout)} chars output)")
    else:
        print(f"  FAIL: --help returned code {result.returncode}")
        print(f"  stderr: {result.stderr[:500]}")
        return False

    # Test 2: Import check
    print("Test 2: import check")
    result = subprocess.run(
        [sys.executable, "-c", f"import importlib.util; spec = importlib.util.spec_from_file_location('m', '{main_py}'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); print('OK')"],
        capture_output=True, text=True, timeout=30,
    )
    if "OK" in result.stdout:
        print("  PASS: all imports succeed")
    else:
        print(f"  FAIL: import error")
        print(f"  stderr: {result.stderr[:500]}")
        return False

    print("\nAll code tests PASSED")
    return True


# ─────────────────────── CLI Entry Point ─────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Requirement to Skill pipeline utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python main.py scaffold --name my-tool --requirement "Process X data..."
              python main.py validate /path/to/my-tool/
              python main.py test /path/to/my-tool/
              python main.py analyze --name my-tool --requirement "Process X data..."
        """),
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline phase to run")

    # scaffold
    sp_scaffold = subparsers.add_parser("scaffold", help="Create skill directory skeleton")
    sp_scaffold.add_argument("--name", required=True, help="Skill name (kebab-case)")
    sp_scaffold.add_argument("--requirement", default="", help="Requirement description")
    sp_scaffold.add_argument("--output-dir", default=".", help="Parent directory")

    # analyze
    sp_analyze = subparsers.add_parser("analyze", help="Generate requirement analysis template")
    sp_analyze.add_argument("--name", required=True, help="Skill name")
    sp_analyze.add_argument("--requirement", required=True, help="Requirement text")
    sp_analyze.add_argument("--output", default=None, help="Output JSON path")

    # validate
    sp_validate = subparsers.add_parser("validate", help="Run skill-metric on a skill directory")
    sp_validate.add_argument("skill_dir", help="Path to skill directory")
    sp_validate.add_argument("--metric-script", default=None, help="Path to skill_quality_eval.py")

    # test
    sp_test = subparsers.add_parser("test", help="Run code usability tests")
    sp_test.add_argument("skill_dir", help="Path to skill directory")

    args = parser.parse_args()

    if args.command == "scaffold":
        scaffold_skill(args.name, args.output_dir, args.requirement)
    elif args.command == "analyze":
        template = generate_analysis_template(args.requirement, args.name)
        output = json.dumps(template, indent=2, ensure_ascii=False)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Analysis template written to: {args.output}")
        else:
            print(output)
    elif args.command == "validate":
        validate_skill(args.skill_dir, args.metric_script)
    elif args.command == "test":
        test_skill_code(args.skill_dir)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
