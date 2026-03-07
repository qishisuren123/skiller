# Quality Checklist for Generated Skills

This checklist corresponds to the 24-point evaluation system. Every generated
skill MUST pass all items.

## 2.1.1 Format Review (8 points, -1 per violation)

- [ ] Has a `SKILL.md` file with correct name (case-sensitive)
- [ ] Directory name is kebab-case (regex: `^[a-z0-9]+(-[a-z0-9]+)*$`)
- [ ] No `README.md` in the directory
- [ ] SKILL.md has YAML frontmatter (delimited by `---`)
- [ ] `name` field in frontmatter matches directory name exactly
- [ ] `description` field present (explains what + when)
- [ ] `description` is under 1024 characters
- [ ] `description` has no XML tags (no `<tag>` patterns)

## 2.1.2 Content Completeness (8 points, +1 per item)

- [ ] Has `license` field (non-placeholder value like "MIT")
- [ ] Has `compatibility` field (under 500 characters)
- [ ] Has `metadata` field with at least one sub-key (e.g., `author`, `version`)
- [ ] Has `scripts/` subdirectory with at least one file
- [ ] Has `references/` subdirectory with at least one file
- [ ] Has `assets/` subdirectory with at least one file
- [ ] Body contains concrete usage examples (code block >= 3 lines, or "example"/"e.g." with context)
- [ ] Body contains error handling guidance (REQUIRES BOTH: error-word + handling-word)
  - Error words: "error", "exception", "troubleshoot", "failure"
  - Handling words: "retry", "catch", "handle", "fallback", "troubleshooting"

## 2.1.3 Writing Quality (8 points, +1 per item)

- [ ] `description` has clear task boundary (>= 40 chars, not vague like "helps with")
- [ ] `description` has clear trigger signal (contains: "use when", "when to use", "use for", "when the user", "when you", or "trigger")
- [ ] Progressive disclosure: SKILL.md body < 5000 chars, details in references/, code in scripts/
- [ ] Content is primarily in English (>= 85% ASCII in first 2000 chars)
- [ ] Forward reference consistency: files mentioned in SKILL.md body exist on disk
- [ ] Reverse reference consistency: if scripts/ or references/ exist, body references at least one file from each
- [ ] `license` is not a placeholder value (not: "unknown", "n/a", "none", "tbd", "todo")
- [ ] Version information present (in frontmatter `version` key, or body text matching `v\d+.\d+`)

## YAML Parser Compatibility Warning

**CRITICAL**: The skill-metric evaluation tool uses a simple line-based YAML parser.
It does NOT support multi-line block scalars (`>`, `>-`, `|`, `|-`).

If you write:
```yaml
description: >-
  Some long text
```
The parser will read description as the literal string `">-"` (2 characters),
causing FAILURES on:
- description field present (reads as ">-" which is truthy but wrong content)
- description has clear task boundary (">-" is only 2 chars, needs >= 40)
- description has clear trigger (">-" contains no trigger phrase)

**ALWAYS use single-line double-quoted strings**:
```yaml
description: "Your full description text here. Use this skill when..."
compatibility: "Python >=3.9; lib1 >=X.Y; lib2 >=A.B."
```
