#!/usr/bin/env python3
"""
conversation-to-skill v2: Generate a multi-file skill package from a conversation log.

Produces a complete skill directory with:
  - SKILL.md (concise, < 5000 chars body)
  - scripts/main.py (full executable code)
  - scripts/requirements.txt (pinned dependencies)
  - references/workflow.md (detailed workflow)
  - references/pitfalls.md (all errors and fixes)
  - assets/example_output.md (example output format)

Requirements: pip install anthropic>=0.39.0
Environment:  ANTHROPIC_API_KEY must be set

Usage:
    python scripts/generate_skill.py <conversation_file> [--output <dir>] [--name <name>]
"""

import argparse
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


# ─────────────────────────── Conversation Parsing ────────────────────────────

def parse_chatgpt_export(data: list | dict) -> list[dict]:
    """Parse ChatGPT bulk export or OpenAI API format."""
    if isinstance(data, list) and data and "mapping" in data[0]:
        data = data[0]

    if isinstance(data, dict) and "mapping" in data:
        mapping = data["mapping"]
        visited = set()
        order = []

        def walk(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            node = mapping.get(node_id, {})
            msg = node.get("message")
            if msg:
                role = msg.get("author", {}).get("role", "unknown")
                parts = msg.get("content", {}).get("parts", [])
                content = "\n".join(str(p) for p in parts if isinstance(p, str)).strip()
                if content and role in ("user", "assistant"):
                    order.append({"role": role, "content": content})
            for child_id in node.get("children", []):
                walk(child_id)

        roots = [k for k, v in mapping.items()
                 if not mapping.get(v.get("parent", ""), {}).get("message")]
        for r in roots:
            walk(r)
        return order

    if isinstance(data, list):
        result = []
        for item in data:
            if isinstance(item, dict) and "role" in item:
                role = item["role"]
                content = item.get("content", "")
                if isinstance(content, list):
                    content = "\n".join(
                        p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("type") == "text"
                    )
                if role in ("user", "assistant") and str(content).strip():
                    result.append({"role": role, "content": str(content).strip()})
        return result

    return []


def parse_plain_text(text: str) -> list[dict]:
    """Parse plain text with User:/Assistant: markers."""
    messages = []
    current_role = None
    current_lines = []

    role_patterns = [
        (r"^(User|Human|You)\s*:", "user"),
        (r"^(Assistant|Claude|GPT|AI|Bot)\s*:", "assistant"),
        (r"^#{1,3}\s*(User|Human|You)\s*$", "user"),
        (r"^#{1,3}\s*(Assistant|Claude|GPT|AI|Bot)\s*$", "assistant"),
    ]

    for line in text.splitlines():
        matched_role = None
        matched_content_start = line

        for pattern, role in role_patterns:
            m = re.match(pattern, line, re.IGNORECASE)
            if m:
                matched_role = role
                matched_content_start = line[m.end():].strip()
                break

        if matched_role:
            if current_role and current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    messages.append({"role": current_role, "content": content})
            current_role = matched_role
            current_lines = [matched_content_start] if matched_content_start else []
        else:
            current_lines.append(line)

    if current_role and current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            messages.append({"role": current_role, "content": content})

    return messages


def load_conversation(filepath: str) -> list[dict]:
    """Auto-detect format and load conversation."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    text = path.read_text(encoding="utf-8", errors="replace")

    if path.suffix.lower() == ".json" or text.lstrip().startswith(("{", "[")):
        try:
            data = json.loads(text)
            messages = parse_chatgpt_export(data)
            if messages:
                return messages
        except json.JSONDecodeError:
            pass

    messages = parse_plain_text(text)
    if not messages:
        raise ValueError(
            "Could not parse any messages. Expected JSON or plain text with "
            "'User:' / 'Assistant:' markers."
        )
    return messages


# ─────────────────────────── Claude API Helpers ──────────────────────────────

def call_claude(client: anthropic.Anthropic, system: str, user: str,
                max_tokens: int = 4096) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text.strip()


def truncate_message(content: str, max_chars: int = 1500) -> str:
    if len(content) <= max_chars:
        return content
    half = max_chars // 2
    return (content[:half] +
            f"\n\n[... {len(content) - max_chars} chars truncated ...]\n\n" +
            content[-half:])


# ─────────────────────────── Analysis Pipeline ───────────────────────────────

def analyze_turns(client: anthropic.Anthropic, messages: list[dict]) -> str:
    """Step 1: Annotate each conversation turn."""
    print("  Step 1/6 - Analyzing conversation turns...")

    turns_text = ""
    for i, msg in enumerate(messages):
        role = msg["role"].upper()
        content = truncate_message(msg["content"], 1200)
        turns_text += f"\n---TURN {i+1} [{role}]---\n{content}\n"

    system = textwrap.dedent("""
        You are a technical analyst. Annotate each turn of a conversation.
        For each turn output:
        TURN <N> [<ROLE>]: <1-2 sentence annotation>
        Flag as: [PROBLEM], [ATTEMPT], [ERROR], [FIX], [SUCCESS], [REFINEMENT]
        Be technical and precise.
    """).strip()

    return call_claude(client, system,
                       f"Annotate every turn:\n{turns_text}", max_tokens=2000)


def extract_workflow(client: anthropic.Anthropic, messages: list[dict],
                     annotations: str) -> str:
    """Step 2: Extract the canonical workflow."""
    print("  Step 2/6 - Extracting workflow...")

    key_msgs = messages[:3] + messages[-3:] if len(messages) > 6 else messages
    sample = "\n\n".join(
        f"[{m['role'].upper()}]: {truncate_message(m['content'], 800)}"
        for m in key_msgs
    )

    system = textwrap.dedent("""
        You are a workflow architect. Extract the canonical workflow.
        Output:
        1. PROBLEM: (1-2 sentences)
        2. INPUTS: data/files involved
        3. OUTPUTS: what was produced
        4. STEPS: numbered list with [REVISED]/[FINAL] markers
        5. KEY TECHNIQUES: tools, libraries with version numbers
        6. GOTCHAS: every error and fix
        7. SKILL NAME SUGGESTION: kebab-case
        8. TRIGGER DESCRIPTION: when to use (2-3 sentences)
        9. COMPATIBILITY: Python version, key library versions needed
    """).strip()

    return call_claude(client, system,
                       f"Annotations:\n{annotations}\n\nSample:\n{sample}",
                       max_tokens=2500)


def extract_code(client: anthropic.Anthropic, messages: list[dict]) -> str:
    """Step 3: Extract final working code."""
    print("  Step 3/6 - Extracting working code...")

    code_msgs = [
        truncate_message(msg["content"], 2000)
        for msg in messages
        if msg["role"] == "assistant" and
        ("```" in msg["content"] or "def " in msg["content"])
    ]

    if not code_msgs:
        return "(No code snippets found)"

    combined = "\n\n---\n\n".join(code_msgs[-6:])

    system = textwrap.dedent("""
        You are a code reviewer. Extract FINAL WORKING code from these messages.
        Rules:
        - Keep only the last working version of each snippet
        - Add short inline comments
        - Group related code together
        - Preserve original code exactly
        - Output as a single complete Python script with all imports,
          an argparse CLI, and a __main__ block
        - Add a header comment listing required pip packages with versions
    """).strip()

    return call_claude(client, system,
                       f"Extract final working code:\n\n{combined}",
                       max_tokens=4000)


def generate_pitfalls(client: anthropic.Anthropic, annotations: str,
                      workflow: str) -> str:
    """Step 4: Generate detailed pitfalls document."""
    print("  Step 4/6 - Generating pitfalls documentation...")

    system = textwrap.dedent("""
        You are a technical writer documenting errors and solutions.
        From the conversation annotations and workflow, extract EVERY error
        that occurred and write a pitfalls document.

        For each pitfall:
        ## Pitfall N: <Short Title>
        **Error**: <exact error message or symptom>
        **Root Cause**: <why it happened>
        **Fix**: <how to fix it>
        ```python
        # Wrong approach
        <bad code>

        # Correct approach
        <good code>
        ```

        Be thorough. Include all pitfalls found in the conversation.
    """).strip()

    return call_claude(client, system,
                       f"Annotations:\n{annotations}\n\nWorkflow:\n{workflow}",
                       max_tokens=3000)


def generate_skill_md(client: anthropic.Anthropic, workflow: str,
                      skill_name: str, msg_count: int) -> str:
    """Step 5: Generate concise SKILL.md (body < 5000 chars)."""
    print("  Step 5/6 - Writing SKILL.md...")

    system = textwrap.dedent("""
        You are a skill author writing a CONCISE SKILL.md file.

        CRITICAL CONSTRAINTS:
        - The body (everything after the closing ---) MUST be under 5000 characters
        - Do NOT include full code — reference scripts/main.py instead
        - Do NOT list all pitfalls — reference references/pitfalls.md instead
        - Keep workflow steps brief with references to detailed docs

        EXACT TEMPLATE (follow precisely):
        ```
        ---
        name: <MUST match directory name, kebab-case>
        description: "<2-4 sentences on a SINGLE LINE. Must have: (a) clear task boundary (what it does), (b) trigger signal (when to use), containing a phrase like 'Use this skill when...'. Must be under 1024 characters. No XML tags. MUST be a double-quoted single-line string.>"
        license: MIT
        compatibility: "<Python version, key libraries with versions. Under 500 chars. MUST be a double-quoted single-line string.>"
        metadata:
          author: conversation-to-skill-generator
          version: "1.0"
        ---

        # <Title>

        <1 paragraph overview, max 3 sentences>

        ## When to Use This Skill
        - <5-7 trigger phrases>

        ## Inputs
        - <required/optional inputs>

        ## Workflow
        <Concise numbered steps. Reference scripts/main.py for code.>
        1. **Step**: Brief instruction.
        See `references/workflow.md` for detailed steps.

        ## Error Handling
        <List 2-4 common errors and how to handle/troubleshoot them.
        MUST contain both error-related words (error, exception, failure)
        AND handling words (handle, troubleshoot, fallback, retry).>

        ## Common Pitfalls
        <Top 3-5 most critical pitfalls only.>
        See `references/pitfalls.md` for the full list.

        ## Output Format
        <Brief description. See `assets/example_output.md` for examples.>
        ```

        CRITICAL YAML RULES:
        - NEVER use multi-line block scalars (>, >-, |, |-) for any value
        - description and compatibility MUST be single-line double-quoted strings
        - The body MUST include an "## Error Handling" section with error + handle keywords

        IMPORTANT: The entire body must be UNDER 5000 characters.
        Count carefully. Be concise.
    """).strip()

    user = f"""Write a SKILL.md for skill name: {skill_name}
Derived from: {msg_count} conversation turns

WORKFLOW:
{workflow}

Remember: body MUST be under 5000 chars. Reference scripts/ and references/.
"""
    return call_claude(client, system, user, max_tokens=3000)


def generate_example_output(client: anthropic.Anthropic, workflow: str) -> str:
    """Step 6: Generate example output document."""
    print("  Step 6/6 - Generating example output...")

    system = textwrap.dedent("""
        Write an example output document showing what this skill produces.
        Include:
        - Directory/file structure if applicable
        - Sample data formats (JSON, CSV, HDF5 schema, etc.)
        - Data shapes and types
        - A concrete small example

        Format as markdown.
    """).strip()

    return call_claude(client, system, f"Workflow:\n{workflow}", max_tokens=1500)


# ─────────────────────────── Output Assembly ─────────────────────────────────

def write_skill_package(out_path: Path, skill_name: str,
                        skill_md: str, code: str, workflow: str,
                        pitfalls: str, example_output: str,
                        annotations: str, raw_workflow: str):
    """Write the complete multi-file skill package."""
    # Create directory structure
    (out_path / "scripts").mkdir(parents=True, exist_ok=True)
    (out_path / "references").mkdir(parents=True, exist_ok=True)
    (out_path / "assets").mkdir(parents=True, exist_ok=True)

    # SKILL.md
    (out_path / "SKILL.md").write_text(skill_md, encoding="utf-8")

    # scripts/main.py
    (out_path / "scripts" / "main.py").write_text(code, encoding="utf-8")

    # scripts/requirements.txt — extract from code header
    reqs = extract_requirements(code)
    (out_path / "scripts" / "requirements.txt").write_text(
        reqs, encoding="utf-8")

    # references/workflow.md
    (out_path / "references" / "workflow.md").write_text(
        f"# Detailed Workflow\n\n{workflow}", encoding="utf-8")

    # references/pitfalls.md
    (out_path / "references" / "pitfalls.md").write_text(
        f"# Common Pitfalls and Solutions\n\n{pitfalls}", encoding="utf-8")

    # assets/example_output.md
    (out_path / "assets" / "example_output.md").write_text(
        f"# Example Output\n\n{example_output}", encoding="utf-8")

    # Analysis file for transparency
    (out_path / "references" / "analysis.md").write_text(
        f"# Conversation Analysis\n\n"
        f"## Turn Annotations\n\n{annotations}\n\n"
        f"## Extracted Workflow\n\n{raw_workflow}\n",
        encoding="utf-8")


def extract_requirements(code: str) -> str:
    """Extract pip requirements from code imports and header comments."""
    known_packages = {
        "numpy": "numpy>=1.24.0",
        "pandas": "pandas>=2.0.0",
        "scipy": "scipy>=1.11.0",
        "h5py": "h5py>=3.9.0",
        "matplotlib": "matplotlib>=3.7.0",
        "scanpy": "scanpy>=1.9.0",
        "anndata": "anndata>=0.9.0",
        "pysam": "pysam>=0.22.0",
        "xarray": "xarray>=2023.6.0",
        "tifffile": "tifffile>=2023.7.0",
        "dask": "dask>=2023.7.0",
        "zarr": "zarr>=2.16.0",
        "pyresample": "pyresample>=1.28.0",
        "satpy": "satpy>=0.45.0",
        "pynwb": "pynwb>=2.5.0",
        "anthropic": "anthropic>=0.39.0",
    }
    found = []
    for pkg, req in known_packages.items():
        if f"import {pkg}" in code or f"from {pkg}" in code:
            found.append(req)
    return "\n".join(sorted(found)) if found else "# No specific requirements detected\n"


# ─────────────────────────── Main Orchestration ──────────────────────────────

def run_pipeline(conversation_file: str, output_dir: Optional[str] = None,
                 skill_name_override: Optional[str] = None) -> Path:
    print(f"\nLoading conversation from: {conversation_file}")
    messages = load_conversation(conversation_file)
    print(f"  Found {len(messages)} messages "
          f"({sum(1 for m in messages if m['role']=='user')} user turns)")

    if len(messages) < 2:
        raise ValueError("Need at least 2 messages to extract a workflow.")

    client = anthropic.Anthropic()

    print("\nRunning 6-step analysis pipeline...\n")

    # Step 1-2: Analyze
    annotations = analyze_turns(client, messages)
    workflow_raw = extract_workflow(client, messages, annotations)

    # Parse skill name
    skill_name = skill_name_override
    if not skill_name:
        for line in workflow_raw.splitlines():
            if "SKILL NAME" in line.upper():
                parts = line.split(":", 1)
                if len(parts) == 2:
                    raw = parts[1].strip().lower()
                    skill_name = re.sub(r"[^a-z0-9-]", "-", raw).strip("-")
                    skill_name = re.sub(r"-+", "-", skill_name)
                    break
        if not skill_name:
            skill_name = "extracted-skill"

    # Step 3-6: Generate files
    code = extract_code(client, messages)
    pitfalls = generate_pitfalls(client, annotations, workflow_raw)
    skill_md = generate_skill_md(client, workflow_raw, skill_name, len(messages))
    example_output = generate_example_output(client, workflow_raw)

    # Assemble package
    out_path = Path(output_dir) if output_dir else Path.cwd() / skill_name
    write_skill_package(
        out_path, skill_name,
        skill_md, code, workflow_raw, pitfalls, example_output,
        annotations, workflow_raw
    )

    print(f"\nSkill package written to: {out_path}/")
    print(f"  - SKILL.md                    (core instructions)")
    print(f"  - scripts/main.py             (executable code)")
    print(f"  - scripts/requirements.txt    (dependencies)")
    print(f"  - references/workflow.md       (detailed workflow)")
    print(f"  - references/pitfalls.md       (errors & fixes)")
    print(f"  - assets/example_output.md     (output examples)")
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate a multi-file skill package from a conversation log"
    )
    parser.add_argument("conversation_file",
                        help="Path to conversation file (.json or .txt)")
    parser.add_argument("--output", "-o",
                        help="Output directory", default=None)
    parser.add_argument("--name", "-n",
                        help="Override skill name (kebab-case)", default=None)
    args = parser.parse_args()

    try:
        skill_path = run_pipeline(
            args.conversation_file, args.output, args.name)
        print(f"\nDone! Review {skill_path}/SKILL.md and refine as needed.")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except anthropic.AuthenticationError:
        print("Error: ANTHROPIC_API_KEY is not set or invalid.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
