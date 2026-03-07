# Manual Workflow

When the automated `scripts/generate_skill.py` is not available (e.g., no API
key or working interactively), follow these steps manually.

## Step 1 — Parse & Summarize

Read the conversation file. For each turn, create a one-line annotation:
```
TURN N [USER/ASSISTANT]: <what was being done / attempted>
```

Flag turns as:
- `[PROBLEM]` — Initial problem statement
- `[ATTEMPT]` — First or new approach tried
- `[ERROR]` — Something went wrong
- `[FIX]` — Correction applied
- `[SUCCESS]` — Working solution achieved
- `[REFINEMENT]` — Enhancement to working solution

## Step 2 — Extract Workflow

From the annotations, identify:

1. **Problem**: What was being solved? (1-2 sentences)
2. **Inputs**: What data/files were involved?
3. **Outputs**: What was produced?
4. **Steps**: Ordered sequence of actions leading to the final solution
   - Mark failed/revised steps with `[REVISED]`
   - Mark the final working approach with `[FINAL]`
5. **Key Techniques**: Libraries, APIs, patterns, algorithms used
   - Include version numbers where mentioned
6. **Gotchas**: Every error and its fix (critical for pitfalls section)
7. **Skill Name**: Short kebab-case name (e.g., `pdf-table-extractor`)

## Step 3 — Extract Final Code

Find the last working versions of all code blocks:
- Keep ONLY the final version that worked
- Add inline comments explaining each section
- Group related snippets together
- Preserve original code exactly (don't rewrite)
- Note required library versions

## Step 4 — Generate Multi-File Package

Create the skill directory with this structure:

```
<skill-name>/
├── SKILL.md
├── scripts/
│   ├── main.py
│   └── requirements.txt
├── references/
│   ├── workflow.md
│   └── pitfalls.md
└── assets/
    └── example_output.md
```

### 4a. Write SKILL.md (body < 5000 chars)

Use the template from `references/skill-template.md`. Key rules:
- Frontmatter: name, description, license, compatibility, metadata
- Body: concise workflow, top 3-5 pitfalls, references to scripts/ and references/
- Do NOT put full code in SKILL.md — reference scripts/ instead

### 4b. Write scripts/main.py

- Complete, runnable script with all imports
- argparse CLI interface
- Error handling for common failure modes
- Header comment with requirements

### 4c. Write scripts/requirements.txt

- All Python dependencies with version pins

### 4d. Write references/workflow.md

- Full detailed workflow with all substeps
- Input/output format specifications
- Library configuration details

### 4e. Write references/pitfalls.md

- Every error from the conversation
- Format: Error message → Root cause → Fix → Code example

### 4f. Write assets/example_output.md

- Concrete example of the skill's output
- Sample data structures, file formats, directory trees

## Step 5 — Quality Check

Run through the quality checklist (see `references/quality-checklist.md`):

### Format checks
- [ ] name matches directory name (kebab-case)
- [ ] No README.md in directory
- [ ] description < 1024 chars with task boundary + trigger
- [ ] license is non-placeholder
- [ ] compatibility < 500 chars

### YAML format compatibility (CRITICAL)
- [ ] `description` is a single-line double-quoted string (NO `>`, `>-`, `|`, `|-`)
- [ ] `compatibility` is a single-line double-quoted string (NO `>`, `>-`, `|`, `|-`)
- [ ] All frontmatter values are on the same line as their key

### Content checks
- [ ] SKILL.md body < 5000 chars
- [ ] scripts/ and references/ exist and are referenced in body
- [ ] Body has **error handling section** with keywords: "error"/"exception" + "handle"/"troubleshoot"/"fallback"
- [ ] Body has **code examples** (code block >= 3 lines)
- [ ] Content is 100% English
- [ ] Version info present

## Step 6 — Self-Test (Optional)

If testing the pipeline:
1. Generate test conversations: `python scripts/generate_test_conversations.py --scenario "..." --domain general`
2. Generate skill from conversation: `python scripts/generate_skill.py conversation.json`
3. Validate against quality checklist
