# Common Pitfalls: Requirement to Skill Pipeline

## Pitfall 1: YAML Multi-Line Block Scalars Break Scoring

**Error**: skill-metric returns 22/24 with failures on "description has clear task boundary" and "description has clear trigger".

**Root Cause**: Using YAML block scalar syntax (`>-`, `>`, `|`, `|-`) for `description` or `compatibility`. The skill-metric tool uses a simple line-based parser that reads `description: >-` as the value `">-"` (2 characters), not the multi-line text below it.

**Fix**: Always use single-line double-quoted strings:
```yaml
# WRONG (score: 22/24)
description: >-
  Long description text that spans
  multiple lines...

# CORRECT (score: 24/24)
description: "Long description text that spans what would be multiple lines but is kept on one line. Use this skill when..."
```

## Pitfall 2: Missing Error Handling Keywords

**Error**: skill-metric returns 23/24 with failure on "body has error handling".

**Root Cause**: The checker requires BOTH an error-related word ("error", "exception", "failure", "troubleshoot") AND a handling-related word ("handle", "retry", "catch", "fallback", "troubleshooting") in the body text.

**Fix**: Add an explicit `## Error Handling` section to SKILL.md body:
```markdown
## Error Handling

1. **FileNotFoundError**: If the input path does not exist, the tool raises a clear error message. Handle by checking the path before running.
2. **ValueError on parse failure**: If the data format is unrecognized, the tool falls back to a default parser. Troubleshoot by checking the input format.
```

## Pitfall 3: Constructed Conversation Too Shallow

**Error**: Generated skill has a thin `references/pitfalls.md` with only 1-2 entries, and the code in `scripts/main.py` lacks edge case handling.

**Root Cause**: The conversation only has 2-3 error→fix iterations, so there's not enough material for robust pitfalls documentation.

**Fix**: Before writing the conversation, plan at least 5 distinct error types from different categories (format, API, edge case, scale, integration). Each error should have a realistic traceback and a non-trivial fix.

## Pitfall 4: Body Exceeds 5000 Characters

**Error**: skill-metric returns lower score on "progressive disclosure" check.

**Root Cause**: Full code, detailed workflow, or complete pitfalls list was included directly in SKILL.md body instead of being delegated to subdirectories.

**Fix**: SKILL.md body should contain ONLY:
- Overview (1 paragraph)
- When to Use (bullet list)
- Inputs (bullet list)
- Workflow (numbered steps with `See references/workflow.md`)
- Error Handling (3-4 items)
- Common Pitfalls (top 3-5 with `See references/pitfalls.md`)
- Output Format (brief with `See assets/example_output.md`)

All details go to `references/`, all code goes to `scripts/`.

## Pitfall 5: Cross-Reference Inconsistency

**Error**: skill-metric fails on "refs consistent with dirs" or "reverse consistency".

**Root Cause**: SKILL.md mentions `references/workflow.md` but the file is named `references/detailed-workflow.md`, or `scripts/` has files but SKILL.md body never mentions any file from `scripts/`.

**Fix**: After writing all files, verify:
1. Every `references/xxx.md` and `scripts/xxx.py` mentioned in SKILL.md body exists on disk
2. If `scripts/` directory exists with files, SKILL.md body references at least one (e.g., `scripts/main.py`)
3. If `references/` directory exists with files, SKILL.md body references at least one

## Pitfall 6: Fake Conversation Feels Artificial

**Error**: Not a scoring issue, but the generated skill's pitfalls are generic and unhelpful.

**Root Cause**: The conversation has the user state problems too precisely (e.g., "I think the issue is that MATLAB v7.3 uses HDF5 internally"), which sounds like the user already knows the answer.

**Fix**: Have the user report symptoms, not diagnoses:
```json
// BAD: User diagnoses the problem
{"role": "user", "content": "The error is because MATLAB v7.3 files are HDF5. Use h5py instead."}

// GOOD: User reports symptoms, assistant diagnoses
{"role": "user", "content": "I got this error:\nOSError: Unable to open file (file signature not found)\nIt happens on subject_03/neural_spikes.mat. The other .mat files work fine."}
```

## Pitfall 7: Code Not Actually Runnable

**Error**: `python scripts/main.py --help` fails with ImportError or SyntaxError.

**Root Cause**: The code was assembled from conversation snippets without testing that all pieces fit together (missing imports, undefined variables, incompatible function signatures).

**Fix**: Always run `--help` test and a synthetic data end-to-end test after extraction. Common issues:
- Missing `import` for a library used in a later function
- Function signature changed between conversation turns but caller wasn't updated
- `argparse` argument name doesn't match the variable used in `main()`
