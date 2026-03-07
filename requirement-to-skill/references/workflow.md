# Detailed Workflow: Requirement to Skill

## Phase 1 — Requirement Analysis (10 min)

### 1.1 Decompose the requirement

Given a plain-language requirement like *"I need a tool that converts multi-format neural data into standardized HDF5"*, extract:

| Element | Example |
|---------|---------|
| **Core task** | Read XDS/NWB/PyalData neural data, standardize to unified HDF5 |
| **Inputs** | .mat files, .nwb files, config JSON |
| **Outputs** | Single HDF5 with /dataset/session/trial/ structure |
| **Key libraries** | h5py, scipy, pynwb, numpy |
| **Edge cases** | MATLAB v7.3 format, variable spike counts, different sampling rates |

### 1.2 Identify domain-realistic errors

For each technical challenge, predict what errors a user would actually encounter:

| Challenge | Realistic error |
|-----------|----------------|
| MATLAB struct reading | `IndexError` from not unwrapping `[0,0]` |
| NWB spike access | Getting `VectorIndex` object instead of arrays |
| Sampling rate mismatch | Spike counts don't align with behavior data |
| Large file processing | Script hangs on multi-GB files |

These become the error→fix turns in the conversation.

### 1.3 Design the solution progression

Plan how the code evolves through the conversation:

```
v1: Basic but incomplete (e.g., only reads one format)
v2: Handles first error (e.g., struct unpacking)
v3: Handles second error (e.g., v7.3 fallback)
v4: Adds requested features (e.g., merging, filtering)
v5: Final production version with CLI, logging, error handling
```

---

## Phase 2 — Conversation Construction (30-60 min)

### 2.1 Write the conversation JSON

Format: `[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]`

**Turn structure template**:

```
Turn 1  [user]      [PROBLEM]     State the task + data description
Turn 2  [assistant] [ATTEMPT]     First attempt (intentionally imperfect)
Turn 3  [user]      [ERROR]       Report actual error with traceback
Turn 4  [assistant] [FIX]         Fix + explain root cause
Turn 5  [user]      [ERROR]       Second error (different from first)
Turn 6  [assistant] [FIX]         Fix with deeper understanding
Turn 7  [user]      [ERROR]       Third error or edge case
Turn 8  [assistant] [FIX]         Robust fix
Turn 9  [user]      [REFINEMENT]  Request new feature or optimization
Turn 10 [assistant] [SUCCESS]     Implement enhancement
Turn 11 [user]      [ERROR]       Bug in the enhancement
Turn 12 [assistant] [FIX]         Fix the bug
Turn 13 [user]      [REFINEMENT]  Final integration request (CLI, logging, etc.)
Turn 14 [assistant] [SUCCESS]     Complete production script
```

### 2.2 Quality checklist for conversations

- [ ] >= 10 turns (5+ user, 5+ assistant)
- [ ] >= 5 distinct error→fix iterations
- [ ] Errors are realistic (actual tracebacks, not vague descriptions)
- [ ] Assistant code evolves incrementally (not perfect from the start)
- [ ] Final code is complete and runnable (all imports, argparse, __main__)
- [ ] All content in English
- [ ] User role discovers errors naturally (not "I predict that...")

### 2.3 Save as JSON

Save to `conversations/<nn>_<topic_name>.json`

---

## Phase 3 — Skill Extraction (20 min)

### 3.1 Manual extraction (recommended for control)

For each section of the skill package, extract from the conversation:

**SKILL.md frontmatter** — MUST use single-line quoted strings:
```yaml
---
name: my-skill-name
description: "2-4 sentences. What it does + when to use. Use this skill when..."
license: MIT
compatibility: "Python >=3.9; lib1 >=X.Y; lib2 >=A.B."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---
```

**SKILL.md body** — Keep under 5000 characters:
- Brief overview (1 paragraph)
- When to Use (5-7 trigger phrases)
- Inputs (bullet list)
- Workflow (numbered steps, reference scripts/ and references/)
- Error Handling (MUST include "error" + "handle" keywords)
- Common Pitfalls (top 3-5, reference references/pitfalls.md)
- Output Format (brief, reference assets/example_output.md)

**scripts/main.py** — Take the final working code from the last assistant turn, clean up:
- Add all imports at the top
- Add argparse CLI
- Add `if __name__ == '__main__':` block
- Add inline comments in English

**references/pitfalls.md** — One section per error→fix iteration:
```markdown
## Pitfall N: <title>
**Error**: <exact error message>
**Root Cause**: <explanation>
**Fix**: <solution>
```

### 3.2 Automated extraction (optional)

If `ANTHROPIC_API_KEY` is available:
```bash
python conversation-to-skill/scripts/generate_skill.py conversation.json --output skill-name/
```

---

## Phase 4 — Validation (5 min)

### 4.1 Run skill-metric

```bash
python skill-metric/scripts/skill_quality_eval.py <skill-dir>/ -j
```

### 4.2 Fix common failures

| Score | Likely cause | Fix |
|-------|-------------|-----|
| 22/24 | YAML `>-` + missing trigger | Single-line description + add "Use this skill when..." |
| 23/24 | Missing error handling keywords | Add `## Error Handling` with "error" + "handle" |
| 23/24 | Missing reverse reference | Body must reference >=1 file from scripts/ and references/ |

### 4.3 Re-run until 24/24

---

## Phase 5 — Code Usability Testing (10 min)

### 5.1 Import test
```bash
python scripts/main.py --help
```

### 5.2 Synthetic data test
Create minimal test data in `/tmp/`, run the full pipeline, verify output structure.

### 5.3 Fix and re-validate
If bugs are found, fix in `scripts/main.py` and re-run skill-metric (code changes don't affect scoring).
