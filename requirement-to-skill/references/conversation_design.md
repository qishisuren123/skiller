# Conversation Design Guide

This document provides detailed guidance on constructing realistic multi-turn
conversations that serve as high-quality source material for skill extraction.

## Why Conversations Matter

The skill extraction process relies on conversations containing:
- **Error→fix iterations** that become pitfalls documentation
- **Progressive code evolution** that shows the "correct" final approach
- **Domain-specific edge cases** that make the skill practically useful

A conversation with no errors produces a skill with no pitfalls. A conversation
with trivial errors produces a skill that's not useful for real work.

## Conversation Architecture

### The Error Cascade Pattern

The most effective conversation structure follows a **realistic error cascade**:
each fix reveals the next problem, which is how real debugging actually works.

```
User asks → Assistant provides initial code
  → User runs it → Hits Error A (format/input issue)
    → Assistant fixes A → Reveals Error B (deeper issue)
      → User reports B → Assistant fixes B → Reveals Error C
        → ...eventually reaches working solution
          → User asks for enhancement → More error→fix cycles
            → Final production version
```

### Error Categories to Include

For each domain, select 3-5 errors from these categories:

| Category | Examples |
|----------|---------|
| **Format incompatibility** | MATLAB v7.3, HDF5 nesting, NWB VectorIndex |
| **API misuse** | Wrong method (dict access vs iterator), deprecated calls |
| **Data edge cases** | Empty arrays, NaN values, mismatched dimensions |
| **Scale issues** | Large files, memory limits, slow iteration |
| **Integration bugs** | In-place mutation, wrong variable scope, off-by-one |

### What Makes a Conversation Feel Real

**DO**:
- Have the user paste actual error tracebacks (even if synthetic)
- Have the user discover problems incrementally, not all at once
- Have the assistant sometimes fix one thing but miss another
- Include small refinement requests (add logging, add CLI args)

**DON'T**:
- Have the user predict errors before running code
- Have the assistant produce perfect code on the first try
- Skip the error message and just say "it doesn't work"
- Make all errors happen in the same area of the code

## Template: Neuroscience Data Processing

```json
[
  {"role": "user", "content": "I have [data format] files from [source]. I need to [task]. Can you write a script?"},
  {"role": "assistant", "content": "Here's a basic version:\n```python\n[initial code with 1-2 subtle issues]\n```"},
  {"role": "user", "content": "I got this error:\n```\n[realistic traceback]\n```\nThe issue seems to be [user's partial understanding]."},
  {"role": "assistant", "content": "The root cause is [explanation]. Here's the fix:\n```python\n[corrected code]\n```\nKey change: [what and why]."},
  ...
]
```

## Checklist

- [ ] 10+ turns total
- [ ] 5+ distinct error types
- [ ] Each error has a realistic traceback or symptom
- [ ] Code evolves from v1 (basic) to vN (production)
- [ ] Final code has: all imports, argparse, main block, comments
- [ ] 100% English content
- [ ] User role sounds like a domain scientist, not a prompt engineer
