---
name: conversation-to-skill
description: "Automatically generate a production-quality, multi-file skill package from any AI conversation log (ChatGPT export, OpenAI API format, Claude JSON, or plain text). Extracts the problem-solving workflow, final working code, and lessons learned, then outputs a skill folder with SKILL.md, scripts/, references/, and assets/. Use this skill when the user provides a chat log or conversation export and wants to turn it into a reusable skill."
license: MIT
compatibility: "Python >=3.9; anthropic >=0.39.0. Requires ANTHROPIC_API_KEY env var. Manual workflow requires no dependencies."
metadata:
  author: conversation-to-skill-generator
  version: "4.0"
  min_claude_code_version: "1.0"
---

# Conversation to Skill Generator

Converts any AI conversation log into a ready-to-use, multi-file skill
package. Also provides tools to generate complex test conversations from
scenario descriptions, enabling end-to-end self-testing of the pipeline.

## When to Use This Skill

- "Turn this ChatGPT/Claude conversation into a skill"
- "Here's a chat log — extract the workflow and make it reusable"
- "Generate test conversations for these scientific scenarios"
- "I solved a problem in a conversation, make it a repeatable skill"
- User provides a `.json` or `.txt` conversation export
- User wants to stress-test the skill generation with complex mock data

## Inputs

- **conversation_file** (required for skill generation): Conversation in JSON or plain text
- **scenario** (required for test generation): Description of the scenario to simulate
- **skill_name** (optional): kebab-case name override
- **output_dir** (optional): Output directory path

## Workflow

### Mode A — Generate Skill from Conversation

1. **Parse**: Auto-detect format and load all turns. Run `scripts/generate_skill.py conversation.json`
2. **Annotate**: Tag each turn as [PROBLEM], [ATTEMPT], [ERROR], [FIX], [SUCCESS], [REFINEMENT]
3. **Extract**: Identify the workflow, final code, and all pitfalls encountered
4. **Package**: Write multi-file skill:
   ```
   <skill-name>/
   ├── SKILL.md              # Core instructions (< 5000 chars body)
   ├── scripts/main.py       # Final working script with CLI
   ├── scripts/requirements.txt
   ├── references/workflow.md # Full step-by-step workflow
   ├── references/pitfalls.md # All errors and fixes
   └── assets/example_output.md
   ```
5. **Validate**: Quality checklist (see `references/quality-checklist.md`)

### Mode B — Generate Test Conversations

1. **Define scenario**: Describe the scientific data processing task
2. **Generate**: Run `scripts/generate_test_conversations.py --scenario "..." --domain neuroscience`
3. **Validate**: Check output quality (English ratio, traceback presence, turn count)

See `references/manual-workflow.md` for the full manual workflow.

## Error Handling

Common errors and how to handle them:

1. **JSON parse error**: If the conversation file has invalid JSON, the parser falls back to plain-text mode with User:/Assistant: markers. Handle this by checking the file format before processing.
2. **API authentication failure**: If ANTHROPIC_API_KEY is missing or invalid, the script raises `anthropic.AuthenticationError`. Troubleshoot by verifying the environment variable is set.
3. **Body exceeds 5000 chars**: The generator catches this and automatically moves code to `scripts/` and details to `references/`. If the error persists, manually trim the SKILL.md body.
4. **Non-English content exception**: Generated skills may inherit conversation language. Handle by ensuring source conversations are in English.

## Common Pitfalls

1. **name/directory mismatch**: The `name` field in frontmatter must exactly match the directory name in kebab-case.
2. **Missing cross-references**: If `scripts/` exists, SKILL.md body must reference at least one file in it.
3. **YAML multi-line block scalars**: NEVER use `>`, `>-`, `|`, or `|-` in frontmatter values; use quoted single-line strings instead.

See `references/pitfalls.md` for the full list.

## Output Format

See `assets/example_output.md` for a complete example of generated skill packages.
