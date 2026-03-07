# Skiller — Automated Skill Package Generators for Claude Code

Generate production-quality [Claude Code skill packages](https://docs.anthropic.com/en/docs/claude-code/skills) automatically from conversations or plain-text requirements.

## What Are Skills?

Skills are reusable instruction packages for Claude Code. A well-structured skill teaches Claude domain-specific workflows, error-handling patterns, and tool usage — turning a generic assistant into a domain expert. Each skill is a directory containing:

```
my-skill/
├── SKILL.md              # Core instructions + YAML frontmatter
├── scripts/              # Executable tools (CLI scripts)
├── references/           # Detailed docs (workflow, pitfalls)
└── assets/               # Examples and templates
```

## Two Generators

This repo provides two complementary skill generators:

### 1. `conversation-to-skill` — From Chat Logs

Extracts a skill from an existing AI conversation (ChatGPT export, Claude JSON, OpenAI API format, or plain text).

**Best for**: When you already have a conversation where a problem was solved through trial-and-error.

```bash
# Automated (requires ANTHROPIC_API_KEY)
python conversation-to-skill/scripts/generate_skill.py conversation.json -o output/

# Or follow the manual workflow
# See conversation-to-skill/references/manual-workflow.md
```

**How it works**:
1. Parse conversation → tag turns as [PROBLEM], [ERROR], [FIX], [SUCCESS]
2. Extract the final working code, workflow, and all pitfalls
3. Package into a multi-file skill directory
4. Validate against quality checklist

### 2. `requirement-to-skill` — From Text Requirements

Generates a skill from a plain-language requirement description — no conversation needed.

**Best for**: When you know what skill you need but don't have a conversation about it.

**How it works**:
1. **Analyze** the requirement (core task, I/O, challenges, domain pitfalls)
2. **Construct** a realistic 10-20 turn conversation with 5+ error→fix iterations
3. **Extract** the skill using conversation-to-skill
4. **Validate** against the 24-point skill-metric rubric
5. **Test** code usability (`--help` + synthetic data end-to-end)

The key insight: real conversations produce high-quality skills because they contain realistic error→fix iterations. This generator constructs such conversations synthetically, then extracts the skill from them.

## Quality Assurance

Both generators target **24/24** on the [skill-metric rubric](https://github.com/anthropics/claude-code/blob/main/skill-metric), which evaluates:

| Dimension | Points | What It Checks |
|-----------|--------|----------------|
| Format | 8 | SKILL.md structure, YAML frontmatter, naming conventions |
| Completeness | 8 | license, compatibility, metadata, scripts/references/assets dirs |
| Writing | 8 | Task boundaries, trigger signals, cross-references, English content |

## Comparison with Anthropic's Official Skill Creator

We ran a controlled experiment comparing three systems on the same task (neuroscience metadata generation):

| System | skill-metric | Practical Test (7 assertions × 3 evals) | Automation |
|--------|-------------|----------------------------------------|------------|
| **conversation-to-skill** | 24/24 | 21/21 (100%) | Fully automated |
| **requirement-to-skill** | 24/24 | 21/21 (100%) | Minimal input |
| Anthropic skill-creator | 19/24 | 21/21 (100%) | Interactive |
| No-skill baseline | N/A | 9/21 (43%) | N/A |

**Key finding**: All three systems are functionally equivalent (100% practical test pass rate), but our generators require significantly less human interaction and consistently hit 24/24 on structural quality. The 5-point difference from the official tool reflects design philosophy (our templates embed the scoring rubric), not quality.

**Skills improve task completion by +57 percentage points** (43% → 100%) compared to no-skill baseline.

## Repository Structure

```
skiller/
├── conversation-to-skill/          # Generator 1: Chat log → Skill
│   ├── SKILL.md                    # Skill instructions
│   ├── scripts/
│   │   ├── generate_skill.py       # Main generator (6-step API pipeline)
│   │   └── generate_test_conversations.py  # Test conversation synthesizer
│   ├── references/
│   │   ├── manual-workflow.md      # Step-by-step manual process
│   │   ├── quality-checklist.md    # 24-point validation checklist
│   │   └── skill-template.md       # SKILL.md template with YAML notes
│   └── assets/
│       └── example_output.md       # Example of generated skill
│
├── requirement-to-skill/           # Generator 2: Requirements → Skill
│   ├── SKILL.md                    # Skill instructions
│   ├── scripts/
│   │   ├── main.py                 # 4 subcommands: scaffold/analyze/validate/test
│   │   └── requirements.txt
│   ├── references/
│   │   ├── workflow.md             # 5-phase pipeline details
│   │   ├── conversation_design.md  # How to construct realistic conversations
│   │   └── pitfalls.md             # Common failure modes
│   └── assets/
│       └── example_output.md       # Example of full pipeline output
│
├── LICENSE                         # MIT
└── README.md
```

## Installation

### As Claude Code Skills

Copy the skill directories to your Claude Code custom instructions path:

```bash
# Clone
git clone https://github.com/qishisuren123/skiller.git

# Copy to your project's .claude/ directory
cp -r skiller/conversation-to-skill /path/to/your/project/.claude/skills/
cp -r skiller/requirement-to-skill /path/to/your/project/.claude/skills/
```

### For Automated Generation

```bash
pip install anthropic  # Required for generate_skill.py
export ANTHROPIC_API_KEY=your-key-here

python conversation-to-skill/scripts/generate_skill.py your_conversation.json -o output/
```

## Requirements

- Python >= 3.9
- `anthropic >= 0.39.0` (for automated generation only)
- No external dependencies for manual workflow

## YAML Compatibility Note

A critical lesson from development: **never use YAML block scalars** (`>`, `>-`, `|`, `|-`) in SKILL.md frontmatter. Different YAML parsers handle them inconsistently. Always use single-line double-quoted strings:

```yaml
# WRONG - breaks simple parsers
description: >-
  This is a multi-line
  description that folds.

# CORRECT - works everywhere
description: "This is a single-line description that all parsers read correctly."
```

## License

MIT
