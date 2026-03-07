# Example: Complete Requirement-to-Skill Pipeline

This example shows the full pipeline from a one-line requirement to a validated 24/24 skill.

## Input Requirement

> "I need a tool that recursively scans a neuroscience data directory with HDF5 and MATLAB files, extracts internal structure metadata, and outputs a structured JSON summary."

## Phase 1 Output: Requirement Analysis

```
Core task:     Scan .h5/.mat files, extract keys/shapes/dtypes, output meta.json
Inputs:        Root directory path
Outputs:       meta.json with file structure catalog
Libraries:     h5py, scipy, numpy, pathlib
Edge cases:    MATLAB v7.3 (HDF5 under the hood), nested HDF5 groups,
               large files (tens of GB), repeated subject structures
Planned errors:
  1. Only scans top-level (no recursion)
  2. Misses nested HDF5 groups
  3. MATLAB v7.3 OSError
  4. Large file hang
  5. Shape comparison too strict for merging
```

## Phase 2 Output: Conversation (abbreviated)

```json
[
  {"role": "user", "content": "I have a neuroscience data folder with .h5 and .mat files under subject directories. Write a script to extract metadata..."},
  {"role": "assistant", "content": "```python\ndef scan_directory(root_dir):\n    for fname in os.listdir(root_dir): ...```"},
  {"role": "user", "content": "It only scans the top level, doesn't recurse into subject_01/..."},
  {"role": "assistant", "content": "Fixed with os.walk + recursive HDF5 group traversal..."},
  {"role": "user", "content": "OSError: Unable to open file (file signature not found)..."},
  {"role": "assistant", "content": "MATLAB v7.3 fallback to h5py..."},
  ...14 turns total, 5 error→fix iterations...
]
```

## Phase 3 Output: Skill Package

```
neuro-metadata-gen/
├── SKILL.md                  (4.0 KB, body 3372 chars < 5000)
├── scripts/
│   ├── main.py               (24 KB, 700 lines, full CLI)
│   └── requirements.txt      (53 B)
├── references/
│   ├── workflow.md            (8.5 KB)
│   └── pitfalls.md            (8.1 KB, 5 pitfalls)
└── assets/
    └── example_output.md      (4.8 KB)
```

### SKILL.md frontmatter:
```yaml
---
name: neuro-metadata-gen
description: "Recursively scan neuroscience data directories containing HDF5 and MATLAB files, extract internal structure metadata (keys, shapes, dtypes), and generate a structured meta.json catalog. Supports MATLAB v7.3 auto-fallback via h5py, large file depth limiting, and wildcard pattern merging for consistent subject structures. Use this skill when the user needs to catalog the internal structure of a neuroscience dataset folder."
license: MIT
compatibility: "Python >=3.9; h5py >=3.9.0; scipy >=1.11.0; numpy >=1.24.0. Optional: tqdm for progress bars."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---
```

## Phase 4 Output: Scoring

```
$ python skill_quality_eval.py neuro-metadata-gen/ -j

  Format:        8/8   (all 8 checks pass)
  Completeness:  8/8   (all 8 checks pass)
  Writing:       8/8   (all 8 checks pass)
  Total:         24/24
```

## Phase 5 Output: Code Testing

### --help test:
```
$ python scripts/main.py --help
usage: neuro-metadata-gen [-h] [--output OUTPUT] [--merge | --no-merge]
                          [--subject-pattern PATTERN] [--shape-mode MODE]
                          [--large-threshold BYTES] [--verbose]
                          root_dir
```

### Synthetic data test:
```
$ python scripts/main.py /tmp/test_data/ -o meta.json --merge -v
[INFO] Discovered 6 files.
Inspecting files: 100%|██████████| 6/6 [00:00<00:00, 1848 file/s]
[INFO] Summary: 6 files, 8.83 MB total, 12 datasets, 0 errors.
```

Output meta.json correctly merges 3 subjects × 2 files into 2 pattern entries
with shape_dim0_ranges showing per-subject variation.

## Timeline

| Phase | Duration | Output |
|-------|----------|--------|
| 1. Requirement analysis | 10 min | Error plan, library list |
| 2. Conversation construction | 30-60 min | 14-turn JSON conversation |
| 3. Skill extraction | 20 min | 6-file skill package |
| 4. Validation | 5 min | 24/24 score |
| 5. Code testing | 10 min | --help + synthetic test pass |
| **Total** | **~90 min** | **Production-ready skill** |
