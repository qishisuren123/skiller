# Skill Template Reference

This document provides the exact template that generated skills must follow.

## Directory Structure

Every generated skill MUST have this structure:

```
<skill-name>/                     # kebab-case, no underscores/spaces
├── SKILL.md                      # Core file (body < 5000 chars)
├── scripts/                      # Executable code
│   ├── main.py                   # Primary script with argparse CLI
│   └── requirements.txt          # Python dependencies with versions
├── references/                   # Detailed documentation
│   ├── workflow.md               # Full workflow details
│   └── pitfalls.md               # All errors and fixes
└── assets/                       # Supporting files
    └── example_output.md         # Example output format
```

## SKILL.md Frontmatter Fields

### Required Fields

| Field | Rules |
|-------|-------|
| `name` | Must match directory name exactly. kebab-case only. |
| `description` | 2-4 sentences on a SINGLE LINE in double quotes. < 1024 chars. Must state WHAT it does and WHEN to use it. No XML tags. Must contain a trigger phrase like "Use this skill when..." |
| `license` | Non-placeholder value. Use "MIT" if uncertain. |
| `compatibility` | SINGLE LINE in double quotes. < 500 chars. Python version, key library names + versions. |
| `metadata` | Must include `author` and `version` subfields. |

### YAML Parser Compatibility Notes

**CRITICAL**: Many YAML parsers (including the skill-metric evaluation tool) use simple line-based parsing and do NOT support multi-line block scalars. You MUST follow these rules:

- **NEVER** use `>`, `>-`, `|`, or `|-` for any frontmatter value
- **ALWAYS** write `description` as a single-line double-quoted string
- **ALWAYS** write `compatibility` as a single-line double-quoted string
- Keep all values on the same line as their key

**Correct example**:
```yaml
---
name: my-skill-name
description: "Processes X data from Y format, applies Z transformation, and outputs W. Handles edge cases like A and B. Use this skill when the user needs to convert Y format data into standardized W output."
license: MIT
compatibility: "Python >=3.9; numpy >=1.24.0; h5py >=3.9.0; scipy >=1.11.0."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---
```

**WRONG** (will cause scoring failures):
```yaml
description: >-
  Multi-line text that a simple
  parser reads as ">-"
compatibility: >
  Also broken for simple parsers
```

### Description Quality Checklist

Good: "Preprocesses spatial transcriptomics data (10x Visium, DLPFC format) into analysis-ready AnnData objects with QC filtering, normalization, HVG selection, and batch correction. Handles non-standard H5 formats and multi-slice integration. Use this skill when the user needs to prepare spatial transcriptomics data for downstream analysis tools like STAGATE or Scanpy."

Bad: "Helps with data processing."

## Body Constraints

- **Maximum 5000 characters** for the body (everything after the frontmatter)
- Keep workflow steps concise — reference `scripts/` for full code
- Keep pitfalls to top 3-5 — full list in `references/pitfalls.md`
- Reference files: "See `references/workflow.md` for details"
- Reference code: "Run `scripts/main.py --help` for full options"
- **MUST include an Error Handling section** with keywords "error" + "handle" (or "troubleshoot", "fallback", etc.)
- **MUST include code examples** (at least one code block with >= 3 lines)

## Cross-Reference Rules

1. If SKILL.md mentions `scripts/xxx.py`, that file MUST exist
2. If SKILL.md mentions `references/xxx.md`, that file MUST exist
3. If `scripts/` or `references/` directories exist, SKILL.md MUST reference
   at least one file from each

## Language Rules

- All generated content must be in English
- This includes SKILL.md, scripts/, references/, and assets/
- Code comments should be in English for international readability
