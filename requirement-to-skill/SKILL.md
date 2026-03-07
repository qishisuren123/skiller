---
name: requirement-to-skill
description: "Generate a production-quality, 24/24-scoring skill package from a plain-language requirement description, without needing a real conversation log. Constructs a realistic multi-turn conversation with error-fix iterations, extracts the solution into a multi-file skill (SKILL.md, scripts/, references/, assets/), and validates against the skill-metric rubric. Use this skill when the user has a task description or feature request and wants to produce a reusable skill package."
license: MIT
compatibility: "Python >=3.9. No external API required for manual workflow. Optional: anthropic >=0.39.0 for automated conversation generation."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Requirement to Skill Generator

Converts a plain-language task requirement into a complete, validated skill
package — without needing a pre-existing conversation log. The core insight:
real conversations contain error-fix iterations that produce high-quality
pitfalls and robust code, so we **construct** such conversations first, then
extract the skill from them.

## When to Use This Skill

- "I need a skill for X but don't have a conversation about it"
- "Create a skill package from this feature description"
- "Turn this task requirement into a reusable, validated skill"
- "Generate a skill that scores 24/24 on the quality rubric"
- User provides a requirement, not a conversation log

## Workflow

The process has 5 phases. See `references/workflow.md` for full details.

### Phase 1 — Requirement Analysis

Break the requirement into:
- **Core task**: What does the tool do? (1-2 sentences)
- **Input/output**: What goes in, what comes out?
- **Technical challenges**: What libraries, formats, edge cases?
- **Domain pitfalls**: What errors will a user realistically encounter?

### Phase 2 — Conversation Construction

Build a realistic 10-20 turn conversation following this pattern:

```
Turn 1  [user]:      State the problem
Turn 2  [assistant]: Provide initial (imperfect) solution
Turn 3  [user]:      Report first error/limitation
Turn 4  [assistant]: Fix the error, explain root cause
Turn 5  [user]:      Report second error
Turn 6  [assistant]: Fix with deeper understanding
...
Turn N-1 [user]:     Request final integration/polish
Turn N   [assistant]: Deliver complete production script
```

**Critical rules** (see `references/conversation_design.md`):
- Minimum 5 error→fix iterations (not Q&A)
- Errors must be realistic (format incompatibility, edge cases, API misuse)
- Final code must be complete and runnable
- All content in English

### Phase 3 — Skill Extraction

Use the `conversation-to-skill` generator (v4) to produce:

```
<skill-name>/
├── SKILL.md              # Body < 5000 chars, single-line YAML values
├── scripts/main.py       # Complete CLI tool with argparse
├── scripts/requirements.txt
├── references/workflow.md
├── references/pitfalls.md
└── assets/example_output.md
```

Run `scripts/main.py --help` to verify the extraction produces valid code.

### Phase 4 — Validation & Scoring

Run the skill-metric evaluator:

```bash
python skill_quality_eval.py <skill-dir>/ -j
```

All 24 checks must pass. Key failure points and how to handle them:

| Check | Common failure | Fix |
|-------|---------------|-----|
| description task boundary | Too short (< 40 chars) | Write 2-4 sentences describing WHAT the tool does |
| description trigger | Missing "use when" | Add "Use this skill when..." at the end |
| error handling in body | Missing keywords | Add `## Error Handling` section with "error" + "handle" |
| YAML parsing | Used `>-` or `>` | Change to single-line `"quoted string"` |

### Phase 5 — Code Usability Testing

1. **`--help` test**: `python scripts/main.py --help` must succeed
2. **Synthetic data test**: Create minimal test data, run end-to-end, verify output
3. **Fix any bugs** found during testing

## Error Handling

Common errors in this workflow and how to handle them:

1. **Conversation too shallow**: If the constructed conversation has fewer than 5 error→fix iterations, the pitfalls section will be thin. Handle by adding domain-realistic errors (format incompatibility, edge cases, OOM).
2. **YAML multi-line failure**: If skill-metric reads description as `">-"`, the frontmatter used block scalars. Troubleshoot by checking that all values are single-line double-quoted strings.
3. **Body exceeds 5000 chars**: The SKILL.md body is too long. Handle by moving code to `scripts/` and details to `references/`, keeping only summaries in the body.
4. **Import errors in main.py**: Generated code references unavailable libraries. Handle by listing all dependencies in `requirements.txt` and testing in a clean environment.

## Common Pitfalls

1. **Fake conversations feel artificial**: The most common mistake. Real conversations have the user discovering problems incrementally, not stating them upfront. Make the user role "discover" errors only after running code.
2. **Missing cross-references**: SKILL.md must reference at least one file from both `scripts/` and `references/`. Check with the quality checklist.
3. **Score 22-23 instead of 24**: Almost always caused by YAML `>-` parsing or missing error-handling keywords.

See `references/pitfalls.md` for the full list.

## Output Format

The final deliverable is a skill directory that:
- Scores **24/24** on skill-metric
- Has a working `scripts/main.py` with `--help` and end-to-end functionality
- Contains realistic pitfalls extracted from the constructed conversation

See `assets/example_output.md` for a concrete example of the complete pipeline.
