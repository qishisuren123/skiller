#!/usr/bin/env python3
"""
Generate complex, realistic English test conversations from scenario descriptions.

This script creates multi-turn conversations that simulate real debugging sessions,
including: error tracebacks, performance profiling, multi-file interactions, ambiguous
user requirements, and iterative problem-solving.

The generated conversations can then be fed into `generate_skill.py` to produce
skill packages, enabling end-to-end self-testing of the conversation-to-skill pipeline.

Requirements: pip install anthropic>=0.39.0
Environment:  ANTHROPIC_API_KEY must be set

Usage:
    # Generate from a scenario description
    python scripts/generate_test_conversations.py \
        --scenario "Preprocess spatial transcriptomics 10x Visium data for STAGATE analysis" \
        --domain "bioinformatics" \
        --output conversations/spatial-transcriptomics.json

    # Generate from a CSV file of scenarios
    python scripts/generate_test_conversations.py \
        --csv scenarios.csv \
        --output-dir conversations/

    # Generate multiple conversations for one scenario (stress test)
    python scripts/generate_test_conversations.py \
        --scenario "Build a neural spike visualization pipeline" \
        --num-conversations 3 \
        --output-dir conversations/
"""

import argparse
import csv
import json
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Optional

try:
    import anthropic
except ImportError:
    print("Error: anthropic SDK not found. Run: pip install anthropic>=0.39.0")
    sys.exit(1)


# ─────────────────────── Conversation Complexity Profiles ────────────────────

COMPLEXITY_PROFILES = {
    "standard": {
        "min_turns": 10,
        "max_turns": 14,
        "error_types": 3,
        "must_include": [
            "at least one full Python traceback",
            "at least one performance issue (memory or speed)",
            "at least one data format mismatch",
        ],
    },
    "advanced": {
        "min_turns": 14,
        "max_turns": 20,
        "error_types": 5,
        "must_include": [
            "at least two full Python tracebacks with different root causes",
            "a memory profiling session showing OOM and its resolution",
            "a multi-file code interaction (imports across modules)",
            "a subtle data bug that requires debugging (e.g., off-by-one, coordinate system)",
            "an ambiguous user requirement that gets clarified mid-conversation",
        ],
    },
    "expert": {
        "min_turns": 18,
        "max_turns": 25,
        "error_types": 7,
        "must_include": [
            "at least three full Python tracebacks with different root causes",
            "a performance profiling session (cProfile or memory_profiler output)",
            "a race condition or concurrency issue",
            "a version incompatibility between libraries",
            "a data corruption or silent failure scenario",
            "refactoring from prototype to production-quality code",
            "cross-platform or environment-specific issue",
        ],
    },
}


# ─────────────────────── Domain-Specific Error Libraries ─────────────────────

DOMAIN_ERRORS = {
    "neuroscience": [
        "h5py.File fails with OSError: Unable to open file (truncated HDF5)",
        "numpy MemoryError when loading full spike matrix (100k neurons x 1M timepoints)",
        "matplotlib colorbar position shifts after bbox_inches='tight'",
        "scipy.signal.butter filter produces NaN for edge frequencies",
        "KeyError: 'movement_onset' — HDF5 key naming convention changed between sessions",
        "IndexError in trial alignment when some trials have no spikes",
        "ValueError: operands could not be broadcast together — shape mismatch in z-score normalization",
    ],
    "bioinformatics": [
        "scanpy.read_h5ad fails: anndata version 0.8 vs 0.10 incompatibility",
        "MemoryError: cannot allocate 48GB for full expression matrix .toarray()",
        "ValueError: AnnData object has n_obs x n_vars = 0 x 0 after filtering",
        "KeyError: 'spatial' not in adata.obsm — 10x Visium vs SlideSeq format difference",
        "pysam.VariantFile raises ValueError on malformed VCF header",
        "pandas merge produces unexpected duplicates due to multi-mapping genes",
        "RuntimeWarning: divide by zero encountered in log2 — zero-count genes in normalization",
    ],
    "earth_science": [
        "pyresample AreaDefinition ValueError: incorrect number of proj parameters",
        "netCDF4.Dataset raises OSError: [Errno -101] NetCDF: HDF error",
        "xarray.open_mfdataset MemoryError on 500+ MODIS granules",
        "cartopy.crs.PlateCarree() vs epsg:4326 coordinate mismatch",
        "numpy RuntimeWarning: overflow in multiply — satellite radiance scaling factor",
        "TimeoutError: SatPy reader hangs on corrupted L1B file",
        "ValueError: conflicting sizes for dimension 'time' — misaligned temporal grids",
    ],
    "materials_science": [
        "json.decoder.JSONDecodeError: Expecting property name on incomplete CIF export",
        "UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff — binary-mixed corpus",
        "regex catastrophic backtracking on nested chemical formulae",
        "pandas DataFrame.apply bottleneck: 40 min for 2M rows tokenization",
        "sklearn TfidfVectorizer MemoryError on 10M-document corpus",
        "SMILES parsing ValueError: kekulization error for aromatic ring",
        "spaCy model fails to segment measurement units (e.g., 'GPa' split as 'G' 'Pa')",
    ],
    "general": [
        "FileNotFoundError: path does not exist (wrong working directory)",
        "TypeError: expected str, bytes or os.PathLike object, not NoneType",
        "PermissionError: [Errno 13] Permission denied on NFS mount",
        "ConnectionError: HTTPSConnectionPool max retries exceeded",
        "RecursionError: maximum recursion depth exceeded in nested data parsing",
        "pickle.UnpicklingError: invalid load key on corrupted checkpoint",
        "subprocess.TimeoutExpired: command timed out after 300 seconds",
    ],
}


# ─────────────────────── Conversation Generation ─────────────────────────────

def generate_conversation(
    client: anthropic.Anthropic,
    scenario: str,
    domain: str = "general",
    complexity: str = "advanced",
    conversation_id: int = 1,
) -> list[dict]:
    """Generate a single complex English test conversation."""

    profile = COMPLEXITY_PROFILES.get(complexity, COMPLEXITY_PROFILES["advanced"])
    domain_errors = DOMAIN_ERRORS.get(domain, DOMAIN_ERRORS["general"])

    # Select specific error types to include
    error_samples = domain_errors[:profile["error_types"]]

    system_prompt = textwrap.dedent(f"""\
        You are generating a REALISTIC, COMPLEX multi-turn conversation between
        a User and an AI Assistant (Claude) about a scientific data processing task.

        CRITICAL REQUIREMENTS:
        1. The ENTIRE conversation MUST be in English. No Chinese, no other languages.
        2. The conversation must have {profile['min_turns']}-{profile['max_turns']} turns
           (a turn = one user message + one assistant response).
        3. The User should behave like a real scientist — sometimes vague, sometimes
           providing incomplete information, occasionally misunderstanding the solution.
        4. The Assistant should provide working Python code with realistic complexity.

        MANDATORY ELEMENTS (the conversation MUST include ALL of these):
        {chr(10).join(f'- {item}' for item in profile['must_include'])}

        DOMAIN-SPECIFIC ERRORS TO INCORPORATE (use at least {len(error_samples)} of these):
        {chr(10).join(f'- {err}' for err in error_samples)}

        CONVERSATION FLOW PATTERN:
        1. User describes problem (somewhat vague, missing key details)
        2. Assistant asks clarifying questions or makes assumptions
        3. User provides data description / shares file structure
        4. Assistant provides initial solution code
        5. User reports error (with FULL traceback, not just error message)
        6. Assistant diagnoses and fixes
        7. Code works but has performance issue (slow or OOM)
        8. Assistant optimizes (with profiling data)
        9. User has additional requirements or edge cases
        10. Final working solution with validation

        CODE QUALITY RULES:
        - All code must be syntactically valid Python
        - Include realistic library imports with version-specific APIs
        - Include realistic file paths (e.g., /data/experiment_2024/, not /path/to/data)
        - Include realistic data dimensions (e.g., 50000 cells x 30000 genes, not 10x10)
        - Tracebacks must look real: include file paths, line numbers, full stack

        OUTPUT FORMAT:
        Return a JSON array of message objects, each with "role" and "content" fields.
        Example: [{{"role": "user", "content": "..."}}, {{"role": "assistant", "content": "..."}}]

        The output must be valid JSON. Use \\n for newlines in content strings.
        Escape all special characters properly for JSON.
    """)

    user_prompt = textwrap.dedent(f"""\
        Generate conversation #{conversation_id} for this scenario:

        SCENARIO: {scenario}
        DOMAIN: {domain}
        COMPLEXITY: {complexity}

        Remember:
        - ALL English, no exceptions
        - Include realistic Python tracebacks with full stack traces
        - Include realistic data sizes and file structures
        - The user should sometimes be wrong or confused
        - The conversation should feel like a REAL debugging session, not a tutorial
        - Include at least one moment where the assistant's first attempt fails

        Return ONLY the JSON array. No markdown code fences, no explanation.
    """)

    print(f"  Generating conversation (scenario: {scenario[:50]}..., "
          f"complexity: {complexity})...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()

    # Strip possible markdown code fences
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)

    try:
        messages = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  WARNING: JSON parse failed ({e}), attempting repair...")
        # Attempt to fix common JSON issues
        raw = raw.replace("\n", "\\n").replace("\t", "\\t")
        try:
            messages = json.loads(raw)
        except json.JSONDecodeError:
            print(f"  ERROR: Could not parse conversation JSON. Saving raw output.")
            return [{"role": "system", "content": f"PARSE_ERROR: {raw[:500]}"}]

    if not isinstance(messages, list):
        messages = [messages]

    # Validate format
    valid = []
    for msg in messages:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            if msg["role"] in ("user", "assistant"):
                valid.append({"role": msg["role"], "content": str(msg["content"])})

    print(f"  Generated {len(valid)} valid turns")
    return valid


def enhance_conversation(
    client: anthropic.Anthropic,
    messages: list[dict],
    scenario: str,
) -> list[dict]:
    """Add additional complexity layers to an existing conversation."""

    print("  Enhancing conversation with additional complexity...")

    system = textwrap.dedent("""\
        You are adding MORE complexity to an existing technical conversation.
        Add 4-6 additional turns that include:
        1. A subtle bug that was missed earlier (e.g., timezone handling, encoding issue)
        2. A production-readiness concern (error handling, logging, config management)
        3. The user discovering an edge case that breaks the solution

        Keep all content in English. Return the COMPLETE conversation (original + new turns)
        as a JSON array. No code fences.
    """)

    existing = json.dumps(messages, indent=2, ensure_ascii=False)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=12000,
        system=system,
        messages=[{"role": "user", "content": f"Scenario: {scenario}\n\nExisting conversation:\n{existing}"}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
        raw = re.sub(r"\n?```\s*$", "", raw)

    try:
        enhanced = json.loads(raw)
        if isinstance(enhanced, list) and len(enhanced) > len(messages):
            print(f"  Enhanced: {len(messages)} → {len(enhanced)} turns")
            return enhanced
    except json.JSONDecodeError:
        pass

    print("  Enhancement failed, keeping original")
    return messages


def validate_conversation(messages: list[dict]) -> dict:
    """Validate conversation quality and return a report."""
    report = {
        "total_turns": len(messages),
        "user_turns": sum(1 for m in messages if m["role"] == "user"),
        "assistant_turns": sum(1 for m in messages if m["role"] == "assistant"),
        "has_traceback": any("Traceback" in m["content"] for m in messages),
        "has_code_blocks": any("```" in m["content"] for m in messages),
        "has_error_keyword": any(
            any(kw in m["content"] for kw in ["Error", "Exception", "error", "failed", "OOM"])
            for m in messages
        ),
        "avg_content_length": sum(len(m["content"]) for m in messages) / max(len(messages), 1),
        "total_chars": sum(len(m["content"]) for m in messages),
        "english_ratio": 0.0,
        "issues": [],
    }

    # Check English ratio
    all_text = " ".join(m["content"] for m in messages)
    ascii_chars = sum(1 for c in all_text if ord(c) < 128)
    report["english_ratio"] = ascii_chars / max(len(all_text), 1)

    # Quality checks
    if report["total_turns"] < 10:
        report["issues"].append("Too few turns (< 10)")
    if not report["has_traceback"]:
        report["issues"].append("No Python traceback found")
    if not report["has_code_blocks"]:
        report["issues"].append("No code blocks found")
    if report["english_ratio"] < 0.95:
        report["issues"].append(f"Low English ratio: {report['english_ratio']:.1%}")
    if report["avg_content_length"] < 200:
        report["issues"].append("Average message too short (< 200 chars)")

    report["quality"] = "PASS" if not report["issues"] else "NEEDS_REVIEW"
    return report


# ─────────────────────── Batch Generation from CSV ───────────────────────────

def load_scenarios_from_csv(csv_path: str) -> list[dict]:
    """Load scenarios from a CSV file.

    Expected columns: scenario (required), domain (optional), complexity (optional)
    """
    scenarios = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Support multiple column name variants
            scenario = (
                row.get("scenario") or row.get("description") or
                row.get("question") or row.get("prompt") or ""
            ).strip()
            if not scenario:
                continue

            domain = (row.get("domain") or row.get("field") or "general").strip().lower()
            complexity = (row.get("complexity") or "advanced").strip().lower()
            name = row.get("name") or row.get("id") or ""

            # Map domain names to standardized identifiers
            domain_map = {
                "neuroscience": "neuroscience",
                "neuro": "neuroscience",
                "bioinformatics": "bioinformatics",
                "bio": "bioinformatics",
                "life_science": "bioinformatics",
                "life science": "bioinformatics",
                "earth_science": "earth_science",
                "earth science": "earth_science",
                "geo": "earth_science",
                "materials_science": "materials_science",
                "materials science": "materials_science",
                "material": "materials_science",
            }
            domain = domain_map.get(domain, domain)

            scenarios.append({
                "scenario": scenario,
                "domain": domain,
                "complexity": complexity,
                "name": name,
            })

    return scenarios


# ─────────────────────── Main ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate complex English test conversations for skill extraction"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--scenario", "-s",
                       help="Single scenario description")
    group.add_argument("--csv", "-c",
                       help="CSV file with multiple scenarios")

    parser.add_argument("--domain", "-d", default="general",
                        choices=list(DOMAIN_ERRORS.keys()),
                        help="Domain for error library (default: general)")
    parser.add_argument("--complexity", default="advanced",
                        choices=list(COMPLEXITY_PROFILES.keys()),
                        help="Conversation complexity level (default: advanced)")
    parser.add_argument("--output", "-o",
                        help="Output file path (for single scenario)")
    parser.add_argument("--output-dir",
                        help="Output directory (for CSV mode or multi-conversation)")
    parser.add_argument("--num-conversations", "-n", type=int, default=1,
                        help="Number of conversations per scenario (default: 1)")
    parser.add_argument("--enhance", action="store_true",
                        help="Add enhancement pass for extra complexity")
    parser.add_argument("--name",
                        help="Name prefix for output files")

    args = parser.parse_args()

    client = anthropic.Anthropic()

    if args.csv:
        # Batch mode
        scenarios = load_scenarios_from_csv(args.csv)
        output_dir = Path(args.output_dir or "conversations")
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Loaded {len(scenarios)} scenarios from {args.csv}")

        all_reports = []
        for i, sc in enumerate(scenarios, 1):
            print(f"\n{'='*60}")
            print(f"Scenario {i}/{len(scenarios)}: {sc['scenario'][:60]}...")
            print(f"  Domain: {sc['domain']}, Complexity: {sc['complexity']}")

            for conv_num in range(1, args.num_conversations + 1):
                messages = generate_conversation(
                    client, sc["scenario"], sc["domain"],
                    sc["complexity"], conv_num
                )

                if args.enhance and len(messages) > 4:
                    messages = enhance_conversation(client, messages, sc["scenario"])

                report = validate_conversation(messages)
                report["scenario"] = sc["scenario"][:50]
                all_reports.append(report)

                # Generate output filename
                name = sc.get("name") or re.sub(
                    r"[^a-z0-9]+", "_",
                    sc["scenario"][:40].lower()
                ).strip("_")
                suffix = f"_v{conv_num}" if args.num_conversations > 1 else ""
                out_file = output_dir / f"{name}{suffix}.json"

                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(messages, f, indent=2, ensure_ascii=False)
                print(f"  Saved: {out_file} ({report['total_turns']} turns, "
                      f"{report['quality']})")

        # Print summary
        print(f"\n{'='*60}")
        print("GENERATION SUMMARY")
        print(f"{'='*60}")
        for r in all_reports:
            status = "✓" if r["quality"] == "PASS" else "✗"
            print(f"  {status} {r['scenario']}: {r['total_turns']} turns, "
                  f"English {r['english_ratio']:.0%}, "
                  f"traceback={'Y' if r['has_traceback'] else 'N'}")
            if r["issues"]:
                for issue in r["issues"]:
                    print(f"    → {issue}")

    else:
        # Single scenario mode
        for conv_num in range(1, args.num_conversations + 1):
            messages = generate_conversation(
                client, args.scenario, args.domain,
                args.complexity, conv_num
            )

            if args.enhance and len(messages) > 4:
                messages = enhance_conversation(client, messages, args.scenario)

            report = validate_conversation(messages)

            # Determine output path
            if args.output:
                out_path = Path(args.output)
            elif args.output_dir:
                name = args.name or re.sub(
                    r"[^a-z0-9]+", "_",
                    args.scenario[:40].lower()
                ).strip("_")
                suffix = f"_v{conv_num}" if args.num_conversations > 1 else ""
                out_dir = Path(args.output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                out_path = out_dir / f"{name}{suffix}.json"
            else:
                out_path = Path(f"conversation_{conv_num}.json")

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)

            print(f"\nSaved: {out_path}")
            print(f"  Turns: {report['total_turns']}")
            print(f"  English ratio: {report['english_ratio']:.1%}")
            print(f"  Has traceback: {report['has_traceback']}")
            print(f"  Quality: {report['quality']}")
            if report["issues"]:
                for issue in report["issues"]:
                    print(f"  Issue: {issue}")


if __name__ == "__main__":
    main()
